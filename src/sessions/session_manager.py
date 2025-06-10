# src/sessions/session_manager.py
"""
Session Manager for Physics Literature Synthesis Pipeline
High-level interface for managing conversation sessions
"""

from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime
import logging

from .session import Session, SessionDocument
from .storage import SessionStorage
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SessionManager:
    """
    High-level session management interface
    Handles session CRUD operations, auto-naming, and lifecycle management
    """
    
    def __init__(self, project_root: Path):
        """
        Initialize session manager
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.storage = SessionStorage(project_root)
        self._current_session: Optional[Session] = None
        
        logger.info(f"SessionManager initialized with project root: {project_root}")
    
    @property
    def current_session(self) -> Optional[Session]:
        """Get the currently active session"""
        return self._current_session
    
    def create_session(self, 
                      name: Optional[str] = None,
                      knowledge_base_name: Optional[str] = None,
                      auto_activate: bool = True) -> Session:
        """
        Create a new session
        
        Args:
            name: Session name (auto-generated if None)
            knowledge_base_name: Knowledge base to attach (optional)
            auto_activate: Whether to make this the current session
            
        Returns:
            Created session
        """
        session = Session(
            name=name,
            knowledge_base_name=knowledge_base_name
        )
        
        # Save immediately
        if self.storage.save_session(session):
            logger.info(f"Created new session: {session.id} - '{session.name}'")
            
            if auto_activate:
                self._current_session = session
                logger.debug(f"Activated session: {session.id}")
            
            return session
        else:
            raise RuntimeError(f"Failed to save new session: {session.id}")
    
    def load_session(self, session_id: str, auto_activate: bool = True) -> Optional[Session]:
        """
        Load an existing session
        
        Args:
            session_id: ID of session to load
            auto_activate: Whether to make this the current session
            
        Returns:
            Loaded session or None if not found
        """
        session = self.storage.load_session(session_id)
        
        if session:
            logger.info(f"Loaded session: {session_id} - '{session.name}'")
            
            if auto_activate:
                self._current_session = session
                logger.debug(f"Activated session: {session_id}")
            
            return session
        else:
            logger.warning(f"Session not found: {session_id}")
            return None
    
    def save_current_session(self) -> bool:
        """
        Save the current session to disk
        
        Returns:
            True if saved successfully, False otherwise
        """
        if not self._current_session:
            logger.warning("No current session to save")
            return False
        
        success = self.storage.save_session(self._current_session)
        if success:
            logger.debug(f"Saved current session: {self._current_session.id}")
        else:
            logger.error(f"Failed to save current session: {self._current_session.id}")
        
        return success
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: ID of session to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        # If deleting current session, clear it
        if self._current_session and self._current_session.id == session_id:
            self._current_session = None
            logger.info("Cleared current session (was deleted)")
        
        success = self.storage.delete_session(session_id)
        if success:
            logger.info(f"Deleted session: {session_id}")
        else:
            logger.error(f"Failed to delete session: {session_id}")
        
        return success
    
    def list_sessions(self) -> List[Dict]:
        """
        Get list of all sessions with metadata
        
        Returns:
            List of session metadata dictionaries, sorted by last activity
        """
        return self.storage.get_all_sessions_metadata()
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """
        Get metadata for a specific session
        
        Args:
            session_id: Session ID
            
        Returns:
            Session metadata dictionary or None if not found
        """
        return self.storage.get_session_metadata(session_id)
    
    def rename_session(self, session_id: str, new_name: str) -> bool:
        """
        Rename a session
        
        Args:
            session_id: ID of session to rename
            new_name: New name for the session
            
        Returns:
            True if renamed successfully, False otherwise
        """
        try:
            # If it's the current session, update directly
            if self._current_session and self._current_session.id == session_id:
                self._current_session.set_name(new_name)
                return self.save_current_session()
            
            # Otherwise, load, rename, and save
            session = self.storage.load_session(session_id)
            if session:
                session.set_name(new_name)
                success = self.storage.save_session(session)
                if success:
                    logger.info(f"Renamed session {session_id} to '{new_name}'")
                return success
            else:
                logger.warning(f"Cannot rename - session not found: {session_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to rename session {session_id}: {e}")
            return False
    
    def add_message_to_current(self, role: str, content: str, sources: List[str] = None) -> bool:
        """
        Add a message to the current session
        
        Args:
            role: Message role ("user" or "assistant")
            content: Message content
            sources: List of source references (optional)
            
        Returns:
            True if message added successfully, False otherwise
        """
        if not self._current_session:
            logger.warning("No current session - cannot add message")
            return False
        
        try:
            self._current_session.add_message(role, content, sources)
            
            # Auto-save after each message
            success = self.save_current_session()
            if success:
                logger.debug(f"Added {role} message to session {self._current_session.id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to add message to current session: {e}")
            return False
    
    def add_document_to_current(self, file_path: Path, original_name: str) -> Optional[SessionDocument]:
        """
        Add a document to the current session
        
        Args:
            file_path: Path to the document file
            original_name: Original filename
            
        Returns:
            SessionDocument if added successfully, None otherwise
        """
        if not self._current_session:
            logger.warning("No current session - cannot add document")
            return None
        
        try:
            # Store document in session storage
            stored_path = self.storage.store_document(
                self._current_session.id, 
                file_path, 
                original_name
            )
            
            # Add to session
            doc = self._current_session.add_document(stored_path, original_name)
            
            # Save session
            if self.save_current_session():
                logger.info(f"Added document '{original_name}' to session {self._current_session.id}")
                return doc
            else:
                logger.error("Failed to save session after adding document")
                return None
                
        except Exception as e:
            logger.error(f"Failed to add document to current session: {e}")
            return None
    
    def remove_document_from_current(self, filename: str) -> bool:
        """
        Remove a document from the current session
        
        Args:
            filename: Name of document to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        if not self._current_session:
            logger.warning("No current session - cannot remove document")
            return False
        
        try:
            success = self._current_session.remove_document(filename)
            
            if success:
                # Save session
                if self.save_current_session():
                    logger.info(f"Removed document '{filename}' from session {self._current_session.id}")
                    return True
                else:
                    logger.error("Failed to save session after removing document")
                    return False
            else:
                logger.warning(f"Document '{filename}' not found in current session")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove document from current session: {e}")
            return False
    
    def set_knowledge_base_for_current(self, kb_name: Optional[str]) -> bool:
        """
        Set the knowledge base for the current session
        
        Args:
            kb_name: Name of knowledge base (None to remove)
            
        Returns:
            True if set successfully, False otherwise
        """
        if not self._current_session:
            logger.warning("No current session - cannot set knowledge base")
            return False
        
        try:
            old_kb = self._current_session.knowledge_base_name
            self._current_session.set_knowledge_base(kb_name)
            
            # Save session
            if self.save_current_session():
                logger.info(f"Changed KB for session {self._current_session.id}: '{old_kb}' -> '{kb_name}'")
                return True
            else:
                logger.error("Failed to save session after setting knowledge base")
                return False
                
        except Exception as e:
            logger.error(f"Failed to set knowledge base for current session: {e}")
            return False
    
    def update_current_session_settings(self, **kwargs) -> bool:
        """
        Update settings for the current session
        
        Args:
            **kwargs: Settings to update (temperature, max_sources, response_style)
            
        Returns:
            True if updated successfully, False otherwise
        """
        if not self._current_session:
            logger.warning("No current session - cannot update settings")
            return False
        
        try:
            self._current_session.update_settings(**kwargs)
            
            # Save session
            if self.save_current_session():
                logger.debug(f"Updated settings for session {self._current_session.id}: {kwargs}")
                return True
            else:
                logger.error("Failed to save session after updating settings")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update settings for current session: {e}")
            return False
    
    def get_or_create_default_session(self) -> Session:
        """
        Get current session or create a default one if none exists
        
        Returns:
            Current or newly created session
        """
        if self._current_session:
            return self._current_session
        
        # Check if we have any existing sessions
        sessions = self.list_sessions()
        
        if sessions:
            # Load the most recent session
            most_recent = sessions[0]  # Already sorted by last_active
            session = self.load_session(most_recent['id'], auto_activate=True)
            if session:
                logger.info(f"Loaded most recent session: {session.id}")
                return session
        
        # Create new default session
        session = self.create_session(name="New Session", auto_activate=True)
        logger.info(f"Created default session: {session.id}")
        return session
    
    def switch_to_session(self, session_id: str) -> bool:
        """
        Switch to a different session
        
        Args:
            session_id: ID of session to switch to
            
        Returns:
            True if switched successfully, False otherwise
        """
        # Save current session first
        if self._current_session:
            self.save_current_session()
        
        # Load new session
        session = self.load_session(session_id, auto_activate=True)
        return session is not None
    
    def cleanup_old_empty_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up old empty sessions
        
        Args:
            max_age_hours: Maximum age in hours for empty sessions
            
        Returns:
            Number of sessions cleaned up
        """
        return self.storage.cleanup_empty_sessions(max_age_hours)
    
    def get_sessions_for_knowledge_base(self, kb_name: str) -> List[Dict]:
        """
        Get all sessions that use a specific knowledge base
        
        Args:
            kb_name: Name of knowledge base
            
        Returns:
            List of session metadata for sessions using this KB
        """
        all_sessions = self.list_sessions()
        return [
            session for session in all_sessions 
            if session.get('knowledge_base_name') == kb_name
        ]
    
    def handle_knowledge_base_deleted(self, kb_name: str) -> Tuple[int, List[str]]:
        """
        Handle when a knowledge base is deleted
        Updates all affected sessions and returns info about them
        
        Args:
            kb_name: Name of deleted knowledge base
            
        Returns:
            Tuple of (number_of_affected_sessions, list_of_session_names)
        """
        affected_sessions = self.get_sessions_for_knowledge_base(kb_name)
        affected_names = []
        
        for session_meta in affected_sessions:
            session_id = session_meta['id']
            session_name = session_meta['name']
            
            try:
                # Load session
                session = self.storage.load_session(session_id)
                if session:
                    # Remove KB reference
                    session.set_knowledge_base(None)
                    
                    # Add a system message about the deletion
                    session.add_message(
                        "system",
                        f"⚠️ Knowledge base '{kb_name}' was deleted and is no longer available for this conversation."
                    )
                    
                    # Save session
                    self.storage.save_session(session)
                    affected_names.append(session_name)
                    
                    logger.info(f"Updated session {session_id} - removed deleted KB '{kb_name}'")
                
            except Exception as e:
                logger.error(f"Failed to update session {session_id} after KB deletion: {e}")
        
        return len(affected_names), affected_names
    
    def export_session(self, session_id: str, export_path: Path) -> bool:
        """
        Export a session to a file
        
        Args:
            session_id: ID of session to export
            export_path: Path where to save the export
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            session = self.storage.load_session(session_id)
            if not session:
                logger.error(f"Cannot export - session not found: {session_id}")
                return False
            
            # Create export data
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'session': session.to_dict(),
                'export_version': '1.0'
            }
            
            # Save to file
            import json
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Exported session {session_id} to {export_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export session {session_id}: {e}")
            return False
    
    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        return self.storage.get_storage_stats()
    
    def validate_all_sessions(self) -> Dict[str, List[str]]:
        """
        Validate all sessions and return any issues found
        
        Returns:
            Dictionary with 'valid', 'corrupted', and 'missing_documents' lists
        """
        result = {
            'valid': [],
            'corrupted': [],
            'missing_documents': []
        }
        
        session_ids = self.storage.list_sessions()
        
        for session_id in session_ids:
            try:
                session = self.storage.load_session(session_id)
                if session:
                    # Check for missing documents
                    missing_docs = []
                    for doc in session.documents:
                        if not doc.file_path.exists():
                            missing_docs.append(doc.original_name)
                    
                    if missing_docs:
                        result['missing_documents'].append({
                            'session_id': session_id,
                            'session_name': session.name,
                            'missing_docs': missing_docs
                        })
                    else:
                        result['valid'].append(session_id)
                else:
                    result['corrupted'].append(session_id)
                    
            except Exception as e:
                logger.error(f"Session validation failed for {session_id}: {e}")
                result['corrupted'].append(session_id)
        
        return result
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - save current session"""
        if self._current_session:
            self.save_current_session()