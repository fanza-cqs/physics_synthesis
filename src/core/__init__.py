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
from .kb_orchestrator import (
    KnowledgeBaseOrchestrator,
    KBOperation,
    SourceSelection,
    PreProcessingSummary,
    OrchestrationResult
)
from .source_processors import (
    BaseSourceProcessor,
    SourceProcessingResult,
    SourceScanResult,
    LocalFolderProcessor,
    ZoteroProcessor,
    CustomFolderProcessor
)

__all__ = [
    # Document processing
    'DocumentProcessor',
    'ProcessedDocument', 
    'EmbeddingsManager',
    'DocumentChunk',
    'SearchResult',
    
    # Knowledge base management
    'KnowledgeBase',
    'list_knowledge_bases',
    'create_knowledge_base', 
    'load_knowledge_base',
    'delete_knowledge_base',
    
    # Orchestrator
    'KnowledgeBaseOrchestrator',
    'KBOperation',
    'SourceSelection',
    'PreProcessingSummary', 
    'OrchestrationResult',
    
    # Source processors
    'BaseSourceProcessor',
    'SourceProcessingResult',
    'SourceScanResult',
    'LocalFolderProcessor',
    'ZoteroProcessor',
    'CustomFolderProcessor'
]