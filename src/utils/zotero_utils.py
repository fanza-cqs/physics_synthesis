# src/utils/zotero_utils.py
"""
Shared Zotero utility functions for the Physics Literature Synthesis Pipeline

This module contains common Zotero operations that need to be used across 
multiple UI components, eliminating code duplication and providing a single
source of truth for Zotero connection management.
"""

import streamlit as st
from typing import Dict, Any, Tuple, List, Optional
import logging

# Use absolute imports to avoid relative import issues
try:
    from src.utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    # Fallback if logging config not available
    logger = logging.getLogger(__name__)


def retry_zotero_connection() -> bool:
    """
    Retry Zotero connection with proper error handling and status updates
    
    Returns:
        bool: True if retry was successful, False otherwise
    """
    try:
        config = st.session_state.get('config')
        if not config:
            st.session_state.zotero_status = "❌ Failed: No config available"
            logger.error("Zotero retry failed: No config available")
            return False
        
        # Set connecting status
        st.session_state.zotero_status = "🔄 Connecting..."
        logger.info("Attempting Zotero reconnection...")
        
        # Try to create new manager - use absolute import
        from src.downloaders import create_zotero_manager
        zotero_manager = create_zotero_manager(config)
        
        # Test the connection immediately
        connection_info = zotero_manager.test_connection()
        if not connection_info.get('connected'):
            raise ConnectionError(f"Connection test failed: {connection_info.get('error', 'Unknown error')}")
        
        # Success - update session state
        st.session_state.zotero_manager = zotero_manager
        st.session_state.zotero_status = "✅ Connected"
        
        # Try to load collections immediately
        try:
            collections = zotero_manager.get_collections()
            st.session_state.zotero_collections = collections
            logger.info(f"Zotero reconnection successful - loaded {len(collections)} collections")
        except Exception as e:
            # Connection works but collections failed - still consider it success
            logger.warning(f"Zotero connected but collections failed: {e}")
            st.session_state.zotero_collections = []
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        st.session_state.zotero_manager = None
        st.session_state.zotero_status = f"❌ Failed: {error_msg}"
        logger.error(f"Zotero retry failed: {e}")
        return False


def test_zotero_connection_and_update_status() -> Dict[str, Any]:
    """
    Test Zotero connection and update session state accordingly
    
    Returns:
        Dict with connection test results:
        {
            'success': bool,
            'total_items': int (if successful),
            'error': str (if failed),
            'collections_count': int (if successful)
        }
    """
    zotero_manager = st.session_state.get('zotero_manager')
    
    if not zotero_manager:
        return {
            'success': False,
            'error': 'No Zotero manager available'
        }
    
    try:
        logger.info("Testing Zotero connection...")
        
        # Test the connection
        connection_info = zotero_manager.test_connection()
        
        if connection_info.get('connected'):
            total_items = connection_info.get('total_items', 0)
            
            # Update collections if test was successful
            collections_count = 0
            try:
                collections = zotero_manager.get_collections()
                st.session_state.zotero_collections = collections
                collections_count = len(collections)
                logger.info(f"Zotero test successful: {total_items} items, {collections_count} collections")
            except Exception as e:
                # Connection works but collections failed - still consider it success
                logger.warning(f"Zotero connected but collections failed: {e}")
                st.session_state.zotero_collections = []
            
            return {
                'success': True,
                'total_items': total_items,
                'collections_count': collections_count
            }
        else:
            error_msg = connection_info.get('error', 'Unknown connection error')
            logger.error(f"Zotero test failed: {error_msg}")
            return {
                'success': False,
                'error': error_msg
            }
            
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Zotero test exception: {e}")
        return {
            'success': False,
            'error': error_msg
        }


