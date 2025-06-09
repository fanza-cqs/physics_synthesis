# src/core/__init__.py
"""Core modules for document processing and knowledge management."""

from .document_processor import DocumentProcessor, ProcessedDocument
from .embeddings import EmbeddingsManager, DocumentChunk, SearchResult
from .knowledge_base import (
    KnowledgeBase, 
    list_knowledge_bases, 
    create_knowledge_base, 
    load_knowledge_base, 
    delete_knowledge_base
)

__all__ = [
    'DocumentProcessor',
    'ProcessedDocument', 
    'EmbeddingsManager',
    'DocumentChunk',
    'SearchResult',
    'KnowledgeBase',
    'list_knowledge_bases',
    'create_knowledge_base', 
    'load_knowledge_base',
    'delete_knowledge_base'
]