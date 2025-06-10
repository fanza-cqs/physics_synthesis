# src/sessions/session.py
"""
Session data model for Physics Literature Synthesis Pipeline
Handles individual conversation sessions with their context (KB + documents + messages)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
from pathlib import Path


@dataclass
class SessionMessage:
    """Individual message in a session"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    sources: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionDocument:
    """Document uploaded to a session"""
    filename: str
    original_name: str
    file_path: Path
    upload_timestamp: datetime
    file_size: int
    file_type: str
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'filename': self.filename,
            'original_name': self.original_name,
            'file_path': str(self.file_path),
            'upload_timestamp': self.upload_timestamp.isoformat(),
            'file_size': self.file_size,
            'file_type': self.file_type,
            'processed': self.processed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionDocument':
        """Create from dictionary (JSON deserialization)"""
        return cls(
            filename=data['filename'],
            original_name=data['original_name'],
            file_path=Path(data['file_path']),
            upload_timestamp=datetime.fromisoformat(data['upload_timestamp']),
            file_size=data['file_size'],
            file_type=data['file_type'],
            processed=data.get('processed', False)
        )


@dataclass
class SessionSettings:
    """Chat settings for a session"""
    temperature: float = 0.3
    max_sources: int = 8
    response_style: str = "detailed"  # detailed, concise, technical
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'temperature': self.temperature,
            'max_sources': self.max_sources,
            'response_style': self.response_style
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionSettings':
        """Create from dictionary (JSON deserialization)"""
        return cls(
            temperature=data.get('temperature', 0.3),
            max_sources=data.get('max_sources', 8),
            response_style=data.get('response_style', 'detailed')
        )