def reload_zotero_collections() -> Tuple[bool, str]:
    """
    Reload Zotero collections from the current manager
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    zotero_manager = st.session_state.get('zotero_manager')
    
    if not zotero_manager:
        return False, "No Zotero manager available"
    
    try:
        logger.info("Reloading Zotero collections...")
        collections = zotero_manager.get_collections()
        st.session_state.zotero_collections = collections
        
        message = f"Loaded {len(collections)} collections"
        logger.info(f"Collections reloaded successfully: {message}")
        return True, message
        
    except Exception as e:
        error_msg = f"Failed to reload collections: {e}"
        logger.error(error_msg)
        return False, error_msg


def get_zotero_status_display() -> Tuple[str, str, bool]:
    """
    Get current Zotero status for display purposes
    
    Returns:
        Tuple[str, str, bool]: (status_text, display_class, is_working)
        - status_text: Human readable status
        - display_class: CSS class for styling ('success', 'error', 'warning', 'info')
        - is_working: Whether Zotero is currently functional
    """
    zotero_status = st.session_state.get('zotero_status', 'unknown')
    zotero_manager = st.session_state.get('zotero_manager')
    collections = st.session_state.get('zotero_collections', [])
    
    # Determine if Zotero is working
    is_working = (zotero_manager is not None and 
                 (zotero_status == "✅ Connected" or 
                  zotero_status == "connected" or 
                  "Connected" in str(zotero_status)))
    
    if is_working:
        if collections:
            status_text = f"✅ Connected ({len(collections)} collections)"
        else:
            status_text = "✅ Connected (no collections)"
        display_class = "success"
        
    elif (zotero_status == 'not_configured' or 
          zotero_status is None or 
          zotero_status == 'unknown'):
        status_text = "⚙️ Not configured"
        display_class = "warning"
        
    elif "Connecting" in str(zotero_status) or "🔄" in str(zotero_status):
        status_text = "🔄 Connecting..."
        display_class = "info"
        
    else:
        # Error state
        if "Failed:" in str(zotero_status):
            status_text = str(zotero_status)
        else:
            status_text = f"❌ Error: {zotero_status}"
        display_class = "error"
    
    return status_text, display_class, is_working


def initialize_zotero(config) -> bool:
    """
    Initialize Zotero manager with proper error handling
    
    Args:
        config: PipelineConfig instance
        
    Returns:
        bool: True if initialization was successful
    """
    try:
        logger.info("Initializing Zotero manager...")
        
        from src.downloaders import create_zotero_manager
        zotero_manager = create_zotero_manager(config)
        
        # Test connection immediately
        connection_info = zotero_manager.test_connection()
        if not connection_info.get('connected'):
            raise ConnectionError(f"Connection test failed: {connection_info.get('error', 'Unknown error')}")
        
        # Success
        st.session_state.zotero_manager = zotero_manager
        st.session_state.zotero_status = "✅ Connected"
        
        # Load collections
        try:
            collections = zotero_manager.get_collections()
            st.session_state.zotero_collections = collections
            logger.info(f"Zotero initialized successfully with {len(collections)} collections")
        except Exception as e:
            logger.warning(f"Zotero initialized but collections failed: {e}")
            st.session_state.zotero_collections = []
        
        return True
        
    except Exception as e:
        error_msg = str(e)
        st.session_state.zotero_manager = None
        st.session_state.zotero_status = f"❌ Failed: {error_msg}"
        st.session_state.zotero_collections = []
        logger.error(f"Zotero initialization failed: {e}")
        return False


def is_zotero_working() -> bool:
    """
    Simple check if Zotero is currently working
    
    Returns:
        bool: True if Zotero is functional
    """
    _, _, is_working = get_zotero_status_display()
    return is_working


def get_collections_summary() -> str:
    """
    Get a summary of current Zotero collections
    
    Returns:
        str: Human readable collections summary
    """
    collections = st.session_state.get('zotero_collections', [])
    
    if not collections:
        return "No collections found"
    
    total_items = sum(collection.get('num_items', 0) for collection in collections)
    return f"{len(collections)} collections, {total_items} total items"