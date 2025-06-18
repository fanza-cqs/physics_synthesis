#!/usr/bin/env python3
"""
Base chunking strategy interface for the Physics Literature Synthesis Pipeline.

Defines the interface for different text chunking strategies that can be
plugged into the enhanced embeddings system.

Phase 1B: Enhanced chunking strategies for better document processing.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class ChunkingConfig:
    """Configuration for chunking strategies."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    preserve_sentences: bool = True
    preserve_equations: bool = True
    section_awareness: bool = True
    min_chunk_size: int = 100
    max_chunk_size: int = 2000

@dataclass
class ChunkMetadata:
    """Metadata for a text chunk."""
    chunk_index: int
    total_chunks: int
    section_type: Optional[str] = None  # e.g., "abstract", "introduction", "methods"
    has_equations: bool = False
    has_citations: bool = False
    sentence_boundaries: List[int] = None  # Character positions of sentence boundaries
    confidence_score: float = 1.0  # Confidence in chunk boundary quality

class BaseChunkingStrategy(ABC):
    """
    Abstract base class for text chunking strategies.
    
    All chunking strategies must implement the chunk_text method and
    provide configuration options for their specific approach.
    """
    
    def __init__(self, config: ChunkingConfig = None):
        """
        Initialize the chunking strategy.
        
        Args:
            config: Configuration for the chunking strategy
        """
        self.config = config or ChunkingConfig()
        self.name = self.__class__.__name__
    
    @abstractmethod
    def chunk_text(self, text: str, document_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks according to the strategy.
        
        Args:
            text: Input text to chunk
            document_metadata: Optional metadata about the document (title, authors, etc.)
        
        Returns:
            List of dictionaries containing:
            - 'text': The chunk text
            - 'metadata': ChunkMetadata object with chunk information
        """
        pass
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about this chunking strategy.
        
        Returns:
            Dictionary with strategy name, description, and configuration
        """
        return {
            'name': self.name,
            'description': self.__doc__.strip() if self.__doc__ else "No description available",
            'config': self.config.__dict__
        }
    
    def _detect_section_type(self, text: str, chunk_index: int, total_chunks: int) -> Optional[str]:
        """
        Detect the section type of a text chunk.
        
        Args:
            text: The chunk text
            chunk_index: Index of this chunk
            total_chunks: Total number of chunks in document
        
        Returns:
            Section type string or None if not detected
        """
        text_lower = text.lower()
        
        # Check for common academic paper sections
        if chunk_index == 0:
            if 'abstract' in text_lower[:200]:
                return 'abstract'
        
        # Look for section headers
        if 'introduction' in text_lower[:100]:
            return 'introduction'
        elif any(word in text_lower[:100] for word in ['method', 'experimental', 'procedure']):
            return 'methods'
        elif any(word in text_lower[:100] for word in ['result', 'finding', 'observation']):
            return 'results'
        elif any(word in text_lower[:100] for word in ['discussion', 'analysis', 'interpretation']):
            return 'discussion'
        elif any(word in text_lower[:100] for word in ['conclusion', 'summary', 'closing']):
            return 'conclusion'
        elif 'reference' in text_lower[:100] or 'bibliography' in text_lower[:100]:
            return 'references'
        
        # Default classification based on position
        if chunk_index < total_chunks * 0.2:
            return 'introduction'
        elif chunk_index > total_chunks * 0.8:
            return 'conclusion'
        else:
            return 'body'
    
    def _detect_equations(self, text: str) -> bool:
        """
        Detect if text contains mathematical equations.
        
        Args:
            text: Text to analyze
        
        Returns:
            True if equations are likely present
        """
        # Look for LaTeX math delimiters
        latex_indicators = ['$$', '$', '\\begin{equation}', '\\begin{align}', '\\[', '\\]']
        if any(indicator in text for indicator in latex_indicators):
            return True
        
        # Look for mathematical symbols and patterns
        math_indicators = ['=', '≡', '≈', '∝', '∫', '∂', '∇', 'α', 'β', 'γ', 'δ', 'θ', 'λ', 'μ', 'π', 'σ', 'φ', 'ψ', 'ω']
        symbol_count = sum(1 for indicator in math_indicators if indicator in text)
        
        # If we have multiple math symbols, likely contains equations
        return symbol_count >= 3
    
    def _detect_citations(self, text: str) -> bool:
        """
        Detect if text contains academic citations.
        
        Args:
            text: Text to analyze
        
        Returns:
            True if citations are likely present
        """
        # Look for common citation patterns
        import re
        
        # Pattern for citations like [1], [Smith et al., 2020], (Author, Year)
        citation_patterns = [
            r'\[\d+\]',  # [1], [23]
            r'\[[\w\s,]+\d{4}\]',  # [Smith et al., 2020]
            r'\([\w\s,]+\d{4}\)',  # (Smith et al., 2020)
            r'\b\w+\s+et\s+al\.',  # Author et al.
        ]
        
        for pattern in citation_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _find_sentence_boundaries(self, text: str) -> List[int]:
        """
        Find sentence boundaries in text.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of character positions where sentences end
        """
        import re
        
        # Simple sentence boundary detection
        # Look for periods, exclamation marks, question marks followed by whitespace
        sentence_endings = re.finditer(r'[.!?]+\s+', text)
        boundaries = [match.end() for match in sentence_endings]
        
        # Add the end of text as a boundary
        if boundaries and boundaries[-1] != len(text):
            boundaries.append(len(text))
        
        return boundaries