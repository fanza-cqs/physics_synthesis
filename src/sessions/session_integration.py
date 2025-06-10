# src/sessions/session_integration.py
"""
Session Integration module for Physics Literature Synthesis Pipeline
Handles integration between session system and UI components
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

from .session_manager import SessionManager
from .session import Session
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SessionIntegration:
    """
    Handles integration between session system and Streamlit UI
    Provides high-level session management for the UI
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize session integration
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
    
    def ensure_current_session(self) -> Session:
        """
        Ensure there's always a current session
        Creates default session if none exists
        
        Returns:
            Current session
        """
        current_session = self.session_manager.current_session
        
        if not current_session:
            # Check if we have any existing sessions
            sessions = self.session_manager.list_sessions()
            
            if sessions:
                # Load the most recent session
                most_recent = sessions[0]  # Already sorted by last_active
                session = self.session_manager.load_session(most_recent['id'], auto_activate=True)
                if session:
                    logger.info(f"Loaded most recent session: {session.id}")
                    return session
            
            # Create new default session
            session = self.session_manager.create_session(
                name="New Session",
                auto_activate=True
            )
            logger.info(f"Created new default session: {session.id}")
            return session
        
        return current_session
    
    def sync_session_to_streamlit(self, session: Session):
        """
        Sync session state to Streamlit session state
        
        Args:
            session: Session to sync
        """
        # Update chat settings in Streamlit state
        st.session_state.chat_temperature = session.settings.temperature
        st.session_state.chat_max_sources = session.settings.max_sources
        
        # Store session reference
        st.session_state.current_session_id = session.id
        st.session_state.current_session_name = session.name
        st.session_state.current_kb_name = session.knowledge_base_name
        
        logger.debug(f"Synced session {session.id} to Streamlit state")
    
    def sync_streamlit_to_session(self, session: Session):
        """
        Sync Streamlit session state changes back to session
        
        Args:
            session: Session to update
        """
        # Get current values from Streamlit
        temperature = st.session_state.get('chat_temperature', 0.3)
        max_sources = st.session_state.get('chat_max_sources', 8)
        
        # Update session if values changed
        if (temperature != session.settings.temperature or 
            max_sources != session.settings.max_sources):
            
            self.session_manager.update_current_session_settings(
                temperature=temperature,
                max_sources=max_sources
            )
            
            logger.debug(f"Updated session {session.id} settings from Streamlit state")
    
    def handle_session_switch(self, new_session_id: str) -> bool:
        """
        Handle switching to a different session
        
        Args:
            new_session_id: ID of session to switch to
            
        Returns:
            True if switch was successful, False otherwise
        """
        try:
            # Save current session first
            if self.session_manager.current_session:
                self.sync_streamlit_to_session(self.session_manager.current_session)
                self.session_manager.save_current_session()
            
            # Switch to new session
            if self.session_manager.switch_to_session(new_session_id):
                new_session = self.session_manager.current_session
                self.sync_session_to_streamlit(new_session)
                
                logger.info(f"Successfully switched to session: {new_session_id}")
                return True
            else:
                logger.error(f"Failed to switch to session: {new_session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error switching to session {new_session_id}: {e}")
            return False
    
    def handle_new_session(self, kb_name: Optional[str] = None) -> Optional[Session]:
        """
        Handle creation of a new session
        
        Args:
            kb_name: Knowledge base to assign to new session
            
        Returns:
            New session if created successfully, None otherwise
        """
        try:
            # Save current session first
            if self.session_manager.current_session:
                self.sync_streamlit_to_session(self.session_manager.current_session)
                self.session_manager.save_current_session()
            
            # Create new session
            new_session = self.session_manager.create_session(
                name="New Session",
                knowledge_base_name=kb_name,
                auto_activate=True
            )
            
            # Sync to Streamlit
            self.sync_session_to_streamlit(new_session)
            
            logger.info(f"Created new session: {new_session.id}")
            return new_session
            
        except Exception as e:
            logger.error(f"Error creating new session: {e}")
            return None
    
    def handle_kb_change(self, new_kb_name: Optional[str]) -> bool:
        """
        Handle knowledge base change for current session
        
        Args:
            new_kb_name: New knowledge base name (None for pure chat)
            
        Returns:
            True if change was successful, False otherwise
        """
        try:
            current_session = self.ensure_current_session()
            
            if self.session_manager.set_knowledge_base_for_current(new_kb_name):
                # Update Streamlit state
                st.session_state.current_kb_name = new_kb_name
                
                logger.info(f"Changed KB for session {current_session.id}: {new_kb_name}")
                return True
            else:
                logger.error(f"Failed to change KB for session {current_session.id}")
                return False
                
        except Exception as e:
            logger.error(f"Error changing KB: {e}")
            return False
    
    def handle_document_upload(self, uploaded_files) -> List[str]:
        """
        Handle document upload for current session
        
        Args:
            uploaded_files: Streamlit uploaded files
            
        Returns:
            List of successfully uploaded document names
        """
        current_session = self.ensure_current_session()
        uploaded_names = []
        
        for uploaded_file in uploaded_files:
            try:
                # Save uploaded file temporarily
                temp_file = Path("/tmp") / uploaded_file.name
                with open(temp_file, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Add to session
                doc = self.session_manager.add_document_to_current(temp_file, uploaded_file.name)
                
                if doc:
                    uploaded_names.append(uploaded_file.name)
                    logger.info(f"Added document to session {current_session.id}: {uploaded_file.name}")
                
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()
                    
            except Exception as e:
                logger.error(f"Document upload failed for {uploaded_file.name}: {e}")
        
        return uploaded_names
    
    def handle_message_add(self, role: str, content: str, sources: List[str] = None) -> bool:
        """
        Handle adding a message to current session
        
        Args:
            role: Message role ("user" or "assistant")
            content: Message content
            sources: List of sources (for assistant messages)
            
        Returns:
            True if message was added successfully, False otherwise
        """
        try:
            current_session = self.ensure_current_session()
            
            # Sync any Streamlit state changes first
            self.sync_streamlit_to_session(current_session)
            
            # Add message
            success = self.session_manager.add_message_to_current(role, content, sources)
            
            if success:
                logger.debug(f"Added {role} message to session {current_session.id}")
            else:
                logger.error(f"Failed to add {role} message to session {current_session.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding message: {e}")
            return False
    
    def handle_session_rename(self, session_id: str, new_name: str) -> bool:
        """
        Handle session rename
        
        Args:
            session_id: ID of session to rename
            new_name: New name for session
            
        Returns:
            True if rename was successful, False otherwise
        """
        try:
            success = self.session_manager.rename_session(session_id, new_name)
            
            if success:
                # Update Streamlit state if it's the current session
                if (self.session_manager.current_session and 
                    self.session_manager.current_session.id == session_id):
                    st.session_state.current_session_name = new_name
                
                logger.info(f"Renamed session {session_id} to '{new_name}'")
            else:
                logger.error(f"Failed to rename session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error renaming session {session_id}: {e}")
            return False
    
    def handle_session_delete(self, session_id: str) -> bool:
        """
        Handle session deletion
        
        Args:
            session_id: ID of session to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            # Check if we're deleting the current session
            is_current = (self.session_manager.current_session and 
                         self.session_manager.current_session.id == session_id)
            
            # Delete session
            success = self.session_manager.delete_session(session_id)
            
            if success:
                # If we deleted the current session, create a new one
                if is_current:
                    new_session = self.handle_new_session()
                    if new_session:
                        logger.info(f"Created new session after deleting current session")
                
                logger.info(f"Deleted session {session_id}")
            else:
                logger.error(f"Failed to delete session {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting session {session_id}: {e}")
            return False
    
    def handle_clear_conversation(self) -> bool:
        """
        Handle clearing current conversation
        
        Returns:
            True if conversation was cleared successfully, False otherwise
        """
        try:
            current_session = self.session_manager.current_session
            if not current_session:
                return False
            
            # Clear messages
            current_session.messages = []
            
            # Save session
            success = self.session_manager.save_current_session()
            
            if success:
                logger.info(f"Cleared conversation for session {current_session.id}")
            else:
                logger.error(f"Failed to clear conversation for session {current_session.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error clearing conversation: {e}")
            return False
    
    def get_session_list_for_ui(self) -> List[Dict]:
        """
        Get session list formatted for UI display
        
        Returns:
            List of session metadata with UI-friendly formatting
        """
        try:
            sessions = self.session_manager.list_sessions()
            
            # Add UI-specific formatting
            for session in sessions:
                # Format last active time
                from datetime import datetime
                last_active = datetime.fromisoformat(session['last_active'])
                session['last_active_formatted'] = last_active.strftime('%m/%d %I:%M %p')
                
                # Add context summary
                context_parts = []
                if session.get('knowledge_base_name'):
                    context_parts.append(f"KB: {session['knowledge_base_name']}")
                if session.get('document_count', 0) > 0:
                    context_parts.append(f"{session['document_count']} docs")
                if session.get('message_count', 0) > 0:
                    context_parts.append(f"{session['message_count']} messages")
                
                session['context_summary'] = " • ".join(context_parts) if context_parts else "Empty"
            
            return sessions
            
        except Exception as e:
            logger.error(f"Error getting session list: {e}")
            return []
    
    def validate_session_integrity(self) -> Dict[str, Any]:
        """
        Validate integrity of all sessions
        
        Returns:
            Dictionary with validation results
        """
        try:
            return self.session_manager.validate_all_sessions()
        except Exception as e:
            logger.error(f"Error validating session integrity: {e}")
            return {'valid': [], 'corrupted': [], 'missing_documents': []}
    
    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old empty sessions
        
        Args:
            max_age_hours: Maximum age for empty sessions
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            return self.session_manager.cleanup_old_empty_sessions(max_age_hours)
        except Exception as e:
            logger.error(f"Error cleaning up old sessions: {e}")
            return 0


def get_session_integration() -> SessionIntegration:
    """
    Get or create session integration instance
    
    Returns:
        SessionIntegration instance
    """
    if 'session_integration' not in st.session_state:
        session_manager = st.session_state.get('session_manager')
        if not session_manager:
            raise RuntimeError("Session manager not initialized")
        
        st.session_state.session_integration = SessionIntegration(session_manager)
    
    return st.session_state.session_integration


def init_session_integration():
    """Initialize session integration for the app"""
    try:
        integration = get_session_integration()
        
        # Ensure we have a current session
        current_session = integration.ensure_current_session()
        
        # Sync to Streamlit state
        integration.sync_session_to_streamlit(current_session)
        
        logger.info("Session integration initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize session integration: {e}")
        return False