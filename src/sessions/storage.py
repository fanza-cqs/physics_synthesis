# src/sessions/storage.py
"""
Session storage system for Physics Literature Synthesis Pipeline
Handles persistent storage of sessions to JSON files
"""

import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging

from .session import Session
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class SessionStorage:
    """
    Handles persistent storage of sessions to the filesystem
    Each session is stored as a separate JSON file
    """
    
    def __init__(self, storage_root: Path):
        """
        Initialize session storage
        
        Args:
            storage_root: Root directory for all project files
        """
        self.storage_root = Path(storage_root)
        self.sessions_dir = self.storage_root / "sessions"
        self.documents_dir = self.sessions_dir / "documents"
        
        # Create directories
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.documents_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Session storage initialized at: {self.sessions_dir}")
    
    def _get_session_file_path(self, session_id: str) -> Path:
        """Get the file path for a session"""
        return self.sessions_dir / f"session_{session_id}.json"
    
    def _get_document_storage_path(self, session_id: str) -> Path:
        """Get the document storage directory for a session"""
        session_docs_dir = self.documents_dir / session_id
        session_docs_dir.mkdir(exist_ok=True)
        return session_docs_dir
    
    def save_session(self, session: Session) -> bool:
        """
        Save a session to disk
        
        Args:
            session: Session to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            session_file = self._get_session_file_path(session.id)
            
            # Update last_active timestamp
            session.last_active = datetime.now()
            
            # Convert to dictionary
            session_data = session.to_dict()
            
            # Save to JSON file
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"Saved session {session.id} to {session_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save session {session.id}: {e}")
            return False
    
    def load_session(self, session_id: str) -> Optional[Session]:
        """
        Load a session from disk
        
        Args:
            session_id: ID of session to load
            
        Returns:
            Session object if found and loaded successfully, None otherwise
        """
        try:
            session_file = self._get_session_file_path(session_id)
            
            if not session_file.exists():
                logger.warning(f"Session file not found: {session_file}")
                return None
            
            # Load from JSON file
            with open(session_file, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Create session object
            session = Session.from_dict(session_data)
            
            # Validate document paths still exist
            self._validate_session_documents(session)
            
            logger.debug(f"Loaded session {session_id} from {session_file}")
            return session
            
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session and its associated files
        
        Args:
            session_id: ID of session to delete
            
        Returns:
            bool: True if deleted successfully, False otherwise
        """
        try:
            # Load session first to get document info
            session = self.load_session(session_id)
            
            # Delete session documents
            if session:
                for doc in session.documents:
                    if doc.file_path.exists():
                        try:
                            doc.file_path.unlink()
                            logger.debug(f"Deleted document: {doc.file_path}")
                        except Exception as e:
                            logger.warning(f"Could not delete document {doc.file_path}: {e}")
            
            # Delete session document directory
            session_docs_dir = self.documents_dir / session_id
            if session_docs_dir.exists():
                try:
                    shutil.rmtree(session_docs_dir)
                    logger.debug(f"Deleted session documents directory: {session_docs_dir}")
                except Exception as e:
                    logger.warning(f"Could not delete session docs directory {session_docs_dir}: {e}")
            
            # Delete session file
            session_file = self._get_session_file_path(session_id)
            if session_file.exists():
                session_file.unlink()
                logger.debug(f"Deleted session file: {session_file}")
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def list_sessions(self) -> List[str]:
        """
        Get list of all session IDs
        
        Returns:
            List of session IDs sorted by last modified time (newest first)
        """
        try:
            session_files = list(self.sessions_dir.glob("session_*.json"))
            
            # Sort by modification time (newest first)
            session_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # Extract session IDs
            session_ids = []
            for file in session_files:
                # Extract ID from filename: session_<id>.json
                filename = file.stem  # removes .json
                if filename.startswith("session_"):
                    session_id = filename[8:]  # remove "session_" prefix
                    session_ids.append(session_id)
            
            return session_ids
            
        except Exception as e:
            logger.error(f"Failed to list sessions: {e}")
            return []
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict]:
        """
        Get basic metadata about a session without loading the full session
        
        Args:
            session_id: ID of session
            
        Returns:
            Dictionary with basic session info or None if not found
        """
        try:
            session_file = self._get_session_file_path(session_id)
            
            if not session_file.exists():
                return None
            
            # Load just the metadata we need
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return {
                'id': data['id'],
                'name': data['name'],
                'created_at': data['created_at'],
                'last_active': data['last_active'],
                'message_count': len(data.get('messages', [])),
                'document_count': len(data.get('documents', [])),
                'knowledge_base_name': data.get('knowledge_base_name'),
                'has_knowledge_base': data.get('knowledge_base_name') is not None,
                'has_documents': len(data.get('documents', [])) > 0,
                'has_messages': len(data.get('messages', [])) > 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get metadata for session {session_id}: {e}")
            return None
    
    def get_all_sessions_metadata(self) -> List[Dict]:
        """
        Get metadata for all sessions
        
        Returns:
            List of session metadata dictionaries, sorted by last_active (newest first)
        """
        session_ids = self.list_sessions()
        metadata_list = []
        
        for session_id in session_ids:
            metadata = self.get_session_metadata(session_id)
            if metadata:
                metadata_list.append(metadata)
        
        # Sort by last_active (newest first)
        metadata_list.sort(
            key=lambda x: datetime.fromisoformat(x['last_active']), 
            reverse=True
        )
        
        return metadata_list
    
    def store_document(self, session_id: str, document_file: Path, original_name: str) -> Path:
        """
        Store a document for a session
        
        Args:
            session_id: ID of session
            document_file: Path to source document file
            original_name: Original filename
            
        Returns:
            Path to stored document
        """
        try:
            # Get session document storage directory
            session_docs_dir = self._get_document_storage_path(session_id)
            
            # Create unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = document_file.suffix
            stored_filename = f"{timestamp}_{original_name}"
            stored_path = session_docs_dir / stored_filename
            
            # Copy file to session storage
            shutil.copy2(document_file, stored_path)
            
            logger.info(f"Stored document {original_name} for session {session_id} at {stored_path}")
            return stored_path
            
        except Exception as e:
            logger.error(f"Failed to store document {original_name} for session {session_id}: {e}")
            raise
    
    def _validate_session_documents(self, session: Session):
        """
        Validate that all session documents still exist
        Remove references to missing documents
        
        Args:
            session: Session to validate
        """
        valid_documents = []
        
        for doc in session.documents:
            if doc.file_path.exists():
                valid_documents.append(doc)
            else:
                logger.warning(f"Document not found, removing from session: {doc.file_path}")
        
        session.documents = valid_documents
    
    def cleanup_empty_sessions(self, max_age_hours: int = 24) -> int:
        """
        Clean up empty sessions older than specified age
        
        Args:
            max_age_hours: Maximum age in hours for empty sessions
            
        Returns:
            Number of sessions cleaned up
        """
        cleaned_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        try:
            for session_id in self.list_sessions():
                metadata = self.get_session_metadata(session_id)
                
                if not metadata:
                    continue
                
                # Check if session is empty and old enough
                is_empty = not metadata['has_messages'] and not metadata['has_documents']
                created_time = datetime.fromisoformat(metadata['created_at']).timestamp()
                is_old = created_time < cutoff_time
                
                if is_empty and is_old:
                    if self.delete_session(session_id):
                        cleaned_count += 1
                        logger.info(f"Cleaned up empty session: {session_id}")
            
        except Exception as e:
            logger.error(f"Error during session cleanup: {e}")
        
        return cleaned_count
    
    def get_storage_stats(self) -> Dict:
        """
        Get storage statistics
        
        Returns:
            Dictionary with storage statistics
        """
        try:
            session_ids = self.list_sessions()
            total_sessions = len(session_ids)
            
            total_size = 0
            total_documents = 0
            
            # Calculate total size
            for path in self.sessions_dir.rglob("*"):
                if path.is_file():
                    total_size += path.stat().st_size
            
            # Count total documents
            for session_id in session_ids:
                metadata = self.get_session_metadata(session_id)
                if metadata:
                    total_documents += metadata['document_count']
            
            return {
                'total_sessions': total_sessions,
                'total_documents': total_documents,
                'total_size_mb': total_size / (1024 * 1024),
                'storage_path': str(self.sessions_dir)
            }
            
        except Exception as e:
            logger.error(f"Failed to get storage stats: {e}")
            return {
                'total_sessions': 0,
                'total_documents': 0,
                'total_size_mb': 0,
                'storage_path': str(self.sessions_dir)
            }