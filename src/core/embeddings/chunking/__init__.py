#!/usr/bin/env python3
"""
Chunking strategies for the Physics Literature Synthesis Pipeline.

This module provides various text chunking strategies for processing
scientific documents with different approaches optimized for physics literature.

Phase 1B: Enhanced chunking strategies for better document understanding.
"""

from .base_strategy import BaseChunkingStrategy, ChunkingConfig, ChunkMetadata
from .simple_strategy import SimpleChunkingStrategy
from .context_aware_strategy import ContextAwareChunkingStrategy

# Factory function for creating chunking strategies
def create_chunking_strategy(strategy_name: str, config: ChunkingConfig = None) -> BaseChunkingStrategy:
    """
    Factory function to create chunking strategies by name.
    
    Args:
        strategy_name: Name of the strategy ('simple', 'context_aware')
        config: Configuration for the strategy
    
    Returns:
        Initialized chunking strategy
    """
    strategies = {
        'simple': SimpleChunkingStrategy,
        'context_aware': ContextAwareChunkingStrategy,
    }
    
    if strategy_name not in strategies:
        available = ', '.join(strategies.keys())
        raise ValueError(f"Unknown chunking strategy '{strategy_name}'. Available: {available}")
    
    return strategies[strategy_name](config)

# List available strategies
def list_chunking_strategies():
    """List all available chunking strategies."""
    return ['simple', 'context_aware']

__all__ = [
    'BaseChunkingStrategy',
    'ChunkingConfig', 
    'ChunkMetadata',
    'SimpleChunkingStrategy',
    'ContextAwareChunkingStrategy',
    'create_chunking_strategy',
    'list_chunking_strategies'
]