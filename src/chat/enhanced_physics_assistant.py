#!/usr/bin/env python3
"""
Enhanced Physics-Aware Assistant

This module provides an improved version of the literature assistant
with better physics understanding and more sophisticated prompting.

PHASE 1A: Updated to use reorganized prompt structure while maintaining functionality.
PHASE 1B: Enhanced prompt engineering will be added next.

Location: src/chat/enhanced_physics_assistant.py
"""

from .literature_assistant import LiteratureAssistant
from ..core.knowledge_base import KnowledgeBase
from ..utils.logging_config import get_logger

# PHASE 1A: Import prompts from new reorganized structure
from .prompts import (
    get_enhanced_physics_prompt,
    get_concept_explanation_prefix,
    get_literature_survey_template,
    get_research_brainstorm_template
)

logger = get_logger(__name__)

class EnhancedPhysicsAssistant(LiteratureAssistant):
    """
    Enhanced literature assistant with improved physics understanding.
    
    This extends the base LiteratureAssistant with:
    - Better physics-specific system prompts
    - Enhanced context handling for physics concepts
    - Improved source citation formatting
    - Physics-aware conversation flow
    
    PHASE 1A CHANGES:
    - Updated to use prompts from reorganized prompts module
    - Maintains exact same functionality as before restructuring
    - Prepared for Phase 1B enhanced prompt engineering
    """
    
    def __init__(self, knowledge_base: KnowledgeBase, anthropic_api_key: str, chat_config: dict = None):
        """Initialize the enhanced physics assistant."""
        super().__init__(knowledge_base, anthropic_api_key, chat_config)
        
        # PHASE 1A: Override with enhanced physics system prompt using new structure
        self._setup_enhanced_physics_prompt()
    
    def _setup_enhanced_physics_prompt(self) -> None:
        """
        Set up enhanced system prompt with better physics understanding.
        
        PHASE 1A: Now uses prompt from reorganized prompts module.
        PHASE 1B: Will be enhanced with modular prompt engineering.
        """
        kb_stats = self.knowledge_base.get_statistics()
        
        # PHASE 1A: Use prompt from reorganized module instead of hardcoded
        system_prompt = get_enhanced_physics_prompt(kb_stats)
        
        self.chat.set_system_prompt(system_prompt)
        logger.debug("Enhanced physics system prompt configured using reorganized prompt structure")
    
    def ask_physics_question(self, question: str, context_level: str = "research", include_math: bool = True) -> dict:
        """
        Ask a physics question with enhanced context handling.
        
        Args:
            question: The physics question
            context_level: "introductory", "undergraduate", "graduate", or "research"
            include_math: Whether to include mathematical details
        
        Returns:
            Enhanced response with physics-specific metadata
        """
        # Enhance the question with context instructions
        enhanced_question = f"""
        Context level: {context_level}
        Include mathematics: {include_math}
        
        Question: {question}
        
        Please provide a response appropriate for the {context_level} level, 
        {'including relevant mathematical expressions' if include_math else 'focusing on conceptual understanding'}.
        """
        
        # Get the standard response
        response = self.ask(enhanced_question, temperature=0.3, max_context_chunks=6)
        
        # Add physics-specific metadata
        physics_metadata = {
            'context_level': context_level,
            'includes_math': include_math,
            'sources_used': response.sources_used,
            'processing_time': response.processing_time,
            'physics_topics': self._extract_physics_topics(response.content)
        }
        
        return {
            'content': response.content,
            'metadata': physics_metadata,
            'sources': response.sources_used,
            'context_chunks': response.context_chunks_used
        }
    
    def _extract_physics_topics(self, content: str) -> list:
        """Extract physics topics mentioned in the response."""
        # Simple keyword extraction for physics topics
        physics_keywords = {
            'quantum mechanics', 'quantum field theory', 'quantum computing',
            'condensed matter', 'particle physics', 'cosmology', 'relativity',
            'thermodynamics', 'statistical mechanics', 'electromagnetism',
            'optics', 'atomic physics', 'nuclear physics', 'biophysics',
            'superconductivity', 'magnetism', 'phase transitions',
            'many-body systems', 'quantum entanglement', 'quantum information'
        }
        
        content_lower = content.lower()
        found_topics = [topic for topic in physics_keywords if topic in content_lower]
        
        return found_topics
    
    def explain_concept(self, concept: str, level: str = "undergraduate") -> dict:
        """
        Explain a physics concept at a specific level.
        
        Args:
            concept: Physics concept to explain
            level: Education level (introductory, undergraduate, graduate, research)
        
        Returns:
            Detailed concept explanation with metadata
        """
        # PHASE 1A: Use prompt template from reorganized module
        concept_prompt = get_concept_explanation_prefix(concept, level)
        
        response = self.ask(concept_prompt, temperature=0.2, max_context_chunks=5)
        
        return {
            'content': response.content,
            'concept': concept,
            'level': level,
            'sources_used': response.sources_used,
            'physics_topics': self._extract_physics_topics(response.content),
            'processing_time': response.processing_time
        }
    
    def literature_survey(self, topic: str, max_papers: int = 10) -> dict:
        """
        Conduct a literature survey on a specific physics topic.
        
        Args:
            topic: Physics topic to survey
            max_papers: Maximum number of papers to include
        
        Returns:
            Comprehensive literature survey with metadata
        """
        # Find relevant papers first
        search_results = self.knowledge_base.search(topic, top_k=max_papers * 2)  # Get extra for filtering
        
        # Extract unique papers (by filename)
        seen_papers = set()
        top_papers = []
        for result in search_results:
            paper_name = result.chunk.file_name
            if paper_name not in seen_papers:
                seen_papers.add(paper_name)
                top_papers.append(paper_name)
                if len(top_papers) >= max_papers:
                    break
        
        # PHASE 1A: Use prompt template from reorganized module
        survey_prompt = get_literature_survey_template(topic, len(top_papers))
        
        response = self.ask(survey_prompt, temperature=0.4, max_context_chunks=max_papers)
        
        return {
            'content': response.content,
            'papers_found': len(top_papers),
            'papers_list': top_papers,
            'topics_covered': self._extract_physics_topics(response.content),
            'processing_time': response.processing_time
        }
    
    def research_brainstorm(self, current_work: str, research_direction: str = None) -> dict:
        """
        Brainstorm research ideas based on current work and literature.
        
        Args:
            current_work: Description of current research
            research_direction: Optional specific direction to explore
        
        Returns:
            Research suggestions with literature support
        """
        # PHASE 1A: Use prompt template from reorganized module
        prompt = get_research_brainstorm_template(current_work, research_direction)
        
        response = self.ask(prompt, temperature=0.5, max_context_chunks=8)
        
        return {
            'content': response.content,
            'sources_used': response.sources_used,
            'research_areas': self._extract_physics_topics(response.content)
        }

