#!/usr/bin/env python3
"""
Enhanced embeddings manager with improved chunking strategies.

This module extends the base embeddings functionality with:
- Pluggable chunking strategies
- Better document preprocessing
- Enhanced metadata extraction
- A/B testing capabilities

Phase 1B: Enhanced embeddings for better document understanding.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from .base_embeddings import EmbeddingsManager, DocumentChunk, SearchResult
from .chunking import create_chunking_strategy, ChunkingConfig
from ..document_processor import ProcessedDocument
from ...utils.logging_config import get_logger

logger = get_logger(__name__)

class EnhancedEmbeddingsManager(EmbeddingsManager):
    """
    Enhanced embeddings manager with improved chunking and processing.
    
    This class extends the base EmbeddingsManager with:
    - Pluggable chunking strategies (simple, context-aware)
    - Enhanced document preprocessing
    - Better metadata extraction
    - Configuration-driven behavior
    - Backward compatibility with base implementation
    
    Use this for:
    - Better chunk quality and semantic coherence
    - Configurable chunking strategies
    - Enhanced physics document processing
    - A/B testing different approaches
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 chunking_strategy: str = "context_aware",
                 chunking_config: ChunkingConfig = None):
        """
        Initialize the enhanced embeddings manager.
        
        Args:
            model_name: Name of the sentence transformer model
            chunk_size: Target chunk size (words for simple, chars for context-aware)
            chunk_overlap: Overlap between chunks
            chunking_strategy: Strategy to use ('simple', 'context_aware')
            chunking_config: Detailed configuration for chunking
        """
        # Initialize base embeddings manager
        super().__init__(model_name, chunk_size, chunk_overlap)
        
        # Enhanced configuration
        self.chunking_strategy_name = chunking_strategy
        
        # Create chunking configuration
        if chunking_config is None:
            chunking_config = ChunkingConfig(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                preserve_sentences=True,
                preserve_equations=True,
                section_awareness=True
            )
        
        # Initialize chunking strategy
        try:
            self.chunking_strategy = create_chunking_strategy(chunking_strategy, chunking_config)
            logger.info(f"Enhanced embeddings manager initialized with '{chunking_strategy}' strategy")
        except ValueError as e:
            logger.warning(f"Unknown chunking strategy '{chunking_strategy}', falling back to 'simple': {e}")
            self.chunking_strategy = create_chunking_strategy('simple', chunking_config)
            self.chunking_strategy_name = 'simple'
        
        # Enhanced metadata tracking
        self.chunk_metadata: List[Dict[str, Any]] = []
        self.strategy_info = self.chunking_strategy.get_strategy_info()
    
    def chunk_text(self, text: str, document_metadata: Dict[str, Any] = None) -> List[str]:
        """
        Enhanced text chunking using configured strategy.
        
        Args:
            text: Input text to chunk
            document_metadata: Optional metadata about the document
        
        Returns:
            List of chunk texts (maintains compatibility with base class)
        """
        if not text.strip():
            return []
        
        # Use the chunking strategy to create enhanced chunks
        enhanced_chunks = self.chunking_strategy.chunk_text(text, document_metadata)
        
        # Store enhanced metadata for later use
        chunk_metadata = []
        chunk_texts = []
        
        for chunk_data in enhanced_chunks:
            chunk_texts.append(chunk_data['text'])
            chunk_metadata.append({
                'text': chunk_data['text'],
                'metadata': chunk_data['metadata'],
                'strategy': self.chunking_strategy_name
            })
        
        # Store metadata for this document's chunks
        self.chunk_metadata.extend(chunk_metadata)
        
        logger.debug(f"Enhanced chunking created {len(chunk_texts)} chunks using '{self.chunking_strategy_name}' strategy")
        return chunk_texts
    
    def add_documents(self, documents: List[ProcessedDocument]) -> None:
        """
        Enhanced document addition with improved preprocessing.
        
        Args:
            documents: List of processed documents to add
        """
        logger.info(f"Adding {len(documents)} documents with enhanced processing")
        
        new_chunks = []
        chunk_id_counter = len(self.chunks)
        
        for doc in documents:
            if not doc.processing_success or not doc.text.strip():
                logger.warning(f"Skipping document with no text: {doc.file_name}")
                continue
            
            # Enhanced preprocessing
            preprocessed_text = self._preprocess_document(doc)
            
            # Create document metadata for chunking
            document_metadata = {
                'file_name': doc.file_name,
                'file_path': doc.file_path,
                'source_type': doc.source_type,
                'word_count': doc.word_count,
                'file_size_mb': doc.file_size_mb
            }
            
            # Use enhanced chunking
            text_chunks = self.chunk_text(preprocessed_text, document_metadata)
            
            # Create DocumentChunk objects with enhanced metadata
            for chunk_index, chunk_text in enumerate(text_chunks):
                # Get enhanced metadata if available
                enhanced_metadata = None
                if chunk_index < len(self.chunk_metadata):
                    enhanced_metadata = self.chunk_metadata[-(len(text_chunks) - chunk_index)]
                
                chunk = DocumentChunk(
                    chunk_id=chunk_id_counter,
                    file_path=doc.file_path,
                    file_name=doc.file_name,
                    source_type=doc.source_type,
                    text=chunk_text,
                    chunk_index=chunk_index,
                    total_chunks=len(text_chunks),
                    full_document_text=doc.text
                )
                
                # Add enhanced metadata as attributes
                if enhanced_metadata:
                    chunk.enhanced_metadata = enhanced_metadata['metadata']
                    chunk.chunking_strategy = enhanced_metadata['strategy']
                
                new_chunks.append(chunk)
                chunk_id_counter += 1
            
            logger.debug(f"Enhanced processing created {len(text_chunks)} chunks for {doc.file_name}")
        
        # Add new chunks to storage
        self.chunks.extend(new_chunks)
        
        # Create embeddings for new chunks
        if new_chunks:
            logger.info(f"Creating embeddings for {len(new_chunks)} enhanced chunks")
            new_texts = [chunk.text for chunk in new_chunks]
            new_embeddings = self.model.encode(new_texts, show_progress_bar=True)
            
            # Combine with existing embeddings
            if self.embeddings is not None:
                import numpy as np
                self.embeddings = np.vstack([self.embeddings, new_embeddings])
            else:
                self.embeddings = new_embeddings
        
        logger.info(f"Enhanced embeddings: {len(self.chunks)} total chunks")
    
    def _preprocess_document(self, doc: ProcessedDocument) -> str:
        """
        Enhanced document preprocessing for better chunking.
        
        Args:
            doc: Processed document
        
        Returns:
            Preprocessed text optimized for chunking
        """
        text = doc.text
        
        # Basic cleaning
        import re
        
        # Normalize whitespace while preserving paragraph breaks
        text = re.sub(r'[ \t]+', ' ', text)  # Normalize spaces/tabs
        text = re.sub(r'\n\s*\n', '\n\n', text)  # Normalize paragraph breaks
        
        # Preserve equation formatting
        text = re.sub(r'\$\s+', text)  # Remove spaces after $
        text = re.sub(r'\s+\, ', text)  # Remove spaces before $
        
        # Handle common LaTeX commands that might interfere with chunking
        text = re.sub(r'\\newpage\s*', '\n\n', text)
        text = re.sub(r'\\clearpage\s*', '\n\n', text)
        
        # Preserve reference formatting
        text = re.sub(r'\s*\\cite\{', ' \\cite{', text)
        text = re.sub(r'\s*\\ref\{', ' \\ref{', text)
        
        return text.strip()
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """
        Get enhanced statistics including chunking strategy information.
        
        Returns:
            Dictionary with enhanced statistics
        """
        base_stats = self.get_statistics()
        
        # Add enhanced information
        enhanced_stats = base_stats.copy()
        enhanced_stats.update({
            'chunking_strategy': self.chunking_strategy_name,
            'strategy_config': self.strategy_info,
            'enhanced_features': {
                'context_aware_chunking': self.chunking_strategy_name != 'simple',
                'equation_preservation': getattr(self.chunking_strategy.config, 'preserve_equations', False),
                'sentence_awareness': getattr(self.chunking_strategy.config, 'preserve_sentences', False),
                'section_awareness': getattr(self.chunking_strategy.config, 'section_awareness', False)
            }
        })
        
        # Analyze chunk quality if we have enhanced metadata
        if hasattr(self, 'chunk_metadata') and self.chunk_metadata:
            quality_stats = self._analyze_chunk_quality()
            enhanced_stats['chunk_quality'] = quality_stats
        
        return enhanced_stats
    
    def _analyze_chunk_quality(self) -> Dict[str, Any]:
        """
        Analyze the quality of chunks based on enhanced metadata.
        
        Returns:
            Dictionary with chunk quality statistics
        """
        if not self.chunk_metadata:
            return {}
        
        total_chunks = len(self.chunk_metadata)
        
        # Count chunks with different characteristics
        has_equations = sum(1 for chunk in self.chunk_metadata 
                          if hasattr(chunk['metadata'], 'has_equations') and chunk['metadata'].has_equations)
        
        has_citations = sum(1 for chunk in self.chunk_metadata 
                          if hasattr(chunk['metadata'], 'has_citations') and chunk['metadata'].has_citations)
        
        # Calculate average confidence score
        confidence_scores = [chunk['metadata'].confidence_score 
                           for chunk in self.chunk_metadata 
                           if hasattr(chunk['metadata'], 'confidence_score')]
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return {
            'total_chunks': total_chunks,
            'chunks_with_equations': has_equations,
            'chunks_with_citations': has_citations,
            'equation_percentage': (has_equations / total_chunks * 100) if total_chunks > 0 else 0,
            'citation_percentage': (has_citations / total_chunks * 100) if total_chunks > 0 else 0,
            'average_confidence': round(avg_confidence, 3)
        }
    
    def search_with_enhanced_context(self, 
                                   query: str, 
                                   context_type: str = None,
                                   top_k: int = 10) -> List[SearchResult]:
        """
        Enhanced search with context-aware filtering.
        
        Args:
            query: Search query
            context_type: Filter by context type ('equations', 'citations', etc.)
            top_k: Number of results to return
        
        Returns:
            List of enhanced search results
        """
        # Get base search results
        results = self.search(query, top_k * 2)  # Get more results for filtering
        
        # Apply context-based filtering if requested
        if context_type and hasattr(self, 'chunk_metadata'):
            filtered_results = []
            
            for result in results:
                chunk_id = result.chunk.chunk_id
                
                # Find corresponding enhanced metadata
                chunk_meta = None
                for meta in self.chunk_metadata:
                    if meta['text'] == result.chunk.text:
                        chunk_meta = meta['metadata']
                        break
                
                if chunk_meta:
                    # Apply context filter
                    if (context_type == 'equations' and getattr(chunk_meta, 'has_equations', False)) or \
                       (context_type == 'citations' and getattr(chunk_meta, 'has_citations', False)) or \
                       (context_type == 'high_confidence' and getattr(chunk_meta, 'confidence_score', 0) > 0.8):
                        filtered_results.append(result)
                
                if len(filtered_results) >= top_k:
                    break
            
            return filtered_results
        
        return results[:top_k]
    
    def get_chunking_strategy_info(self) -> Dict[str, Any]:
        """
        Get information about the current chunking strategy.
        
        Returns:
            Dictionary with strategy information
        """
        return self.strategy_info.copy()
    
    def switch_chunking_strategy(self, new_strategy: str, config: ChunkingConfig = None) -> bool:
        """
        Switch to a different chunking strategy.
        
        Note: This requires rebuilding embeddings for existing documents.
        
        Args:
            new_strategy: Name of the new strategy
            config: Configuration for the new strategy
        
        Returns:
            True if strategy was changed successfully
        """
        try:
            old_strategy = self.chunking_strategy_name
            
            # Create new strategy
            if config is None:
                config = ChunkingConfig(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
            
            new_strategy_obj = create_chunking_strategy(new_strategy, config)
            
            # Update strategy
            self.chunking_strategy = new_strategy_obj
            self.chunking_strategy_name = new_strategy
            self.strategy_info = new_strategy_obj.get_strategy_info()
            
            logger.info(f"Switched chunking strategy from '{old_strategy}' to '{new_strategy}'")
            logger.warning("Existing embeddings may need to be rebuilt for consistency")
            
            return True
            
        except ValueError as e:
            logger.error(f"Failed to switch chunking strategy: {e}")
            return False