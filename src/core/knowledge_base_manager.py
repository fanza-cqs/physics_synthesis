# src/core/knowledge_base_manager.py
"""
Knowledge Base Manager with Session Context Awareness
Integrates with existing KB system while preventing session interference
"""

import logging
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

# Import your existing KB modules
from .knowledge_base import (
    KnowledgeBase, 
    create_knowledge_base as _create_kb,
    load_knowledge_base as _load_kb,
    delete_knowledge_base as _delete_kb,
    list_knowledge_bases as _list_kbs
)
from .kb_orchestrator import (
    KnowledgeBaseOrchestrator,
    SourceSelection,
    KBOperation
)

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class KnowledgeBaseManager:
    """
    Context-aware wrapper for knowledge base operations
    Prevents KB operations from interfering with session lifecycle
    """
    
    def __init__(self, config, session_integration = None):
        """
        Initialize KB manager
        
        Args:
            config: Pipeline configuration
            session_integration: Session integration for context management (optional)
        """
        self.config = config
        self.session_integration = session_integration
        self.orchestrator = KnowledgeBaseOrchestrator(config)
    
    def create_knowledge_base_simple(self, name: str, **kwargs) -> bool:
        """
        Create a simple empty knowledge base without affecting sessions
        
        Args:
            name: KB name
            **kwargs: Additional arguments for KnowledgeBase
            
        Returns:
            True if created successfully
        """
        try:
            # Set context to prevent session modifications
            if self.session_integration:
                with self.session_integration.handle_kb_management_operations():
                    kb = _create_kb(
                        name=name, 
                        base_storage_dir=self.config.knowledge_bases_folder,
                        **kwargs
                    )
                    success = kb is not None
            else:
                kb = _create_kb(
                    name=name, 
                    base_storage_dir=self.config.knowledge_bases_folder,
                    **kwargs
                )
                success = kb is not None
            
            # Notify about creation without creating sessions
            if success and self.session_integration:
                self._notify_kb_created(name)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to create knowledge base '{name}': {e}")
            return False
    
    def create_knowledge_base_from_sources(self, 
                                         name: str,
                                         source_selection: SourceSelection,
                                         operation: KBOperation = KBOperation.CREATE_NEW,
                                         **kwargs) -> Dict[str, Any]:
        """
        Create knowledge base from multiple sources using orchestrator
        
        Args:
            name: KB name
            source_selection: Source configuration
            operation: KB operation type
            **kwargs: Additional orchestrator arguments
            
        Returns:
            Dictionary with creation results
        """
        try:
            # Set context to prevent session modifications
            if self.session_integration:
                with self.session_integration.handle_kb_management_operations():
                    result = self.orchestrator.create_knowledge_base(
                        name, source_selection, operation, **kwargs
                    )
            else:
                result = self.orchestrator.create_knowledge_base(
                    name, source_selection, operation, **kwargs
                )
            
            # Notify about creation without creating sessions
            if result.success and self.session_integration:
                self._notify_kb_created(result.kb_name)
            
            return {
                'success': result.success,
                'kb_name': result.kb_name,
                'total_documents': result.total_documents,
                'total_chunks': result.total_chunks,
                'error_messages': result.error_messages,
                'is_partial': result.is_partial
            }
            
        except Exception as e:
            logger.error(f"Failed to create knowledge base from sources '{name}': {e}")
            return {
                'success': False,
                'kb_name': name,
                'error_messages': [str(e)]
            }
    
    def create_knowledge_base_from_directories(self, 
                                             name: str,
                                             literature_folder: Optional[Path] = None,
                                             your_work_folder: Optional[Path] = None,
                                             **kwargs) -> Dict[str, Any]:
        """
        Create knowledge base from directories without affecting sessions
        
        Args:
            name: KB name
            literature_folder: Literature directory
            your_work_folder: Your work directory
            **kwargs: Additional arguments
            
        Returns:
            Dictionary with build statistics
        """
        try:
            # Set context to prevent session modifications
            if self.session_integration:
                with self.session_integration.handle_kb_management_operations():
                    # Create KB and build from directories
                    kb = _create_kb(
                        name=name, 
                        base_storage_dir=self.config.knowledge_bases_folder
                    )
                    
                    if kb:
                        stats = kb.build_from_directories(
                            literature_folder=literature_folder,
                            your_work_folder=your_work_folder,
                            **kwargs
                        )
                        success = stats.get('total_documents', 0) > 0
                    else:
                        success = False
                        stats = {}
            else:
                # Create KB and build from directories
                kb = _create_kb(
                    name=name, 
                    base_storage_dir=self.config.knowledge_bases_folder
                )
                
                if kb:
                    stats = kb.build_from_directories(
                        literature_folder=literature_folder,
                        your_work_folder=your_work_folder,
                        **kwargs
                    )
                    success = stats.get('total_documents', 0) > 0
                else:
                    success = False
                    stats = {}
            
            # Notify about creation without creating sessions
            if success and self.session_integration:
                self._notify_kb_created(name)
            
            return {
                'success': success,
                **stats
            }
            
        except Exception as e:
            logger.error(f"Failed to create knowledge base from directories '{name}': {e}")
            return {
                'success': False,
                'error_message': str(e)
            }
    
    def delete_knowledge_base(self, name: str) -> bool:
        """
        Delete KB and handle affected sessions properly
        
        Args:
            name: KB name to delete
            
        Returns:
            True if deleted successfully
        """
        try:
            # Set context to prevent session modifications during deletion
            if self.session_integration:
                with self.session_integration.handle_kb_management_operations():
                    success = _delete_kb(name, self.config.knowledge_bases_folder)
            else:
                success = _delete_kb(name, self.config.knowledge_bases_folder)
            
            # Handle affected sessions
            if success and self.session_integration:
                affected_count, affected_names = self._handle_kb_deletion_for_sessions(name)
                logger.info(f"KB '{name}' deleted. Updated {affected_count} affected sessions.")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to delete knowledge base '{name}': {e}")
            return False
    
    def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """
        List available knowledge bases without affecting sessions
        
        Returns:
            List of KB information dictionaries
        """
        try:
            # Set context to prevent session modifications
            if self.session_integration:
                with self.session_integration.handle_kb_management_operations():
                    return _list_kbs(self.config.knowledge_bases_folder)
            else:
                return _list_kbs(self.config.knowledge_bases_folder)
                
        except Exception as e:
            logger.error(f"Failed to list knowledge bases: {e}")
            return []
    
    def load_knowledge_base(self, name: str) -> Optional[KnowledgeBase]:
        """
        Load knowledge base without affecting sessions
        
        Args:
            name: KB name to load
            
        Returns:
            KnowledgeBase instance or None
        """
        try:
            # Set context to prevent session modifications
            if self.session_integration:
                with self.session_integration.handle_kb_management_operations():
                    return _load_kb(name, self.config.knowledge_bases_folder)
            else:
                return _load_kb(name, self.config.knowledge_bases_folder)
                
        except Exception as e:
            logger.error(f"Failed to load knowledge base '{name}': {e}")
            return None
    
    def get_knowledge_base_stats(self, name: str) -> Dict[str, Any]:
        """
        Get statistics for a knowledge base without affecting sessions
        
        Args:
            name: KB name
            
        Returns:
            Statistics dictionary
        """
        try:
            # Set context to prevent session modifications
            if self.session_integration:
                with self.session_integration.handle_kb_management_operations():
                    kb = _load_kb(name, self.config.knowledge_bases_folder)
                    if kb:
                        return kb.get_statistics()
                    else:
                        return {}
            else:
                kb = _load_kb(name, self.config.knowledge_bases_folder)
                if kb:
                    return kb.get_statistics()
                else:
                    return {}
                
        except Exception as e:
            logger.error(f"Failed to get stats for knowledge base '{name}': {e}")
            return {}
    
    def rebuild_knowledge_base(self, name: str, **kwargs) -> bool:
        """
        Rebuild an existing knowledge base without affecting sessions
        
        Args:
            name: KB name to rebuild
            **kwargs: Additional rebuild arguments
            
        Returns:
            True if rebuilt successfully
        """
        try:
            success = False
            
            # Set context to prevent session modifications
            if self.session_integration:
                with self.session_integration.handle_kb_management_operations():
                    kb = _load_kb(name, self.config.knowledge_bases_folder)
                    if not kb:
                        logger.warning(f"Knowledge base '{name}' not found for rebuild")
                        return False
                    
                    # Force rebuild
                    stats = kb.build_from_directories(force_rebuild=True, **kwargs)
                    success = stats.get('total_documents', 0) > 0
            else:
                kb = _load_kb(name, self.config.knowledge_bases_folder)
                if not kb:
                    logger.warning(f"Knowledge base '{name}' not found for rebuild")
                    return False
                
                # Force rebuild
                stats = kb.build_from_directories(force_rebuild=True, **kwargs)
                success = stats.get('total_documents', 0) > 0
            
            if success:
                logger.info(f"Successfully rebuilt knowledge base '{name}'")
            else:
                logger.warning(f"Knowledge base '{name}' rebuild completed but no documents found")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rebuild knowledge base '{name}': {e}")
            return False
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rebuild knowledge base '{name}': {e}")
            return False
    
    def _notify_kb_created(self, kb_name: str):
        """
        Notify about KB creation without creating sessions
        
        Args:
            kb_name: Name of created KB
        """
        logger.info(f"Knowledge base '{kb_name}' created successfully")
        
        # Could add UI notification here using Streamlit
        try:
            import streamlit as st
            if hasattr(st, 'success'):
                st.success(f"✅ Knowledge base '{kb_name}' created successfully!")
        except:
            pass  # Silent fail if Streamlit not available
    
    def _handle_kb_deletion_for_sessions(self, kb_name: str) -> Tuple[int, List[str]]:
        """
        Handle KB deletion impact on existing sessions
        
        Args:
            kb_name: Name of deleted KB
            
        Returns:
            Tuple of (affected_count, affected_session_names)
        """
        if not self.session_integration:
            return 0, []
        
        try:
            # Import here to avoid circular imports
            from ..sessions.session_manager import SessionOperationContext
            
            # Switch to conversation context to update sessions
            session_manager = self.session_integration.session_manager
            
            # Find affected sessions
            affected_sessions = session_manager.get_sessions_for_knowledge_base(kb_name)
            
            if not affected_sessions:
                return 0, []
            
            affected_names = []
            
            # Update affected sessions with conversation context
            with self.session_integration.with_context(SessionOperationContext.CONVERSATION):
                for session_meta in affected_sessions:
                    session_id = session_meta['id']
                    session_name = session_meta['name']
                    
                    try:
                        # Load session
                        session = session_manager.storage.load_session(session_id)
                        if session:
                            # Add notification message
                            session.add_message(
                                "system",
                                f"⚠️ Knowledge base '{kb_name}' was deleted and is no longer available for this conversation."
                            )
                            # Clear KB reference
                            session.knowledge_base_name = None
                            # Save the updated session
                            session_manager.storage.save_session(session)
                            affected_names.append(session_name)
                            
                            logger.info(f"Updated session '{session_name}' after KB deletion")
                    
                    except Exception as e:
                        logger.error(f"Failed to update session {session_id} after KB deletion: {e}")
            
            return len(affected_names), affected_names
            
        except Exception as e:
            logger.error(f"Error handling KB deletion for sessions: {e}")
            return 0, []


