#!/usr/bin/env python3
"""
Context-aware chunking strategy for scientific documents.

This strategy improves upon simple word-based chunking by:
- Respecting sentence boundaries
- Preserving mathematical equations
- Being aware of document structure
- Smart overlap at natural breakpoints

Phase 1B: Enhanced chunking for better context preservation.
"""

import re
from typing import List, Dict, Any, Tuple
from .base_strategy import BaseChunkingStrategy, ChunkingConfig, ChunkMetadata

class ContextAwareChunkingStrategy(BaseChunkingStrategy):
    """
    Context-aware chunking strategy for scientific documents.
    
    This strategy creates chunks that respect document structure and maintain
    semantic coherence by:
    - Breaking at sentence boundaries when possible
    - Keeping mathematical equations intact
    - Preserving paragraph structure
    - Creating smart overlaps at natural breakpoints
    
    Use this strategy for:
    - Better semantic coherence in chunks
    - Preservation of mathematical content
    - Improved retrieval quality
    - Scientific document processing
    """
    
    def chunk_text(self, text: str, document_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Split text into context-aware chunks.
        
        Args:
            text: Input text to chunk
            document_metadata: Optional document metadata for better processing
        
        Returns:
            List of chunk dictionaries with text and metadata
        """
        if not text.strip():
            return []
        
        # Preprocess text to identify structure
        processed_text = self._preprocess_text(text)
        
        # Find sentence boundaries
        sentence_boundaries = self._find_enhanced_sentence_boundaries(processed_text)
        
        # Find equation boundaries
        equation_boundaries = self._find_equation_boundaries(processed_text)
        
        # Create chunks respecting boundaries
        chunks = self._create_smart_chunks(
            processed_text, 
            sentence_boundaries, 
            equation_boundaries
        )
        
        return chunks
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text to normalize whitespace and handle special cases.
        
        Args:
            text: Input text
        
        Returns:
            Preprocessed text
        """
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Preserve equation spacing
        text = re.sub(r'\$\s+', '$', text)
        text = re.sub(r'\s+\$', '$', text)
        
        # Normalize line breaks around equations
        text = re.sub(r'\n\s*\$\$', '\n$$', text)
        text = re.sub(r'\$\$\s*\n', '$$\n', text)
        
        return text.strip()
    
    def _find_enhanced_sentence_boundaries(self, text: str) -> List[int]:
        """
        Find sentence boundaries with better handling of scientific text.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of character positions where sentences end
        """
        boundaries = []
        
        # Pattern for sentence endings, considering scientific text patterns
        # Avoid breaking on abbreviations common in scientific text
        abbreviations = {
            'Dr.', 'Prof.', 'et al.', 'i.e.', 'e.g.', 'vs.', 'cf.', 'Fig.', 
            'Eq.', 'Ref.', 'Sec.', 'Ch.', 'Vol.', 'No.', 'pp.', 'eds.'
        }
        
        # Find potential sentence endings
        sentence_pattern = r'[.!?]+\s+'
        for match in re.finditer(sentence_pattern, text):
            start_pos = match.start()
            end_pos = match.end()
            
            # Check if this is likely a real sentence boundary
            if self._is_real_sentence_boundary(text, start_pos, abbreviations):
                boundaries.append(end_pos)
        
        # Add the end of text
        if not boundaries or boundaries[-1] != len(text):
            boundaries.append(len(text))
        
        return boundaries
    
    def _is_real_sentence_boundary(self, text: str, pos: int, abbreviations: set) -> bool:
        """
        Determine if a potential sentence boundary is real or part of an abbreviation.
        
        Args:
            text: Full text
            pos: Position of the potential boundary
            abbreviations: Set of known abbreviations
        
        Returns:
            True if this is likely a real sentence boundary
        """
        # Look backwards to see if this might be an abbreviation
        start = max(0, pos - 20)
        before_context = text[start:pos + 1]
        
        # Check against known abbreviations
        for abbrev in abbreviations:
            if before_context.endswith(abbrev):
                return False
        
        # Check if it's a decimal number (e.g., "3.14")
        if re.search(r'\d\.\s*$', before_context):
            # Look ahead to see if next character is a digit
            if pos + 1 < len(text) and text[pos + 1].isdigit():
                return False
        
        return True
    
    def _find_equation_boundaries(self, text: str) -> List[Tuple[int, int]]:
        """
        Find the boundaries of mathematical equations in the text.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of (start, end) tuples for equation boundaries
        """
        boundaries = []
        
        # Find LaTeX-style equations
        equation_patterns = [
            (r'\$\$.*?\$\$', re.DOTALL),  # Display equations
            (r'\$.*?\$', 0),              # Inline equations
            (r'\\begin\{equation\}.*?\\end\{equation\}', re.DOTALL),
            (r'\\begin\{align\}.*?\\end\{align\}', re.DOTALL),
            (r'\\begin\{eqnarray\}.*?\\end\{eqnarray\}', re.DOTALL),
            (r'\\begin\{gather\}.*?\\end\{gather\}', re.DOTALL),
            (r'\\begin\{multline\}.*?\\end\{multline\}', re.DOTALL),
            (r'\\begin\{flalign\}.*?\\end\{flalign\}', re.DOTALL),
            (r'\\begin\{alignat\}.*?\\end\{alignat\}', re.DOTALL),
            (r'\\\[.*?\\\]', re.DOTALL),  # \[ \] equations
        ]
        
        for pattern, flags in equation_patterns:
            for match in re.finditer(pattern, text, flags):
                boundaries.append((match.start(), match.end()))
        
        # Sort by start position and merge overlapping boundaries
        boundaries.sort()
        merged_boundaries = []
        
        for start, end in boundaries:
            if merged_boundaries and start <= merged_boundaries[-1][1]:
                # Overlapping or adjacent - extend the previous boundary
                merged_boundaries[-1] = (merged_boundaries[-1][0], max(end, merged_boundaries[-1][1]))
            else:
                merged_boundaries.append((start, end))
        
        return merged_boundaries
    
    def _create_smart_chunks(self, 
                           text: str, 
                           sentence_boundaries: List[int], 
                           equation_boundaries: List[Tuple[int, int]]) -> List[Dict[str, Any]]:
        """
        Create chunks that respect sentence and equation boundaries.
        
        Args:
            text: Text to chunk
            sentence_boundaries: List of sentence boundary positions
            equation_boundaries: List of equation boundary tuples
        
        Returns:
            List of chunk dictionaries
        """
        chunks = []
        text_length = len(text)
        current_pos = 0
        chunk_index = 0
        
        # Estimate total chunks for metadata
        estimated_chunks = max(1, text_length // (self.config.chunk_size * 4))  # Rough estimate
        
        while current_pos < text_length:
            # Find the best ending position for this chunk
            target_end = min(current_pos + self.config.chunk_size * 6, text_length)  # Use character-based target
            
            # Find the best boundary near the target end
            chunk_end = self._find_best_chunk_boundary(
                text, current_pos, target_end, sentence_boundaries, equation_boundaries
            )
            
            # Extract chunk text
            chunk_text = text[current_pos:chunk_end].strip()
            
            if chunk_text:
                # Create metadata
                metadata = ChunkMetadata(
                    chunk_index=chunk_index,
                    total_chunks=estimated_chunks,  # Will be updated after all chunks are created
                    section_type=self._detect_section_type(chunk_text, chunk_index, estimated_chunks),
                    has_equations=self._detect_equations(chunk_text),
                    has_citations=self._detect_citations(chunk_text),
                    sentence_boundaries=self._find_sentence_boundaries(chunk_text),
                    confidence_score=self._calculate_chunk_confidence(chunk_text, current_pos, chunk_end)
                )
                
                chunks.append({
                    'text': chunk_text,
                    'metadata': metadata
                })
                
                chunk_index += 1
            
            # Calculate next starting position with smart overlap
            next_start = self._calculate_smart_overlap(
                text, current_pos, chunk_end, sentence_boundaries
            )
            
            if next_start <= current_pos:
                # Prevent infinite loop
                next_start = current_pos + 1
                
            current_pos = next_start
        
        # Update total chunks count in all metadata
        actual_total = len(chunks)
        for chunk in chunks:
            chunk['metadata'].total_chunks = actual_total
        
        return chunks
    
    def _find_best_chunk_boundary(self, 
                                text: str, 
                                start: int, 
                                target_end: int, 
                                sentence_boundaries: List[int], 
                                equation_boundaries: List[Tuple[int, int]]) -> int:
        """
        Find the best position to end a chunk near the target position.
        
        Args:
            text: Full text
            start: Start position of current chunk
            target_end: Target end position
            sentence_boundaries: List of sentence boundaries
            equation_boundaries: List of equation boundaries
        
        Returns:
            Best end position for the chunk
        """
        min_chunk = max(start + self.config.min_chunk_size, start + 100)
        max_chunk = min(start + self.config.max_chunk_size, len(text))
        
        # Ensure we don't make chunks too small or too large
        target_end = max(min_chunk, min(target_end, max_chunk))
        
        # Check if we're inside an equation - if so, extend past it
        for eq_start, eq_end in equation_boundaries:
            if start < eq_end and target_end > eq_start:
                # We overlap with an equation - extend past it if reasonable
                if eq_end <= max_chunk:
                    target_end = max(target_end, eq_end)
        
        # Find the best sentence boundary near the target
        best_boundary = target_end
        min_distance = float('inf')
        
        for boundary in sentence_boundaries:
            if min_chunk <= boundary <= max_chunk:
                distance = abs(boundary - target_end)
                if distance < min_distance:
                    min_distance = distance
                    best_boundary = boundary
        
        # Don't use a boundary that's too far from our target
        if min_distance > self.config.chunk_size // 2:
            return target_end
        
        return best_boundary
    
    def _calculate_smart_overlap(self, 
                               text: str, 
                               current_start: int, 
                               current_end: int, 
                               sentence_boundaries: List[int]) -> int:
        """
        Calculate smart overlap position for the next chunk.
        
        Args:
            text: Full text
            current_start: Start of current chunk
            current_end: End of current chunk
            sentence_boundaries: List of sentence boundaries
        
        Returns:
            Start position for next chunk
        """
        chunk_length = current_end - current_start
        
        # Calculate target overlap
        target_overlap = min(self.config.chunk_overlap * 6, chunk_length // 3)  # Character-based overlap
        target_start = current_end - target_overlap
        
        # Find a good sentence boundary for overlap
        best_start = target_start
        
        for boundary in sentence_boundaries:
            if current_start < boundary < current_end:
                # This boundary is within our current chunk
                if abs(boundary - target_start) < target_overlap // 2:
                    best_start = boundary
                    break
        
        return max(current_start + 1, best_start)
    
    def _calculate_chunk_confidence(self, chunk_text: str, start_pos: int, end_pos: int) -> float:
        """
        Calculate confidence score for chunk boundary quality.
        
        Args:
            chunk_text: The chunk text
            start_pos: Start position in original text
            end_pos: End position in original text
        
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 1.0
        
        # Penalize chunks that are too short or too long
        chunk_length = len(chunk_text.split())
        if chunk_length < self.config.min_chunk_size // 10:
            confidence *= 0.5
        elif chunk_length > self.config.max_chunk_size // 5:
            confidence *= 0.8
        
        # Bonus for ending at sentence boundaries
        if chunk_text.rstrip().endswith(('.', '!', '?')):
            confidence *= 1.1
        
        # Bonus for starting with capital letter (sentence start)
        if chunk_text.lstrip() and chunk_text.lstrip()[0].isupper():
            confidence *= 1.05
        
        # Penalize if chunk cuts through equations
        if self._detect_equations(chunk_text) and ('$' in chunk_text and chunk_text.count('$') % 2 != 0):
            confidence *= 0.7
        
        return min(1.0, confidence)