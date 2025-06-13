# src/core/__init__.py
"""Core modules for document processing and knowledge management."""

from .document_processor import DocumentProcessor, ProcessedDocument
from .embeddings import EmbeddingsManager, DocumentChunk, SearchResult

# Original KB functions (keep for backward compatibility)
from .knowledge_base import (
    KnowledgeBase, 
    list_knowledge_bases as _list_knowledge_bases_original, 
    create_knowledge_base as _create_knowledge_base_original, 
    load_knowledge_base as _load_knowledge_base_original, 
    delete_knowledge_base as _delete_knowledge_base_original
)

# Context-aware KB manager
from .knowledge_base_manager import (
    KnowledgeBaseManager,
    create_knowledge_base_with_context,
    delete_knowledge_base_with_context,
    list_knowledge_bases_with_context
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

# Context-aware wrapper functions that replace the originals
def create_knowledge_base(name: str, **kwargs):
    """
    Create knowledge base - automatically uses context awareness if available
    
    Args:
        name: KB name
        **kwargs: Additional arguments
        
    Returns:
        True if created successfully (for UI) or KnowledgeBase instance (for direct use)
    """
    try:
        # Try to get session integration from Streamlit
        import streamlit as st
        integration = st.session_state.get('session_integration')
        config = st.session_state.get('config')
        
        if integration and config:
            # Context-aware version for UI use
            return create_knowledge_base_with_context(name, config, integration, **kwargs)
        else:
            # Fallback to original function for direct use
            base_dir = config.knowledge_bases_folder if config else kwargs.get('base_storage_dir')
            return _create_knowledge_base_original(name, base_storage_dir=base_dir, **kwargs)
    except ImportError:
        # No Streamlit available - use original function
        return _create_knowledge_base_original(name, **kwargs)
    except Exception:
        # Any other error - use original function
        return _create_knowledge_base_original(name, **kwargs)


def delete_knowledge_base(name: str, base_storage_dir=None):
    """
    Delete knowledge base - automatically uses context awareness if available
    
    Args:
        name: KB name
        base_storage_dir: Base directory (for backward compatibility)
        
    Returns:
        True if deleted successfully
    """
    try:
        # Try to get session integration from Streamlit
        import streamlit as st
        integration = st.session_state.get('session_integration')
        config = st.session_state.get('config')
        
        if integration and config:
            # Context-aware version for UI use
            return delete_knowledge_base_with_context(name, config, integration)
        else:
            # Fallback to original function
            storage_dir = base_storage_dir or (config.knowledge_bases_folder if config else None)
            return _delete_knowledge_base_original(name, storage_dir)
    except ImportError:
        # No Streamlit available - use original function
        return _delete_knowledge_base_original(name, base_storage_dir)
    except Exception:
        # Any other error - use original function
        return _delete_knowledge_base_original(name, base_storage_dir)


def list_knowledge_bases(base_storage_dir=None):
    """
    List knowledge bases - automatically uses context awareness if available
    
    Args:
        base_storage_dir: Base directory (for backward compatibility)
        
    Returns:
        List of KB information dictionaries
    """
    try:
        # Try to get session integration from Streamlit
        import streamlit as st
        integration = st.session_state.get('session_integration')
        config = st.session_state.get('config')
        
        if integration and config:
            # Context-aware version for UI use
            return list_knowledge_bases_with_context(config, integration)
        else:
            # Fallback to original function
            storage_dir = base_storage_dir or (config.knowledge_bases_folder if config else None)
            return _list_knowledge_bases_original(storage_dir)
    except ImportError:
        # No Streamlit available - use original function
        return _list_knowledge_bases_original(base_storage_dir)
    except Exception:
        # Any other error - use original function
        return _list_knowledge_bases_original(base_storage_dir)


def load_knowledge_base(name: str, base_storage_dir=None):
    """
    Load knowledge base - automatically uses context awareness if available
    
    Args:
        name: KB name
        base_storage_dir: Base directory (for backward compatibility)
        
    Returns:
        KnowledgeBase instance or None
    """
    try:
        # Try to get session integration from Streamlit
        import streamlit as st
        integration = st.session_state.get('session_integration')
        config = st.session_state.get('config')
        
        if integration and config:
            # Context-aware version for UI use
            manager = KnowledgeBaseManager(config, integration)
            return manager.load_knowledge_base(name)
        else:
            # Fallback to original function
            storage_dir = base_storage_dir or (config.knowledge_bases_folder if config else None)
            return _load_knowledge_base_original(name, storage_dir)
    except ImportError:
        # No Streamlit available - use original function
        return _load_knowledge_base_original(name, base_storage_dir)
    except Exception:
        # Any other error - use original function
        return _load_knowledge_base_original(name, base_storage_dir)


# For direct access to original functions (if needed)
def get_original_kb_functions():
    """Get original KB functions for direct use without context awareness"""
    return {
        'create_knowledge_base': _create_knowledge_base_original,
        'delete_knowledge_base': _delete_knowledge_base_original,
        'list_knowledge_bases': _list_knowledge_bases_original,
        'load_knowledge_base': _load_knowledge_base_original
    }


__all__ = [
    # Document processing
    'DocumentProcessor',
    'ProcessedDocument', 
    'EmbeddingsManager',
    'DocumentChunk',
    'SearchResult',
    
    # Knowledge base management (context-aware versions)
    'KnowledgeBase',
    'list_knowledge_bases',
    'create_knowledge_base', 
    'load_knowledge_base',
    'delete_knowledge_base',
    
    # KB Manager (for advanced use)
    'KnowledgeBaseManager',
    'create_knowledge_base_with_context',
    'delete_knowledge_base_with_context', 
    'list_knowledge_bases_with_context',
    
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
    'CustomFolderProcessor',
    
    # Utilities
    'get_original_kb_functions'
]