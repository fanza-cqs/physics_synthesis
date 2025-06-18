#!/usr/bin/env python3
"""
Literature-aware assistant for the Physics Literature Synthesis Pipeline.

Provides AI assistance with access to physics literature knowledge base.
Integrates semantic search with conversational AI for research support.

PHASE 1A: Updated to use reorganized prompt structure while maintaining functionality.
PHASE 1B: Enhanced prompt engineering will be added next.
"""

import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .chat_interface import ChatInterface, ChatResponse
from ..core.knowledge_base import KnowledgeBase, SearchResult
from ..utils.logging_config import get_logger

# PHASE 1A: Import prompts from new reorganized structure
from .prompts import get_basic_literature_prompt

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
    
    PHASE 1A CHANGES:
    - Updated to use prompts from reorganized prompts module
    - Maintains exact same functionality as before restructuring
    - Prepared for Phase 1B enhanced prompt engineering
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
        
        # PHASE 1A: Set up system prompt using reorganized prompt structure
        self._setup_system_prompt()
        
        # Track sources used in responses
        self.sources_cache: Dict[int, List[str]] = {}
        
        logger.info("Literature assistant initialized")
    
    def _setup_system_prompt(self) -> None:
        """
        Set up the system prompt for literature-aware responses.
        
        PHASE 1A: Now uses prompt from reorganized prompts module.
        PHASE 1B: Will be enhanced with modular prompt engineering.
        """
        kb_stats = self.knowledge_base.get_statistics()
        
        # PHASE 1A: Use prompt from reorganized module instead of hardcoded
        system_prompt = get_basic_literature_prompt(kb_stats)
        
        self.chat.set_system_prompt(system_prompt)
        logger.debug("System prompt configured using reorganized prompt structure")
    
    def ask(self, 
            question: str,
            temperature: float = None,
            max_context_chunks: int = None,
            include_literature: bool = True) -> ChatResponse:
        """
        Ask a question to the literature-aware assistant.
        
        Args:
            question: User's question
            temperature: Sampling temperature (defaults to configured value)
            max_context_chunks: Max context chunks to include (defaults to configured)
            include_literature: Whether to search literature for context
        
        Returns:
            Chat response with literature context
        """
        start_time = time.time()
        
        # Use defaults if not specified
        if temperature is None:
            temperature = self.default_temperature
        if max_context_chunks is None:
            max_context_chunks = self.max_context_chunks
        
        # Search for relevant literature context
        context = self._get_literature_context(question, max_context_chunks) if include_literature else None
        
        # Format the question with context
        formatted_question = self._format_question_with_context(question, context)
        
        # Get AI response
        response_content = self.chat.send_message(
            formatted_question, 
            temperature=temperature,
            include_history=True
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare response
        sources_used = context.sources_used if context else []
        context_chunks_used = context.total_chunks if context else 0
        
        # Cache sources for this response
        response_hash = hash(response_content)
        self.sources_cache[response_hash] = sources_used
        
        response = ChatResponse(
            content=response_content,
            sources_used=sources_used,
            processing_time=processing_time,
            context_chunks_used=context_chunks_used
        )
        
        logger.info(f"Question answered in {processing_time:.2f}s with {context_chunks_used} context chunks")
        return response
    
    def _get_literature_context(self, question: str, max_chunks: int) -> Optional[LiteratureSearchContext]:
        """
        Search knowledge base for relevant literature context.
        
        Args:
            question: User's question
            max_chunks: Maximum number of chunks to retrieve
        
        Returns:
            Literature context or None if no relevant content found
        """
        try:
            # Search the knowledge base
            search_results = self.knowledge_base.search(question, top_k=max_chunks)
            
            if not search_results:
                logger.debug("No relevant literature found for question")
                return None
            
            # Format context for AI
            formatted_context = self._format_search_results(search_results)
            
            # Extract source information
            sources_used = []
            for result in search_results:
                source_name = result.chunk.file_name
                if source_name not in sources_used:
                    sources_used.append(source_name)
            
            context = LiteratureSearchContext(
                search_results=search_results,
                formatted_context=formatted_context,
                sources_used=sources_used,
                total_chunks=len(search_results)
            )
            
            logger.debug(f"Retrieved {len(search_results)} chunks from {len(sources_used)} sources")
            return context
            
        except Exception as e:
            logger.error(f"Error retrieving literature context: {e}")
            return None
    
    def _format_search_results(self, search_results: List[SearchResult]) -> str:
        """
        Format search results for inclusion in AI prompt.
        
        Args:
            search_results: List of search results from knowledge base
        
        Returns:
            Formatted context string
        """
        if not search_results:
            return ""
        
        context_parts = ["RELEVANT LITERATURE CONTEXT:"]
        
        for i, result in enumerate(search_results, 1):
            chunk = result.chunk
            similarity = result.similarity_score
            
            # Format individual chunk
            chunk_text = f"""
--- Source {i}: {chunk.file_name} (Similarity: {similarity:.3f}) ---
Source Type: {chunk.source_type}
Chunk {chunk.chunk_index + 1} of {chunk.total_chunks}

{chunk.text}

---
"""
            context_parts.append(chunk_text)
        
        return "\n".join(context_parts)
    
    def _format_question_with_context(self, question: str, context: Optional[LiteratureSearchContext]) -> str:
        """
        Format user question with literature context for AI.
        
        Args:
            question: Original user question
            context: Literature context (if available)
        
        Returns:
            Formatted question with context
        """
        if not context:
            return question
        
        formatted_question = f"""{context.formatted_context}

USER QUESTION: {question}

Please answer the question using the relevant literature context provided above. Follow the response guidelines in your system prompt for citations and scientific accuracy."""
        
        return formatted_question
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the current conversation history.
        
        Returns:
            List of conversation messages with metadata
        """
        history = []
        for msg in self.chat.conversation_history:
            # Try to get sources for this message if it was an assistant response
            sources = []
            if msg.role == 'assistant':
                msg_hash = hash(msg.content)
                sources = self.sources_cache.get(msg_hash, [])
            
            history.append({
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp,
                'sources': sources
            })
        
        return history
    
    def clear_conversation(self) -> None:
        """Clear the conversation history and sources cache."""
        self.chat.conversation_history = []
        self.sources_cache = {}
        logger.info("Conversation history cleared")
    
    def get_knowledge_base_info(self) -> Dict[str, Any]:
        """
        Get information about the current knowledge base.
        
        Returns:
            Knowledge base statistics and information
        """
        return self.knowledge_base.get_statistics()