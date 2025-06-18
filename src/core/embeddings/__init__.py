#!/usr/bin/env python3
"""
Embeddings module for the Physics Literature Synthesis Pipeline.

This module provides document embedding functionality for semantic search.
Restructured for modular architecture while maintaining backward compatibility.

Phase 1A: Reorganization of existing functionality
Phase 1B: Enhanced embeddings with new strategies
"""

# Backward compatible exports - maintain existing API
from .base_embeddings import (
    EmbeddingsManager,
    DocumentChunk, 
    SearchResult
)

# Phase 1B: Enhanced embeddings components
from .enhanced_embeddings import EnhancedEmbeddingsManager
from .chunking import (
    BaseChunkingStrategy,
    ChunkingConfig,
    ChunkMetadata,
    create_chunking_strategy,
    list_chunking_strategies
)

# Factory function for creating embeddings managers
def create_embeddings_manager(enhanced: bool = False, **kwargs) -> EmbeddingsManager:
    """
    Factory function to create embeddings managers.
    
    Args:
        enhanced: Whether to use enhanced embeddings manager
        **kwargs: Arguments passed to the embeddings manager constructor
    
    Returns:
        Initialized embeddings manager
    """
    if enhanced:
        return EnhancedEmbeddingsManager(**kwargs)
    else:
        return EmbeddingsManager(**kwargs)

# Module version for tracking restructuring
__version__ = "1.1.0-enhanced"

# Re-export everything that was previously available from embeddings.py
# Plus new enhanced functionality
__all__ = [
    # Original API (Phase 1A)
    'EmbeddingsManager',
    'DocumentChunk',
    'SearchResult',
    
    # Enhanced API (Phase 1B)
    'EnhancedEmbeddingsManager',
    'BaseChunkingStrategy',
    'ChunkingConfig',
    'ChunkMetadata',
    'create_chunking_strategy',
    'list_chunking_strategies',
    
    # Factory functions
    'create_embeddings_manager'
]