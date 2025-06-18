#!/usr/bin/env python3
"""
Modular prompt management system for the Physics Literature Synthesis Pipeline.

This module provides a flexible system for assembling and managing AI prompts
with modular components for physics expertise, context formatting, and more.

Phase 1B: Enhanced prompt engineering for better AI responses.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from .physics_expertise import PhysicsExpertiseModule
from .context_formatting import ContextFormattingModule  
from .scientific_lexicon import ScientificLexiconModule
from .legacy_prompts import get_basic_literature_prompt, get_enhanced_physics_prompt

class PromptStyle(Enum):
    """Available prompt styles."""
    BASIC = "basic"
    ENHANCED = "enhanced"
    MODULAR = "modular"

@dataclass
class PromptConfig:
    """Configuration for prompt generation."""
    style: PromptStyle = PromptStyle.MODULAR
    physics_expertise_level: str = "enhanced"  # "basic", "enhanced", "expert"
    context_integration: str = "structured"    # "simple", "structured", "advanced"
    scientific_lexicon: str = "precise"        # "basic", "precise", "technical"
    citation_style: str = "scientific"         # "basic", "scientific", "academic"
    response_structure: str = "comprehensive"  # "simple", "comprehensive", "detailed"

class PromptManager:
    """
    Modular prompt management system.
    
    This class assembles AI prompts from modular components, allowing for
    flexible and configurable prompt engineering while maintaining
    backward compatibility with existing prompts.
    
    Features:
    - Modular prompt components
    - Configuration-driven assembly
    - A/B testing support
    - Backward compatibility
    - Physics-specific enhancements
    """
    
    def __init__(self, config: PromptConfig = None):
        """
        Initialize the prompt manager.
        
        Args:
            config: Configuration for prompt generation
        """
        self.config = config or PromptConfig()
        
        # Initialize modular components
        self.physics_module = PhysicsExpertiseModule()
        self.context_module = ContextFormattingModule()
        self.lexicon_module = ScientificLexiconModule()
        
        # Track generated prompts for debugging/analysis
        self.generated_prompts: List[Dict[str, Any]] = []
    
    def generate_system_prompt(self, 
                             kb_stats: Dict[str, Any],
                             prompt_type: str = "literature_assistant") -> str:
        """
        Generate a system prompt based on configuration.
        
        Args:
            kb_stats: Knowledge base statistics
            prompt_type: Type of prompt ("literature_assistant", "enhanced_physics")
        
        Returns:
            Generated system prompt string
        """
        if self.config.style == PromptStyle.BASIC:
            return self._generate_basic_prompt(kb_stats, prompt_type)
        elif self.config.style == PromptStyle.ENHANCED:
            return self._generate_enhanced_prompt(kb_stats, prompt_type)
        else:  # MODULAR
            return self._generate_modular_prompt(kb_stats, prompt_type)
    
    def _generate_basic_prompt(self, kb_stats: Dict[str, Any], prompt_type: str) -> str:
        """Generate basic prompt using legacy system."""
        if prompt_type == "enhanced_physics":
            return get_enhanced_physics_prompt(kb_stats)
        else:
            return get_basic_literature_prompt(kb_stats)
    
    def _generate_enhanced_prompt(self, kb_stats: Dict[str, Any], prompt_type: str) -> str:
        """Generate enhanced prompt with improvements."""
        # Use enhanced version for both types
        base_prompt = get_enhanced_physics_prompt(kb_stats)
        
        # Add context formatting improvements
        context_instructions = self.context_module.get_context_formatting_instructions(
            self.config.context_integration
        )
        
        enhanced_prompt = f"{base_prompt}\n\n{context_instructions}"
        
        return enhanced_prompt
    
    def _generate_modular_prompt(self, kb_stats: Dict[str, Any], prompt_type: str) -> str:
        """Generate fully modular prompt from components."""
        components = []
        
        # 1. Core identity and knowledge base info
        components.append(self._generate_core_identity(kb_stats))
        
        # 2. Physics expertise module
        physics_expertise = self.physics_module.get_physics_expertise_prompt(
            self.config.physics_expertise_level
        )
        components.append(physics_expertise)
        
        # 3. Scientific lexicon guidance
        lexicon_guidance = self.lexicon_module.get_lexicon_guidance(
            self.config.scientific_lexicon
        )
        components.append(lexicon_guidance)
        
        # 4. Context integration instructions
        context_instructions = self.context_module.get_context_formatting_instructions(
            self.config.context_integration
        )
        components.append(context_instructions)
        
        # 5. Response structure guidance
        response_structure = self._generate_response_structure_guidance()
        components.append(response_structure)
        
        # 6. Citation and accuracy instructions
        citation_instructions = self._generate_citation_instructions()
        components.append(citation_instructions)
        
        # Assemble final prompt
        prompt = "\n\n".join(components)
        
        # Track for analysis
        self._track_generated_prompt(prompt, kb_stats, prompt_type)
        
        return prompt
    
    def _generate_core_identity(self, kb_stats: Dict[str, Any]) -> str:
        """Generate core identity section."""
        return f"""You are an expert theoretical physicist and research assistant with comprehensive knowledge across all areas of physics. You have access to a specialized literature database containing {kb_stats.get('total_documents', 0)} physics papers organized into {kb_stats.get('total_chunks', 0)} searchable segments.

