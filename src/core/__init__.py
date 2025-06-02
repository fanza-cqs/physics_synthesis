# src/core/__init__.py
"""Core modules for document processing and knowledge management."""

from .document_processor import DocumentProcessor, ProcessedDocument
from .embeddings import EmbeddingsManager, DocumentChunk, SearchResult
from .knowledge_base import KnowledgeBase

__all__ = [
    'DocumentProcessor',
    'ProcessedDocument', 
    'EmbeddingsManager',
    'DocumentChunk',
    'SearchResult',
    'KnowledgeBase'
]