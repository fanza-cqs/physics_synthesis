# src/chat/__init__.py
"""
Chat interfaces and AI assistants for the Physics Literature Synthesis Pipeline.

PHASE 1A: Updated to support reorganized prompt structure while maintaining exports.
PHASE 1B: Enhanced prompt engineering will be added next.
"""

# Core chat functionality
from .chat_interface import ChatInterface, ChatMessage, ChatResponse

# Literature-aware assistants
from .literature_assistant import LiteratureAssistant, LiteratureSearchContext
from .enhanced_physics_assistant import (
    EnhancedPhysicsAssistant, 
    create_enhanced_physics_assistant
)

# PHASE 1A: Export prompt functionality for advanced users
# These are now available from reorganized prompt modules
from .prompts import (
    get_basic_literature_prompt,
    get_enhanced_physics_prompt,
    get_concept_explanation_prefix,
    get_literature_survey_template,
    get_research_brainstorm_template
)

# Module version for tracking changes
__version__ = "1.0.0-restructured"

# Maintain all exports for backward compatibility
__all__ = [
    # Core chat
    'ChatInterface',
    'ChatMessage', 
    'ChatResponse',
    
    # Assistants
    'LiteratureAssistant',
    'LiteratureSearchContext',
    'EnhancedPhysicsAssistant',
    'create_enhanced_physics_assistant',
    
    # Prompts (now from reorganized structure)
    'get_basic_literature_prompt',
    'get_enhanced_physics_prompt',
    'get_concept_explanation_prefix',
    'get_literature_survey_template',
    'get_research_brainstorm_template'
]