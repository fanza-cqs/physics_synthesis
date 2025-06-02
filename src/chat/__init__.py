# src/chat/__init__.py
"""Chat modules for AI-powered literature assistance."""

from .chat_interface import ChatInterface, ChatMessage, ChatResponse
from .literature_assistant import LiteratureAssistant, LiteratureSearchContext

__all__ = [
    'ChatInterface',
    'ChatMessage', 
    'ChatResponse',
    'LiteratureAssistant',
    'LiteratureSearchContext'
]