# Convenience function to create enhanced assistant
def create_enhanced_physics_assistant(knowledge_base: KnowledgeBase, anthropic_api_key: str, chat_config: dict = None):
    """Create an enhanced physics assistant with improved capabilities."""
    return EnhancedPhysicsAssistant(knowledge_base, anthropic_api_key, chat_config)

# Example usage and testing
def demo_enhanced_assistant():
    """Demonstrate the enhanced physics assistant capabilities."""
    print("🚀 ENHANCED PHYSICS ASSISTANT DEMO")
    print("=" * 50)
    
    try:
        import sys
        from pathlib import Path
        
        # Add project root to path for config import
        project_root = Path(__file__).parent.parent.parent
        sys.path.insert(0, str(project_root))
        
        from config import PipelineConfig
        from ..core import KnowledgeBase
        
        # Load configuration
        config = PipelineConfig()
        
        if not config.anthropic_api_key:
            print("❌ ANTHROPIC_API_KEY required for demo")
            return
        
        # Create knowledge base (simplified for demo)
        kb = KnowledgeBase()
        
        # Try to load existing cache or create empty KB
        if config.cache_file.exists():
            kb.load_from_file(config.cache_file)
        
        stats = kb.get_statistics()
        print(f"📚 Knowledge base: {stats['total_documents']} docs, {stats['total_chunks']} chunks")
        
        # Create enhanced assistant
        assistant = create_enhanced_physics_assistant(kb, config.anthropic_api_key)
        
        # Demo different capabilities
        print(f"\n🧪 Testing concept explanation...")
        concept_response = assistant.explain_concept("quantum entanglement", level="undergraduate")
        print(f"✅ Concept explained ({len(concept_response['content'])} chars)")
        
        if stats['total_documents'] > 0:
            print(f"\n🔍 Testing literature survey...")
            survey_response = assistant.literature_survey("quantum computing", max_papers=3)
            print(f"✅ Survey completed ({survey_response['papers_found']} papers)")
            
            print(f"\n💡 Testing research brainstorm...")
            brainstorm_response = assistant.research_brainstorm(
                "quantum error correction in superconducting qubits",
                "improving gate fidelities"
            )
            print(f"✅ Brainstorm completed")
        
        print(f"\n🎉 Enhanced assistant demo completed successfully!")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")

if __name__ == "__main__":
    demo_enhanced_assistant()