# Wrapper functions for backward compatibility and easy integration
def create_knowledge_base_with_context(name: str, 
                                     config = None,
                                     session_integration = None,
                                     **kwargs) -> bool:
    """
    Wrapper function for creating KB with session context awareness
    
    Args:
        name: KB name
        config: Pipeline configuration
        session_integration: Session integration instance
        **kwargs: Additional KB creation arguments
        
    Returns:
        True if created successfully
    """
    if not config:
        # Try to get config from Streamlit state
        try:
            import streamlit as st
            config = st.session_state.get('config')
        except:
            pass
    
    if not config:
        logger.error("Configuration required for KB creation")
        return False
    
    manager = KnowledgeBaseManager(config, session_integration)
    return manager.create_knowledge_base_simple(name, **kwargs)


def delete_knowledge_base_with_context(name: str, 
                                     config = None,
                                     session_integration = None) -> bool:
    """
    Wrapper function for deleting KB with session context awareness
    
    Args:
        name: KB name
        config: Pipeline configuration
        session_integration: Session integration instance
        
    Returns:
        True if deleted successfully
    """
    if not config:
        # Try to get config from Streamlit state
        try:
            import streamlit as st
            config = st.session_state.get('config')
        except:
            pass
    
    if not config:
        logger.error("Configuration required for KB deletion")
        return False
    
    manager = KnowledgeBaseManager(config, session_integration)
    return manager.delete_knowledge_base(name)


def list_knowledge_bases_with_context(config = None,
                                     session_integration = None) -> List[Dict[str, Any]]:
    """
    Wrapper function for listing KBs with session context awareness
    
    Args:
        config: Pipeline configuration
        session_integration: Session integration instance
        
    Returns:
        List of KB information dictionaries
    """
    if not config:
        # Try to get config from Streamlit state
        try:
            import streamlit as st
            config = st.session_state.get('config')
        except:
            pass
    
    if not config:
        logger.error("Configuration required for listing KBs")
        return []
    
    manager = KnowledgeBaseManager(config, session_integration)
    return manager.list_knowledge_bases()