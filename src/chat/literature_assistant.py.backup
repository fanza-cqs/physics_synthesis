#!/usr/bin/env python3
"""
Literature-aware assistant for the Physics Literature Synthesis Pipeline.

Provides AI assistance with access to physics literature knowledge base.
Integrates semantic search with conversational AI for research support.
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .chat_interface import ChatInterface, ChatResponse
from ..core.knowledge_base import KnowledgeBase, SearchResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class LiteratureSearchContext:
    """Context from literature search for AI response."""
    search_results: List[SearchResult]
    formatted_context: str
    sources_used: List[str]
    total_chunks: int

class LiteratureAssistant:
    """
    Literature-aware AI assistant for physics research.
    
    Combines conversational AI with semantic search over physics literature
    to provide informed, source-backed responses to research questions.
    """
    
    def __init__(self, 
                 knowledge_base: KnowledgeBase,
                 anthropic_api_key: str,
                 chat_config: Dict[str, Any] = None):
        """
        Initialize the literature assistant.
        
        Args:
            knowledge_base: Physics literature knowledge base
            anthropic_api_key: Anthropic API key
            chat_config: Configuration for chat interface
        """
        self.knowledge_base = knowledge_base
        
        # Initialize chat interface
        chat_config = chat_config or {}
        self.chat = ChatInterface(
            anthropic_api_key=anthropic_api_key,
            model=chat_config.get('model', 'claude-3-5-sonnet-20241022'),
            max_tokens=chat_config.get('max_tokens', 4000),
            max_conversation_length=chat_config.get('max_history', 20)
        )
        
        # Configuration
        self.default_temperature = chat_config.get('default_temperature', 0.3)
        self.max_context_chunks = chat_config.get('max_context_chunks', 8)
        
        # Set up system prompt
        self._setup_system_prompt()
        
        # Track sources used in responses
        self.sources_cache: Dict[int, List[str]] = {}
        
        logger.info("Literature assistant initialized")
    
    def _setup_system_prompt(self) -> None:
        """Set up the system prompt for literature-aware responses."""
        kb_stats = self.knowledge_base.get_statistics()
        
        system_prompt = f"""You are an expert theoretical physicist assistant with access to a comprehensive literature database.

KNOWLEDGE BASE INFORMATION:
- Total papers: {kb_stats.get('total_documents', 0)}
- Total content chunks: {kb_stats.get('total_chunks', 0)}
- Source types: {list(kb_stats.get('source_breakdown', {}).keys())}
- Embedding model: {kb_stats.get('embedding_model', 'unknown')}

YOUR CAPABILITIES:
- Answer physics questions using relevant literature from the knowledge base
- Provide detailed explanations grounded in research papers
- Cite specific sources when making claims
- Help with research direction and literature synthesis
- Reference user's previous work when relevant
- Maintain scientific rigor while being accessible

RESPONSE GUIDELINES:
- Always ground responses in available literature when possible
- Cite sources as [Source: filename] when referencing specific content
- Distinguish between claims from literature vs. your reasoning
- Be precise about uncertainty when information isn't available
- Ask clarifying questions for ambiguous queries
- Maintain scientific accuracy and proper physics terminology

CITATION FORMAT:
- Literature papers: [Literature: paper_name.pdf]
- User's previous work: [Your work: paper_name.tex]
- Current drafts: [Draft: filename]

Remember to provide source-backed, scientifically accurate responses that help advance physics research."""

        self.chat.set_system_prompt(system_prompt)
    
    def ask(self, 
            question: str,
            temperature: float = None,
            max_context_chunks: int = None,
            include_literature: bool = True) -> ChatResponse:
        """
        Ask a question to the literature-aware assistant.
        
        Args:
            question: Research question or query
            temperature: AI creativity level (uses default if None)
            max_context_chunks: Max literature chunks to include
            include_literature: Whether to search literature
        
        Returns:
            ChatResponse with answer and metadata
        """
        start_time = time.time()
        
        # Use defaults if not specified
        if temperature is None:
            temperature = self.default_temperature
        if max_context_chunks is None:
            max_context_chunks = self.max_context_chunks
        
        logger.info(f"Processing question: {question[:50]}...")
        
        # Search literature for relevant context
        literature_context = None
        sources_used = []
        
        if include_literature:
            literature_context = self._search_literature_context(
                question, max_context_chunks
            )
            sources_used = literature_context.sources_used
        
        # Prepare message for AI
        if literature_context and literature_context.formatted_context:
            enhanced_question = f"""QUESTION: {question}