KNOWLEDGE BASE OVERVIEW:
- Total Documents: {kb_stats.get('total_documents', 0)}
- Content Segments: {kb_stats.get('total_chunks', 0)} 
- Source Types: {', '.join(kb_stats.get('source_breakdown', {}).keys()) or 'Various'}
- Embedding Model: {kb_stats.get('embedding_model', 'Unknown')}
- Last Updated: {kb_stats.get('last_updated', 'Unknown')}"""
    
    def _generate_response_structure_guidance(self) -> str:
        """Generate response structure guidance based on configuration."""
        if self.config.response_structure == "simple":
            return """RESPONSE STRUCTURE:
- Provide direct, concise answers
- Include key supporting evidence
- Maintain scientific accuracy"""
        
        elif self.config.response_structure == "comprehensive":
            return """RESPONSE STRUCTURE:
- Start with a direct answer to the question
- Provide relevant background from the literature
- Explain underlying physics principles
- Include mathematical relationships when appropriate
- Discuss experimental context or evidence
- Suggest connections to broader physics topics
- Offer directions for further exploration"""
        
        else:  # detailed
            return """RESPONSE STRUCTURE:
- Executive Summary: Direct answer with key insights
- Literature Foundation: Detailed grounding in available sources
- Physics Analysis: Deep dive into underlying principles and mechanisms
- Mathematical Framework: Relevant equations and their physical meaning
- Experimental Context: Observational evidence and measurement approaches
- Cross-Domain Connections: Links to other physics areas
- Open Questions: Unresolved issues and research directions
- Further Resources: Specific papers and topics for deeper study"""
    
    def _generate_citation_instructions(self) -> str:
        """Generate citation instructions based on configuration."""
        if self.config.citation_style == "basic":
            return """CITATION GUIDELINES:
- Reference sources when making specific claims
- Use format: [Source: filename]
- Distinguish between literature claims and your reasoning"""
        
        elif self.config.citation_style == "scientific":
            return """CITATION GUIDELINES:
- Always cite specific sources for factual claims: [Literature: paper_name.pdf]
- Reference user's work appropriately: [Your work: filename.tex]
- Cite current drafts when relevant: [Draft: filename]
- When multiple sources support a claim, list all relevant citations
- Clearly distinguish between established results and recent developments
- Acknowledge uncertainty when information is incomplete or conflicting"""
        
        else:  # academic
            return """CITATION GUIDELINES:
- Comprehensive source attribution for all factual claims
- If appropriate, cite more than one reference
- Format: [Literature: Author_Year_Journal.pdf] for publications
- Format: [Your work: filename.tex] for user's research
- Format: [Draft: filename] for works in progress
- Cross-reference multiple sources when possible
- Note methodological approaches from different papers
- Highlight consensus vs. disputed findings in the literature
- Provide context for citation relevance and reliability
- Suggest primary sources when citing review papers"""
    
    def _track_generated_prompt(self, prompt: str, kb_stats: Dict[str, Any], prompt_type: str) -> None:
        """Track generated prompt for analysis."""
        prompt_record = {
            'prompt_type': prompt_type,
            'config': self.config.__dict__,
            'kb_stats': kb_stats,
            'prompt_length': len(prompt),
            'word_count': len(prompt.split()),
            'components_used': [
                'core_identity',
                'physics_expertise', 
                'lexicon_guidance',
                'context_instructions',
                'response_structure',
                'citation_instructions'
            ]
        }
        
        self.generated_prompts.append(prompt_record)
    
    def get_context_formatting_instructions(self, 
                                          context_style: str = None) -> str:
        """
        Get context formatting instructions for retrieved literature.
        
        Args:
            context_style: Style override for context formatting
        
        Returns:
            Context formatting instructions
        """
        style = context_style or self.config.context_integration
        return self.context_module.get_context_formatting_instructions(style)
    
    def format_context_for_prompt(self, 
                                search_results: List[Any],
                                query: str) -> str:
        """
        Format search results for inclusion in AI prompt.
        
        Args:
            search_results: List of search results from knowledge base
            query: Original user query
        
        Returns:
            Formatted context string ready for prompt inclusion
        """
        return self.context_module.format_search_results(
            search_results, 
            query,
            self.config.context_integration
        )
    
    def get_prompt_analysis(self) -> Dict[str, Any]:
        """
        Get analysis of generated prompts.
        
        Returns:
            Dictionary with prompt generation statistics and analysis
        """
        if not self.generated_prompts:
            return {'total_prompts': 0}
        
        total_prompts = len(self.generated_prompts)
        avg_length = sum(p['prompt_length'] for p in self.generated_prompts) / total_prompts
        avg_words = sum(p['word_count'] for p in self.generated_prompts) / total_prompts
        
        prompt_types = {}
        for prompt in self.generated_prompts:
            ptype = prompt['prompt_type']
            prompt_types[ptype] = prompt_types.get(ptype, 0) + 1
        
        return {
            'total_prompts': total_prompts,
            'average_length': round(avg_length, 2),
            'average_word_count': round(avg_words, 2),
            'prompt_types': prompt_types,
            'current_config': self.config.__dict__
        }
    
    def update_config(self, **kwargs) -> None:
        """
        Update prompt configuration.
        
        Args:
            **kwargs: Configuration parameters to update
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")
    
    def clone_with_config(self, **kwargs) -> 'PromptManager':
        """
        Create a new PromptManager with modified configuration.
        
        Args:
            **kwargs: Configuration parameters to change
        
        Returns:
            New PromptManager instance with updated configuration
        """
        new_config = PromptConfig(**self.config.__dict__)
        
        for key, value in kwargs.items():
            if hasattr(new_config, key):
                setattr(new_config, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")
        
        return PromptManager(new_config)