#!/usr/bin/env python3
"""
Enhanced Physics-Aware Assistant

This module provides an improved version of the literature assistant
with better physics understanding and more sophisticated prompting.

Location: src/chat/enhanced_physics_assistant.py
"""

# Since this is in src/chat/, we can use relative imports
from .literature_assistant import LiteratureAssistant
from ..core.knowledge_base import KnowledgeBase

from .literature_assistant import LiteratureAssistant
from ..core.knowledge_base import KnowledgeBase

class EnhancedPhysicsAssistant(LiteratureAssistant):
    """
    Enhanced literature assistant with improved physics understanding.
    
    This extends the base LiteratureAssistant with:
    - Better physics-specific system prompts
    - Enhanced context handling for physics concepts
    - Improved source citation formatting
    - Physics-aware conversation flow
    """
    
    def __init__(self, knowledge_base: KnowledgeBase, anthropic_api_key: str, chat_config: dict = None):
        """Initialize the enhanced physics assistant."""
        super().__init__(knowledge_base, anthropic_api_key, chat_config)
        
        # Override with enhanced physics system prompt
        self._setup_enhanced_physics_prompt()
    
    def _setup_enhanced_physics_prompt(self) -> None:
        """Set up enhanced system prompt with better physics understanding."""
        kb_stats = self.knowledge_base.get_statistics()
        
        system_prompt = f"""You are an expert theoretical physicist and research assistant with deep knowledge across all areas of physics. You have access to a comprehensive literature database containing {kb_stats.get('total_documents', 0)} physics papers and {kb_stats.get('total_chunks', 0)} content segments.

CORE PHYSICS EXPERTISE:
• Quantum mechanics, quantum field theory, and quantum information
• Condensed matter physics and many-body systems  
• High energy physics, particle physics, and cosmology
• Statistical mechanics and thermodynamics
• Electromagnetism and classical mechanics
• Atomic, molecular, and optical physics
• Biophysics and complex systems
• Mathematical physics and computational methods

LITERATURE DATABASE ACCESS:
Your knowledge base contains:
- Research papers from major physics journals
- Preprints and arxiv submissions  
- User's personal research work and drafts
- Conference proceedings and review articles
- Source types: {list(kb_stats.get('source_breakdown', {}).keys())}

RESPONSE GUIDELINES:

1. PHYSICS ACCURACY & RIGOR:
   - Use precise physics terminology and mathematical notation
   - Distinguish between theoretical predictions and experimental results
   - Acknowledge uncertainties and limitations in current understanding
   - Reference standard physics conventions (SI units, sign conventions, etc.)

2. LITERATURE INTEGRATION:
   - Always ground physics explanations in the available literature
   - Cite specific papers when making claims: [Literature: paper_name.pdf]
   - Cross-reference multiple sources when possible
   - Distinguish between established results and recent developments

3. EDUCATIONAL APPROACH:
   - Explain concepts at multiple levels (introductory to advanced)
   - Build understanding progressively from basic principles
   - Use analogies carefully, noting their limitations
   - Suggest further reading from the literature database

4. RESEARCH ASSISTANCE:
   - Help identify connections between different physics subfields
   - Suggest relevant experimental or theoretical approaches
   - Point out potential research directions and open questions
   - Assist with literature surveys and research planning

5. MATHEMATICAL CLARITY:
   - Include key equations when relevant to understanding
   - Explain the physical meaning of mathematical expressions
   - Note approximations and their validity ranges
   - Suggest computational approaches when appropriate

6. SOURCE CITATION FORMAT:
   - Research literature: [Literature: filename.pdf]
   - User's work: [Your work: filename.tex]
   - Current drafts: [Draft: filename]
   - When referencing multiple sources, list all relevant citations

7. CONVERSATION FLOW:
   - Ask clarifying questions about the specific physics context
   - Offer to elaborate on mathematical details or experimental aspects
   - Suggest related topics that might be of interest
   - Remember previous questions to build coherent discussions

RESPONSE STRUCTURE:
Start with a direct answer to the physics question, then provide:
- Relevant background from the literature
- Key physics principles involved
- Mathematical relationships (when appropriate)
- Experimental context or evidence
- Connections to broader physics topics
- Suggestions for further exploration

Always maintain scientific rigor while being accessible and helpful for advancing physics research and understanding."""

        self.chat.set_system_prompt(system_prompt)
    
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
            level: "introductory", "undergraduate", "graduate", or "research"
        
        Returns:
            Detailed explanation with literature context
        """
        question = f"""Please explain the physics concept of "{concept}" at the {level} level. 
        
        Include:
        1. Basic definition and physical principles
        2. Mathematical formulation (if appropriate for the level)
        3. Key experimental evidence or observations
        4. Applications and importance in physics
        5. Connections to other physics concepts
        6. Current research directions (if at graduate/research level)
        
        Please cite relevant literature from the knowledge base."""
        
        return self.ask_physics_question(question, context_level=level, include_math=(level in ["graduate", "research"]))
    
    def literature_survey(self, topic: str, max_papers: int = 10) -> dict:
        """
        Conduct a literature survey on a physics topic.
        
        Args:
            topic: Physics topic for the survey
            max_papers: Maximum number of papers to include
        
        Returns:
            Literature survey with paper summaries
        """
        # Search for relevant papers
        search_results = self.knowledge_base.search(topic, top_k=max_papers * 2)  # Get extra for filtering
        
        if not search_results:
            return {
                'content': f"No literature found for topic: {topic}",
                'papers_found': 0,
                'topics_covered': []
            }
        
        # Group by papers
        papers_found = {}
        for result in search_results:
            filename = result.chunk.file_name
            if filename not in papers_found:
                papers_found[filename] = []
            papers_found[filename].append(result)
        
        # Limit to max_papers
        top_papers = list(papers_found.keys())[:max_papers]
        
        # Create survey prompt
        survey_prompt = f"""Please provide a comprehensive literature survey on the topic: {topic}

        Based on the available literature, please:
        
        1. **Overview**: Summarize the current state of research in {topic}
        2. **Key Findings**: Highlight the most important results and discoveries
        3. **Methodologies**: Describe the main experimental or theoretical approaches used
        4. **Open Questions**: Identify unresolved issues and future research directions
        5. **Paper Summaries**: Briefly summarize the key contributions of each paper
        
        Focus on synthesis rather than just listing papers. Show how different works relate to each other and contribute to our understanding of {topic}.
        
        Papers available in the knowledge base: {len(top_papers)}"""
        
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
        prompt = f"""I'm working on: {current_work}
        
        {f"I'm particularly interested in exploring: {research_direction}" if research_direction else ""}
        
        Please help me brainstorm research directions by:
        
        1. **Literature Connections**: Find papers in the knowledge base that relate to my work
        2. **Research Gaps**: Identify potential gaps or unexplored areas
        3. **Methodological Suggestions**: Suggest experimental or theoretical approaches
        4. **Collaboration Opportunities**: Identify complementary research areas
        5. **Next Steps**: Propose specific next steps I could take
        
        Base your suggestions on the available literature and highlight where my work could make novel contributions."""
        
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