RELEVANT LITERATURE CONTEXT:
{literature_context.formatted_context}

Please answer the question using the provided literature context when relevant. 
Cite sources appropriately and distinguish between information from the literature 
versus your own analysis."""
        else:
            enhanced_question = question
        
        # Get AI response
        try:
            response_text = self.chat.send_message(
                enhanced_question, 
                temperature=temperature
            )
            
            processing_time = time.time() - start_time
            
            # Cache sources for this response
            response_index = len(self.chat.conversation_history) - 1
            self.sources_cache[response_index] = sources_used
            
            # Create response object
            response = ChatResponse(
                content=response_text,
                sources_used=sources_used,
                processing_time=processing_time,
                context_chunks_used=len(sources_used) if literature_context else 0
            )
            
            logger.info(f"Question answered in {processing_time:.2f}s with {len(sources_used)} sources")
            return response
            
        except Exception as e:
            logger.error(f"Error processing question: {e}")
            raise
    
    def _search_literature_context(self, 
                                  question: str, 
                                  max_chunks: int) -> LiteratureSearchContext:
        """
        Search literature and format context for AI.
        
        Args:
            question: User's question
            max_chunks: Maximum chunks to return
        
        Returns:
            LiteratureSearchContext with formatted context
        """
        # Get conversation context for better search
        conversation_context = self.chat.get_context_for_search()
        
        # Search knowledge base
        search_results = self.knowledge_base.search_with_context(
            query=question,
            conversation_context=conversation_context,
            top_k=max_chunks
        )
        
        if not search_results:
            return LiteratureSearchContext(
                search_results=[],
                formatted_context="",
                sources_used=[],
                total_chunks=0
            )
        
        # Format context for AI
        context_parts = []
        sources_used = []
        
        for result in search_results:
            chunk = result.chunk
            similarity = result.similarity_score
            
            # Determine source label
            source_type = chunk.source_type
            if source_type == "literature":
                source_label = f"Literature: {chunk.file_name}"
            elif source_type == "your_work":
                source_label = f"Your work: {chunk.file_name}"
            elif source_type == "current_drafts":
                source_label = f"Draft: {chunk.file_name}"
            else:
                source_label = f"Source: {chunk.file_name}"
            
            # Add to context
            context_parts.append(
                f"[{source_label}] (relevance: {similarity:.3f})\n"
                f"{chunk.text[:600]}...\n"
            )
            
            # Track source
            if chunk.file_name not in sources_used:
                sources_used.append(chunk.file_name)
        
        formatted_context = "\n".join(context_parts)
        
        logger.debug(f"Found {len(search_results)} relevant chunks from {len(sources_used)} sources")
        
        return LiteratureSearchContext(
            search_results=search_results,
            formatted_context=formatted_context,
            sources_used=sources_used,
            total_chunks=len(search_results)
        )
    
    def synthesize_literature(self, 
                             topic: str,
                             focus_areas: List[str] = None,
                             max_chunks: int = 15) -> ChatResponse:
        """
        Generate a literature synthesis on a specific topic.
        
        Args:
            topic: Research topic to synthesize
            focus_areas: Specific aspects to focus on
            max_chunks: Maximum literature chunks to consider
        
        Returns:
            ChatResponse with synthesis
        """
        # Create synthesis prompt
        focus_text = ""
        if focus_areas:
            focus_text = f"\n\nPlease focus specifically on: {', '.join(focus_areas)}"
        
        synthesis_prompt = f"""Please provide a comprehensive literature synthesis on the topic: {topic}

