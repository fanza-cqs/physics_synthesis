#!/usr/bin/env python3
"""
Prompt management module for the Physics Literature Synthesis Pipeline.

This module provides modular prompt engineering capabilities for the AI assistants.
Extracted and reorganized during Phase 1A restructuring.

Phase 1A: Extract existing prompts into organized modules
Phase 1B: Enhanced prompt engineering with modular components
"""

# Backward compatible exports - existing prompts (Phase 1A)
from .legacy_prompts import (
    get_basic_literature_prompt,
    get_enhanced_physics_prompt,
    get_concept_explanation_prefix,
    get_literature_survey_template,
    get_research_brainstorm_template
)

# Phase 1B: Enhanced prompt engineering components
from .prompt_manager import PromptManager, PromptConfig, PromptStyle
from .physics_expertise import PhysicsExpertiseModule
from .context_formatting import ContextFormattingModule
from .scientific_lexicon import ScientificLexiconModule

# Factory function for creating prompt managers
def create_prompt_manager(style: str = "modular", **config_kwargs) -> PromptManager:
    """
    Factory function to create prompt managers.
    
    Args:
        style: Prompt style ("basic", "enhanced", "modular")
        **config_kwargs: Configuration parameters for PromptConfig
    
    Returns:
        Initialized prompt manager
    """
    if style == "basic":
        config = PromptConfig(style=PromptStyle.BASIC, **config_kwargs)
    elif style == "enhanced":
        config = PromptConfig(style=PromptStyle.ENHANCED, **config_kwargs)
    else:  # modular (default)
        config = PromptConfig(style=PromptStyle.MODULAR, **config_kwargs)
    
    return PromptManager(config)

# Module version for tracking restructuring
__version__ = "1.1.0-enhanced"

# Re-export everything for backward compatibility plus new functionality
__all__ = [
    # Legacy prompts (Phase 1A)
    'get_basic_literature_prompt',
    'get_enhanced_physics_prompt',
    'get_concept_explanation_prefix',
    'get_literature_survey_template',
    'get_research_brainstorm_template',
    
    # Enhanced prompt engineering (Phase 1B)
    'PromptManager',
    'PromptConfig',
    'PromptStyle',
    'PhysicsExpertiseModule',
    'ContextFormattingModule',
    'ScientificLexiconModule',
    
    # Factory functions
    'create_prompt_manager'
]