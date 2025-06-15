# src/ui/__init__.py
"""
UI Components for Physics Literature Synthesis Pipeline

Modern React-inspired component architecture for Streamlit
Implements ChatGPT/Claude-style interface with sidebar navigation and chat focus
"""

from .sidebar import Sidebar, render_sidebar_css
from .chat_interface import ChatInterface, render_chat_css, render_enhanced_chat_css
#from .kb_management import KBManagement, render_kb_management_css

# Compatibility aliases
EnhancedChatInterface = ChatInterface

__all__ = [
    'Sidebar',
    'Sidebar', 
    'ChatInterface',
    'EnhancedChatInterface',  # Compatibility alias
    #'KBManagement',
    'render_sidebar_css',
    'render_chat_css',
    'render_enhanced_chat_css',  # Compatibility alias
    #'render_kb_management_css'
]

# Component styling functions
def render_all_css():
    """Render all component CSS styles"""
    render_sidebar_css()
    render_chat_css() 
    #render_kb_management_css()

def render_all_enhanced_css():
    """Render all enhanced CSS styles - compatibility alias"""
    render_sidebar_css()
    render_enhanced_chat_css()  # This calls render_chat_css()
    #render_kb_management_css()

# Version info
__version__ = '1.1.0'