# src/sessions/__init__.py
"""
Enhanced Session management system for Physics Literature Synthesis Pipeline

This package provides comprehensive session-based conversation management with:
- AI-powered auto-naming
- Performance optimization
- Background processing
- Advanced analytics
- Multiple export formats
- Session search and recommendations

Main classes:
- Session: Individual conversation session with context
- SessionManager: Basic session management interface  
- EnhancedSessionManager: Advanced session management with AI features
- SessionStorage: Persistent storage for sessions
- SessionIntegration: UI integration layer
"""

from .session import Session, SessionMessage, SessionDocument, SessionSettings
from .session_manager import SessionManager
from .enhanced_session_manager import EnhancedSessionManager
from .storage import SessionStorage
from .session_integration import SessionIntegration, get_session_integration, init_session_integration

__all__ = [
    # Core session components
    'Session',
    'SessionMessage', 
    'SessionDocument',
    'SessionSettings',
    
    # Management classes
    'SessionManager',
    'EnhancedSessionManager',
    'SessionStorage',
    
    # Integration layer
    'SessionIntegration',
    'get_session_integration',
    'init_session_integration'
]

# Version info
__version__ = '2.0.0'  # Updated for Phase 4 features