class Session:
    """
    A conversation session with its complete context
    Like in Claude/ChatGPT - independent workspace with KB + documents + messages
    """
    
    def __init__(self, 
                 session_id: Optional[str] = None,
                 name: Optional[str] = None,
                 knowledge_base_name: Optional[str] = None):
        """
        Initialize a new session
        
        Args:
            session_id: Unique session ID (auto-generated if None)
            name: Session name (auto-generated if None)
            knowledge_base_name: Name of KB to load (optional)
        """
        self.id = session_id or str(uuid.uuid4())
        self.name = name or "New Session"
        self.created_at = datetime.now()
        self.last_active = datetime.now()
        
        # Context
        self.knowledge_base_name: Optional[str] = knowledge_base_name
        self.documents: List[SessionDocument] = []
        self.settings = SessionSettings()
        
        # Conversation
        self.messages: List[SessionMessage] = []
        
        # State
        self.auto_named = False  # True if name was auto-generated from conversation
    
    def add_message(self, role: str, content: str, sources: List[str] = None) -> SessionMessage:
        """Add a message to the session"""
        message = SessionMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            sources=sources or []
        )
        self.messages.append(message)
        self.last_active = datetime.now()
        
        # Auto-name session if it's the first user message and not already named
        if (role == "user" and len(self.messages) == 1 and 
            self.name == "New Session" and not self.auto_named):
            self.auto_name_from_first_message(content)
        
        return message
    
    def add_document(self, file_path: Path, original_name: str) -> SessionDocument:
        """Add a document to the session"""
        doc = SessionDocument(
            filename=f"session_{self.id}_{len(self.documents)}_{original_name}",
            original_name=original_name,
            file_path=file_path,
            upload_timestamp=datetime.now(),
            file_size=file_path.stat().st_size if file_path.exists() else 0,
            file_type=file_path.suffix.lower()
        )
        self.documents.append(doc)
        self.last_active = datetime.now()
        return doc
    
    def remove_document(self, filename: str) -> bool:
        """Remove a document from the session"""
        for i, doc in enumerate(self.documents):
            if doc.filename == filename or doc.original_name == filename:
                # Remove file if it exists
                if doc.file_path.exists():
                    try:
                        doc.file_path.unlink()
                    except Exception:
                        pass  # File might be in use or already deleted
                
                # Remove from list
                del self.documents[i]
                self.last_active = datetime.now()
                return True
        return False
    
    def set_knowledge_base(self, kb_name: Optional[str]):
        """Set the knowledge base for this session"""
        self.knowledge_base_name = kb_name
        self.last_active = datetime.now()
    
    def update_settings(self, **kwargs):
        """Update session settings"""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        self.last_active = datetime.now()
    
    def auto_name_from_first_message(self, content: str):
        """Auto-name session from first user message"""
        # Take first 50 characters, remove newlines, add ellipsis if truncated
        name = content.replace('\n', ' ').strip()
        if len(name) > 50:
            name = name[:47] + "..."
        
        self.name = name
        self.auto_named = True
    
    def set_name(self, name: str):
        """Set session name (user rename)"""
        self.name = name
        self.auto_named = False  # User explicitly named it
        self.last_active = datetime.now()
    
    def get_message_count(self) -> int:
        """Get total number of messages"""
        return len(self.messages)
    
    def get_user_message_count(self) -> int:
        """Get number of user messages"""
        return len([m for m in self.messages if m.role == "user"])
    
    def get_document_count(self) -> int:
        """Get number of uploaded documents"""
        return len(self.documents)
    
    def has_knowledge_base(self) -> bool:
        """Check if session has a knowledge base"""
        return self.knowledge_base_name is not None
    
    def has_documents(self) -> bool:
        """Check if session has uploaded documents"""
        return len(self.documents) > 0
    
    def has_messages(self) -> bool:
        """Check if session has any messages"""
        return len(self.messages) > 0
    
    def is_empty(self) -> bool:
        """Check if session is empty (no messages, no documents)"""
        return not self.has_messages() and not self.has_documents()
    
    def get_context_summary(self) -> str:
        """Get a summary of the session context"""
        parts = []
        
        if self.knowledge_base_name:
            parts.append(f"KB: {self.knowledge_base_name}")
        
        if self.documents:
            parts.append(f"{len(self.documents)} doc(s)")
        
        if not parts:
            parts.append("No context")
        
        return " • ".join(parts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'last_active': self.last_active.isoformat(),
            'knowledge_base_name': self.knowledge_base_name,
            'documents': [doc.to_dict() for doc in self.documents],
            'settings': self.settings.to_dict(),
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'sources': msg.sources,
                    'metadata': msg.metadata
                }
                for msg in self.messages
            ],
            'auto_named': self.auto_named
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Session':
        """Create session from dictionary (JSON deserialization)"""
        session = cls(
            session_id=data['id'],
            name=data['name'],
            knowledge_base_name=data.get('knowledge_base_name')
        )
        
        session.created_at = datetime.fromisoformat(data['created_at'])
        session.last_active = datetime.fromisoformat(data['last_active'])
        session.auto_named = data.get('auto_named', False)
        
        # Load documents
        session.documents = [
            SessionDocument.from_dict(doc_data) 
            for doc_data in data.get('documents', [])
        ]
        
        # Load settings
        if 'settings' in data:
            session.settings = SessionSettings.from_dict(data['settings'])
        
        # Load messages
        for msg_data in data.get('messages', []):
            message = SessionMessage(
                role=msg_data['role'],
                content=msg_data['content'],
                timestamp=datetime.fromisoformat(msg_data['timestamp']),
                sources=msg_data.get('sources', []),
                metadata=msg_data.get('metadata', {})
            )
            session.messages.append(message)
        
        return session
    
    def __str__(self) -> str:
        """String representation of session"""
        return f"Session(id={self.id[:8]}, name='{self.name}', messages={len(self.messages)})"
    
    def __repr__(self) -> str:
        """Detailed string representation"""
        return (f"Session(id='{self.id}', name='{self.name}', "
                f"kb='{self.knowledge_base_name}', messages={len(self.messages)}, "
                f"documents={len(self.documents)}, created={self.created_at})")