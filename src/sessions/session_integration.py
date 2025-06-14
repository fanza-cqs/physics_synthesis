# src/sessions/session_integration.py
"""
Session Integration module for Physics Literature Synthesis Pipeline
Handles integration between session system and UI components with context awareness
"""

import streamlit as st
from typing import Optional, Dict, Any, List
from pathlib import Path
import logging

from .session_manager import SessionManager, SessionOperationContext
from .session import Session
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SessionIntegration:
    """
    Handles integration between session system and Streamlit UI
    Provides high-level session management for the UI with context awareness
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize session integration
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
    
    def with_context(self, context: SessionOperationContext):
        """Context manager for session operations"""
        class ContextManager:
            def __init__(self, sm, ctx):
                self.session_manager = sm
                self.context = ctx
                self.previous_context = None
            
            def __enter__(self):
                self.previous_context = self.session_manager._operation_context
                self.session_manager.set_operation_context(self.context)
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                self.session_manager.set_operation_context(self.previous_context)
        
        return ContextManager(self.session_manager, context)
    
    def ensure_current_session(self) -> Optional[Session]:
        """
        Ensure there's always a current session for conversation
        Creates default session if none exists
        
        Returns:
            Current session or None if not in conversation context
        """
        # Don't create sessions during app initialization
        if self.session_manager._operation_context == SessionOperationContext.APP_INITIALIZATION:
            logger.debug("Skipping session creation during app initialization")
            return None
        
        with self.with_context(SessionOperationContext.CONVERSATION):
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
                
                # Only create new session if explicitly in conversation context
                # NOT during app initialization or other non-conversation contexts
                if self.session_manager._operation_context == SessionOperationContext.CONVERSATION:
                    session = self.session_manager.create_session(
                        name="New Session",
                        auto_activate=True,
                        trigger="user_initiated"
                    )
                    if session:
                        logger.info(f"Created new default session: {session.id}")
                    return session
            
            return current_session
    
    def sync_session_to_streamlit(self, session: Session):
        """
        Sync session state to Streamlit session state
        
        Args:
            session: Session to sync
        """
        if not session:
            return
        
        # Update chat settings in Streamlit state
        st.session_state.chat_temperature = session.settings.temperature
        st.session_state.max_sources = session.settings.max_sources
        st.session_state.response_style = session.settings.response_style
        
        # Update session context
        st.session_state.current_session_id = session.id
        st.session_state.current_session_name = session.name
        st.session_state.current_kb = session.knowledge_base_name
        
        logger.debug(f"Synced session {session.id} to Streamlit state")
    
    def create_new_session(self, name: Optional[str] = None, kb_name: Optional[str] = None) -> Optional[Session]:
        """
        Create a new session for conversation
        
        Args:
            name: Session name (auto-generated if None)
            kb_name: Knowledge base to attach (optional)
            
        Returns:
            Created session or None if creation not allowed
        """
        with self.with_context(SessionOperationContext.CONVERSATION):
            session = self.session_manager.create_session(
                name=name,
                knowledge_base_name=kb_name,
                auto_activate=True,
                trigger="user_initiated"
            )
            
            if session:
                self.sync_session_to_streamlit(session)
                logger.info(f"Created new session via integration: {session.id}")
            
            return session
    
    def switch_to_session(self, session_id: str) -> bool:
        """
        Switch to a different session
        
        Args:
            session_id: ID of session to switch to
            
        Returns:
            True if switched successfully, False otherwise
        """
        with self.with_context(SessionOperationContext.CONVERSATION):
            success = self.session_manager.switch_to_session(session_id)
            
            if success:
                current_session = self.session_manager.current_session
                if current_session:
                    self.sync_session_to_streamlit(current_session)
                    logger.info(f"Switched to session {session_id} via integration")
            
            return success
    
    def handle_user_message(self, content: str) -> bool:
        """
        Handle user message in conversation context
        
        Args:
            content: Message content
            
        Returns:
            True if message added successfully, False otherwise
        """
        with self.with_context(SessionOperationContext.CONVERSATION):
            # Ensure session exists
            session = self.ensure_current_session()
            if not session:
                logger.error("Cannot add message - no session available")
                return False
            
            # Add message
            success = self.session_manager.add_message_to_current("user", content)
            
            if success:
                self.sync_session_to_streamlit(session)
                logger.debug(f"Added user message to session {session.id}")
            
            return success
    


    # Replace the handle_session_rename method in SessionIntegration with this:

    def handle_session_rename(self, session_id: str, new_name: str) -> bool:
        """
        Handle session rename operation
        
        Args:
            session_id: ID of session to rename
            new_name: New name for the session
            
        Returns:
            True if renamed successfully, False otherwise
        """
        try:
            success = self.session_manager.rename_session(session_id, new_name)
            
            if success:
                # CRITICAL: If this is the current session, we must reload it completely
                current_session = self.session_manager.current_session
                if current_session and current_session.id == session_id:
                    # Force reload the current session from storage to get updated name
                    fresh_session = self.session_manager.load_session(session_id, auto_activate=False)
                    if fresh_session:
                        # Replace the current session object with the fresh one
                        self.session_manager._current_session = fresh_session
                        # Sync the fresh session data to Streamlit
                        self.sync_session_to_streamlit(fresh_session)
                        logger.info(f"Reloaded current session {session_id} after rename to '{new_name}'")
                    else:
                        logger.error(f"Failed to reload session {session_id} after rename")
                        return False
                
                logger.info(f"Renamed session {session_id} to '{new_name}' via integration")
                return True
            else:
                logger.error(f"Failed to rename session {session_id} in session manager")
                return False
                
        except Exception as e:
            logger.error(f"Failed to rename session {session_id}: {e}")
            return False

    def handle_assistant_response(self, content: str, sources: List[str] = None) -> bool:
        """
        Handle assistant response in conversation context
        
        Args:
            content: Response content
            sources: Source references (optional)
            
        Returns:
            True if response added successfully, False otherwise
        """
        with self.with_context(SessionOperationContext.CONVERSATION):
            session = self.session_manager.current_session
            if not session:
                logger.error("Cannot add response - no current session")
                return False
            
            # Add response
            success = self.session_manager.add_message_to_current("assistant", content, sources)
            
            if success:
                self.sync_session_to_streamlit(session)
                logger.debug(f"Added assistant response to session {session.id}")
            
            return success
    
    def handle_kb_selection(self, kb_name: Optional[str]) -> bool:
        """
        Handle knowledge base selection during conversation
        
        Args:
            kb_name: Name of knowledge base (None to remove)
            
        Returns:
            True if KB set successfully, False otherwise
        """
        with self.with_context(SessionOperationContext.UI_INTERACTION):
            success = self.session_manager.set_knowledge_base_for_current(kb_name)
            
            if success:
                current_session = self.session_manager.current_session
                if current_session:
                    self.sync_session_to_streamlit(current_session)
                    logger.info(f"Set KB '{kb_name}' for session {current_session.id}")
            
            return success
    
    def handle_document_upload(self, uploaded_files) -> List[str]:
        """
        Handle document upload during conversation
        
        Args:
            uploaded_files: Streamlit uploaded files
            
        Returns:
            List of successfully uploaded document names
        """
        with self.with_context(SessionOperationContext.CONVERSATION):
            # Ensure session exists
            session = self.ensure_current_session()
            if not session:
                logger.error("Cannot upload documents - no session available")
                return []
            
            uploaded_names = []
            
            for uploaded_file in uploaded_files:
                try:
                    # Create temporary file
                    temp_dir = Path("temp_uploads")
                    temp_dir.mkdir(exist_ok=True)
                    
                    temp_path = temp_dir / uploaded_file.name
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Add to session
                    doc = self.session_manager.add_document_to_current(temp_path, uploaded_file.name)
                    
                    if doc:
                        uploaded_names.append(uploaded_file.name)
                        logger.info(f"Uploaded document '{uploaded_file.name}' to session {session.id}")
                    
                    # Clean up temp file
                    temp_path.unlink(missing_ok=True)
                    
                except Exception as e:
                    logger.error(f"Failed to upload document '{uploaded_file.name}': {e}")
            
            if uploaded_names:
                self.sync_session_to_streamlit(session)
            
            return uploaded_names
    
    def handle_session_settings_update(self, **kwargs) -> bool:
        """
        Handle session settings update
        
        Args:
            **kwargs: Settings to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        with self.with_context(SessionOperationContext.UI_INTERACTION):
            success = self.session_manager.update_current_session_settings(**kwargs)
            
            if success:
                current_session = self.session_manager.current_session
                if current_session:
                    self.sync_session_to_streamlit(current_session)
                    logger.debug(f"Updated settings for session {current_session.id}: {kwargs}")
            
            return success
    
    def handle_session_deletion(self, session_id: str) -> bool:
        """
        Handle session deletion
        
        Args:
            session_id: ID of session to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        with self.with_context(SessionOperationContext.CONVERSATION):
            success = self.session_manager.delete_session(session_id)
            
            if success:
                logger.info(f"Deleted session {session_id} via integration")
                
                # If we deleted the current session, ensure we have a new one
                if not self.session_manager.current_session:
                    new_session = self.ensure_current_session()
                    if new_session:
                        self.sync_session_to_streamlit(new_session)
            
            return success
    
    def handle_clear_conversation(self) -> bool:
        """
        Handle clearing current conversation
        
        Returns:
            True if conversation was cleared successfully, False otherwise
        """
        with self.with_context(SessionOperationContext.CONVERSATION):
            current_session = self.session_manager.current_session
            if not current_session:
                return False
            
            # Clear messages
            current_session.messages = []
            
            # Save session
            success = self.session_manager.save_current_session("clear_conversation")
            
            if success:
                self.sync_session_to_streamlit(current_session)
                logger.info(f"Cleared conversation for session {current_session.id}")
            
            return success
    
    def get_session_list_for_ui(self) -> List[Dict]:
        """
        Get session list formatted for UI display (always fresh data)
        
        Returns:
            List of session metadata with UI-friendly formatting
        """
        try:
            # Always get fresh session list - no caching
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
    
    def handle_kb_management_operations(self):
        """Set context for KB management operations to prevent session interference"""
        return self.with_context(SessionOperationContext.KB_MANAGEMENT)
    
    def handle_app_initialization(self):
        """Set context for app initialization to prevent session interference"""
        return self.with_context(SessionOperationContext.APP_INITIALIZATION)
    
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
        

    def prepare_new_conversation(self) -> bool:
        """
        Prepare UI for a new conversation (ChatGPT/Claude style)
        Clears current session without creating a new one until first message is sent
        
        Returns:
            True if preparation successful
        """
        try:
            # Clear current session without creating a new one
            self.session_manager._current_session = None
            
            # Set UI state for pending new conversation
            st.session_state.current_session_id = None
            st.session_state.current_session_name = "New Chat"
            st.session_state.current_kb = None
            st.session_state.pending_new_session = True
            
            # Clear any existing chat input
            if 'chat_input' in st.session_state:
                st.session_state.chat_input = ""
            
            logger.info("Prepared UI for new conversation (session will be created on first message)")
            return True
            
        except Exception as e:
            logger.error(f"Error preparing new conversation: {e}")
            return False

    def create_session_on_first_message(self, first_message: str) -> Optional[Session]:
        """
        Create a new session when the user sends their first message
        This implements ChatGPT/Claude-style session creation
        
        Args:
            first_message: The first message content (used for auto-naming)
            
        Returns:
            Created session or None if creation failed
        """
        try:
            with self.with_context(SessionOperationContext.CONVERSATION):
                # Create session with auto-naming based on first message
                session = self.session_manager.create_session(
                    name="New Session",  # Will be auto-renamed after first exchange
                    auto_activate=True,
                    trigger="first_message"
                )
                
                if session:
                    self.sync_session_to_streamlit(session)
                    logger.info(f"Created session on first message: {session.id}")
                    
                    # Clear the pending flag
                    st.session_state.pending_new_session = False
                    
                return session
                
        except Exception as e:
            logger.error(f"Error creating session on first message: {e}")
            return None


def get_session_integration() -> Optional[SessionIntegration]:
    """
    Get or create session integration instance
    
    Returns:
        SessionIntegration instance or None if not available
    """
    if 'session_integration' not in st.session_state:
        session_manager = st.session_state.get('session_manager')
        if not session_manager:
            logger.warning("Session manager not available for integration")
            return None
        
        st.session_state.session_integration = SessionIntegration(session_manager)
    
    return st.session_state.session_integration


def init_session_integration() -> bool:
    """
    Initialize session integration for the app
    
    Returns:
        True if initialized successfully, False otherwise
    """
    try:
        integration = get_session_integration()
        if not integration:
            logger.error("Failed to get session integration")
            return False
        
        # Set app initialization context
        with integration.handle_app_initialization():
            # Ensure we have a current session for conversation
            pass  # Don't create session during app init
        
        logger.info("Session integration initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize session integration: {e}")
        return False