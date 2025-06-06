# src/downloaders/__init__.py
"""Download modules for literature acquisition from multiple sources."""

# Legacy BibTeX support (backward compatibility)
from .bibtex_parser import BibtexParser, PaperMetadata
from .arxiv_searcher import ArxivSearcher, ArxivSearchResult, DownloadResult
from .literature_downloader import LiteratureDownloader, PaperDownloadResult

# NEW: Zotero integration
try:
    from .zotero_manager import (
        ZoteroLibraryManager, 
        ZoteroItem, 
        ZoteroAttachment, 
        SyncResult
    )
    from .zotero_literature_syncer import (
        ZoteroLiteratureSyncer,
        LiteratureSyncResult
    )
    ZOTERO_AVAILABLE = True
except ImportError:
    ZOTERO_AVAILABLE = False

__all__ = [
    # Legacy BibTeX support
    'BibtexParser',
    'PaperMetadata',
    'ArxivSearcher', 
    'ArxivSearchResult',
    'DownloadResult',
    'LiteratureDownloader',
    'PaperDownloadResult',
    # Zotero integration (if available)
    'ZOTERO_AVAILABLE'
]

# Add Zotero exports if available
if ZOTERO_AVAILABLE:
    __all__.extend([
        'ZoteroLibraryManager',
        'ZoteroItem',
        'ZoteroAttachment',
        'SyncResult',
        'ZoteroLiteratureSyncer',
        'LiteratureSyncResult'
    ])

def get_available_downloaders():
    """
    Get list of available literature download methods.
    
    Returns:
        Dictionary with available downloaders and their status
    """
    return {
        'bibtex_arxiv': {
            'available': True,
            'description': 'Legacy BibTeX parsing with arXiv downloads',
            'status': 'deprecated',
            'recommended': False
        },
        'arxiv_direct': {
            'available': True,
            'description': 'Direct arXiv API downloads',
            'status': 'active',
            'recommended': False
        },
        'zotero': {
            'available': ZOTERO_AVAILABLE,
            'description': 'Zotero Web API integration',
            'status': 'active' if ZOTERO_AVAILABLE else 'unavailable',
            'recommended': ZOTERO_AVAILABLE
        },
        'manual': {
            'available': True,
            'description': 'Manual file uploads',
            'status': 'active',
            'recommended': False
        }
    }

def create_literature_manager(source_type: str, config: dict):
    """
    Factory function to create appropriate literature manager.
    
    Args:
        source_type: Type of literature source ('zotero', 'bibtex', 'manual')
        config: Configuration dictionary
    
    Returns:
        Appropriate literature manager instance
    """
    if source_type == 'zotero':
        if not ZOTERO_AVAILABLE:
            raise ImportError(
                "Zotero integration not available. Install with: pip install pyzotero"
            )
        return ZoteroLiteratureSyncer(config.get_zotero_config())
    
    elif source_type == 'bibtex':
        # Legacy support
        return LiteratureDownloader(
            output_directory=config.literature_folder,
            arxiv_config=config.get_arxiv_config()
        )
    
    elif source_type == 'manual':
        # For manual uploads, return basic knowledge base integration
        return None  # Handle in calling code
    
    else:
        raise ValueError(f"Unknown literature source type: {source_type}")

def recommend_literature_source(config) -> str:
    """
    Recommend the best literature source based on configuration.
    
    Args:
        config: Pipeline configuration
    
    Returns:
        Recommended source type
    """
    available = get_available_downloaders()
    
    # Check if Zotero is configured and available
    if (available['zotero']['available'] and 
        hasattr(config, 'zotero_api_key') and 
        config.zotero_api_key):
        return 'zotero'
    
    # Fallback to legacy BibTeX if no better option
    return 'bibtex'