I would like you to:
1. Summarize the current state of research in this area
2. Identify key findings and consensus points
3. Highlight any controversies or open questions
4. Suggest potential future research directions
5. Cite all sources appropriately{focus_text}

Please organize your response clearly and provide a thorough analysis based on the available literature."""

        return self.ask(
            synthesis_prompt,
            temperature=0.4,  # Slightly higher for synthesis creativity
            max_context_chunks=max_chunks
        )
    
    def help_with_writing(self, 
                         writing_task: str,
                         current_draft: str = "",
                         style_preferences: str = "") -> ChatResponse:
        """
        Help with academic writing tasks.
        
        Args:
            writing_task: Description of writing task
            current_draft: Current draft text (if any)
            style_preferences: Writing style preferences
        
        Returns:
            ChatResponse with writing assistance
        """
        writing_prompt = f"""I need help with the following writing task: {writing_task}"""
        
        if current_draft:
            writing_prompt += f"\n\nHere is my current draft:\n{current_draft}"
        
        if style_preferences:
            writing_prompt += f"\n\nStyle preferences: {style_preferences}"
        
        writing_prompt += """\n\nPlease provide specific suggestions for improvement, 
drawing on relevant literature when appropriate. Focus on:
- Scientific accuracy and clarity
- Proper structure and flow
- Appropriate citations and references
- Clear physics explanations"""
        
        return self.ask(
            writing_prompt,
            temperature=0.5,  # Higher creativity for writing
            max_context_chunks=self.max_context_chunks
        )
    
    def get_sources_from_last_response(self) -> List[str]:
        """
        Get sources used in the last assistant response.
        
        Returns:
            List of source filenames
        """
        if not self.chat.conversation_history:
            return []
        
        # Get index of last assistant message
        last_assistant_index = None
        for i in reversed(range(len(self.chat.conversation_history))):
            if self.chat.conversation_history[i].role == "assistant":
                last_assistant_index = i
                break
        
        if last_assistant_index is not None and last_assistant_index in self.sources_cache:
            return self.sources_cache[last_assistant_index]
        
        return []
    
    def get_conversation_summary(self) -> str:
        """Get summary of current conversation."""
        return self.chat.get_conversation_summary()
    
    def clear_conversation(self) -> None:
        """Clear conversation history and source cache."""
        self.chat.clear_conversation()
        self.sources_cache.clear()
        logger.info("Conversation and source cache cleared")
    
    def export_conversation_with_sources(self) -> str:
        """
        Export conversation in markdown format with source information.
        
        Returns:
            Formatted conversation with sources
        """
        if not self.chat.conversation_history:
            return "No conversation to export."
        
        lines = ["# Physics Literature Conversation\n\n"]
        
        exchange_num = 1
        for i in range(0, len(self.chat.conversation_history), 2):
            if i + 1 < len(self.chat.conversation_history):
                user_msg = self.chat.conversation_history[i]
                assistant_msg = self.chat.conversation_history[i + 1]
                
                lines.append(f"## Exchange {exchange_num}\n\n")
                lines.append(f"**Question:** {user_msg.content}\n\n")
                lines.append(f"**Answer:** {assistant_msg.content}\n\n")
                
                # Add sources if available
                if (i + 1) in self.sources_cache and self.sources_cache[i + 1]:
                    lines.append(f"**Sources:** {', '.join(self.sources_cache[i + 1])}\n\n")
                
                lines.append("---\n\n")
                exchange_num += 1
        
        return "".join(lines)
    
    def get_knowledge_base_stats(self) -> Dict[str, Any]:
        """Get statistics about the knowledge base."""
        return self.knowledge_base.get_statistics()
    
    def search_knowledge_base(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Direct search of the knowledge base.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of search results
        """
        return self.knowledge_base.search(query, top_k)
    
    def list_available_papers(self) -> List[Dict[str, Any]]:
        """
        List all papers available in the knowledge base.
        
        Returns:
            List of paper information dictionaries
        """
        return self.knowledge_base.list_documents()