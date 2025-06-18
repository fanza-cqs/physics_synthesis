#!/usr/bin/env python3
"""
Simple word-based chunking strategy.

This strategy implements the original chunking approach from the base embeddings
system - splitting text by word count with simple overlap.

Phase 1B: Backward compatibility strategy that maintains existing behavior.
"""

from typing import List, Dict, Any
from .base_strategy import BaseChunkingStrategy, ChunkingConfig, ChunkMetadata

class SimpleChunkingStrategy(BaseChunkingStrategy):
    """
    Simple word-based chunking strategy.
    
    This strategy splits text into chunks based on word count with fixed overlap,
    maintaining the exact behavior of the original embeddings system.
    
    Use this strategy for:
    - Backward compatibility with existing embeddings
    - Simple, predictable chunking behavior
    - When document structure is not important
    """
    
    def chunk_text(self, text: str, document_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into chunks using simple word-based approach.
        
        This is identical to the original EmbeddingsManager.chunk_text() method
        to ensure backward compatibility.
        
        Args:
            text: Input text to chunk
            document_metadata: Optional document metadata (unused in simple strategy)
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text.strip():
            return []
        
        words = text.split()
        if len(words) <= self.config.chunk_size:
            # Single chunk case
            metadata = ChunkMetadata(
                chunk_index=0,
                total_chunks=1,
                section_type=self._detect_section_type(text, 0, 1),
                has_equations=self._detect_equations(text),
                has_citations=self._detect_citations(text),
                sentence_boundaries=self._find_sentence_boundaries(text)
            )
            
            return [{
                'text': text,
                'metadata': metadata
            }]
        
        chunks = []
        start_idx = 0
        chunk_index = 0
        
        # First pass: determine total number of chunks
        total_chunks = self._calculate_total_chunks(len(words))
        
        while start_idx < len(words):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.config.chunk_size, len(words))
            
            # Create chunk from words
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            if chunk_text.strip():
                # Create metadata for this chunk
                metadata = ChunkMetadata(
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    section_type=self._detect_section_type(chunk_text, chunk_index, total_chunks),
                    has_equations=self._detect_equations(chunk_text),
                    has_citations=self._detect_citations(chunk_text),
                    sentence_boundaries=self._find_sentence_boundaries(chunk_text)
                )
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': metadata
                })
                
                chunk_index += 1
            
            # Move start index, accounting for overlap
            if end_idx >= len(words):
                break
            start_idx = end_idx - self.config.chunk_overlap
        
        return chunks
    
    def _calculate_total_chunks(self, total_words: int) -> int:
        """
        Calculate the total number of chunks that will be created.
        
        Args:
            total_words: Total number of words in the document
        
        Returns:
            Expected number of chunks
        """
        if total_words <= self.config.chunk_size:
            return 1
        
        # Calculate based on the sliding window approach
        effective_chunk_size = self.config.chunk_size - self.config.chunk_overlap
        remaining_words = total_words - self.config.chunk_size
        additional_chunks = (remaining_words + effective_chunk_size - 1) // effective_chunk_size
        
        return 1 + additional_chunks