# src/downloaders/__init__.py
"""Download modules for literature acquisition from multiple sources."""

# Legacy BibTeX support (backward compatibility)
from .bibtex_parser import BibtexParser, PaperMetadata
from .arxiv_searcher import ArxivSearcher, ArxivSearchResult, DownloadResult
from .literature_downloader import LiteratureDownloader, PaperDownloadResult

# Original Zotero integration
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

# Enhanced Zotero integration (NEW)
try:
    from .enhanced_zotero_manager import (
        EnhancedZoteroLibraryManager,
        CollectionSyncResult,
        DOIDownloadResult,
        SELENIUM_AVAILABLE
    )
    from .enhanced_literature_syncer import EnhancedZoteroLiteratureSyncer
    ENHANCED_ZOTERO_AVAILABLE = True
except ImportError:
    ENHANCED_ZOTERO_AVAILABLE = False
    SELENIUM_AVAILABLE = False

# PDF Integration system (NEW) - UPDATED: Removed upload_replace components
try:
    from .zotero_pdf_integrator_fixed import (
        integrate_pdfs_with_zotero_fixed,
        IntegrationMode,
        IntegrationConfig,
        IntegrationResult,
        FixedZoteroPDFIntegrator,
        get_available_modes,
        setup_download_only_mode,
        setup_attach_mode,
        # setup_upload_replace_mode  # REMOVED - disabled mode
    )
    PDF_INTEGRATION_AVAILABLE = True
except ImportError:
    PDF_INTEGRATION_AVAILABLE = False

__all__ = [
    # Legacy BibTeX support
    'BibtexParser',
    'PaperMetadata',
    'ArxivSearcher', 
    'ArxivSearchResult',
    'DownloadResult',
    'LiteratureDownloader',
    'PaperDownloadResult',
    # Availability flags
    'ZOTERO_AVAILABLE',
    'ENHANCED_ZOTERO_AVAILABLE',
    'PDF_INTEGRATION_AVAILABLE',
    'SELENIUM_AVAILABLE'
]

# Add original Zotero exports if available
if ZOTERO_AVAILABLE:
    __all__.extend([
        'ZoteroLibraryManager',
        'ZoteroItem',
        'ZoteroAttachment',
        'SyncResult',
        'ZoteroLiteratureSyncer',
        'LiteratureSyncResult'
    ])

# Add enhanced Zotero exports if available
if ENHANCED_ZOTERO_AVAILABLE:
    __all__.extend([
        'EnhancedZoteroLibraryManager',
        'CollectionSyncResult',
        'DOIDownloadResult',
        'EnhancedZoteroLiteratureSyncer'
    ])

# Add PDF integration exports if available - UPDATED: Removed upload_replace components
if PDF_INTEGRATION_AVAILABLE:
    __all__.extend([
        'integrate_pdfs_with_zotero_fixed',
        'IntegrationMode',
        'IntegrationConfig',
        'IntegrationResult',
        'FixedZoteroPDFIntegrator',
        'get_available_modes',
        'setup_download_only_mode',
        'setup_attach_mode',
        # 'setup_upload_replace_mode'  # REMOVED - disabled mode
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
            'recommended': ZOTERO_AVAILABLE and not ENHANCED_ZOTERO_AVAILABLE
        },
        'enhanced_zotero': {
            'available': ENHANCED_ZOTERO_AVAILABLE,
            'description': 'Enhanced Zotero with DOI-based PDF downloads',
            'status': 'active' if ENHANCED_ZOTERO_AVAILABLE else 'unavailable',
            'recommended': ENHANCED_ZOTERO_AVAILABLE
        },
        'manual': {
            'available': True,
            'description': 'Manual file uploads',
            'status': 'active',
            'recommended': False
        }
    }

def get_zotero_capabilities():
    """
    Get detailed information about Zotero integration capabilities.
    
    Returns:
        Dictionary with Zotero feature availability
    """
    return {
        'basic_zotero': {
            'available': ZOTERO_AVAILABLE,
            'features': ['library_sync', 'collection_management', 'basic_downloads']
        },
        'enhanced_zotero': {
            'available': ENHANCED_ZOTERO_AVAILABLE,
            'features': [
                'doi_based_downloads', 
                'selenium_automation',
                'multi_publisher_support',
                'intelligent_pdf_acquisition'
            ]
        },
        'pdf_integration': {
            'available': PDF_INTEGRATION_AVAILABLE,
            'features': [
                'attach_to_existing',
                # 'upload_and_replace',  # REMOVED - disabled mode
                'download_only',
                'metadata_preservation'
            ]
        },
        'selenium_automation': {
            'available': SELENIUM_AVAILABLE,
            'features': ['browser_automation', 'publisher_specific_downloads']
        }
    }

def create_literature_manager(source_type: str, config: dict):
    """
    Factory function to create appropriate literature manager.
    
    Args:
        source_type: Type of literature source ('enhanced_zotero', 'zotero', 'bibtex', 'manual')
        config: Configuration dictionary
    
    Returns:
        Appropriate literature manager instance
    """
    if source_type == 'enhanced_zotero':
        if not ENHANCED_ZOTERO_AVAILABLE:
            raise ImportError(
                "Enhanced Zotero integration not available. Check imports and dependencies."
            )
        return EnhancedZoteroLiteratureSyncer(
            zotero_config=config.get_zotero_config(),
            doi_downloads_enabled=True,
            pdf_integration_enabled=PDF_INTEGRATION_AVAILABLE
        )
    
    elif source_type == 'zotero':
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
        Recommended source type with explanation
    """
    available = get_available_downloaders()
    
    # Check if Enhanced Zotero is configured and available (BEST OPTION)
    if (available['enhanced_zotero']['available'] and 
        hasattr(config, 'zotero_api_key') and 
        config.zotero_api_key):
        return {
            'source': 'enhanced_zotero',
            'reason': 'Enhanced Zotero with DOI downloads and PDF integration available',
            'features': [
                'Automatic DOI-based PDF downloads',
                'Multi-publisher support (APS, MDPI, Nature, arXiv)',
                'PDF integration back to Zotero records (attach mode)',  # UPDATED
                'Knowledge base synchronization'
            ]
        }
    
    # Check if basic Zotero is configured and available
    elif (available['zotero']['available'] and 
          hasattr(config, 'zotero_api_key') and 
          config.zotero_api_key):
        return {
            'source': 'zotero',
            'reason': 'Basic Zotero integration available',
            'features': [
                'Library synchronization',
                'Collection management',
                'Basic PDF downloads'
            ],
            'upgrade_note': 'Consider upgrading to enhanced_zotero for DOI downloads'
        }
    
    # Fallback to legacy BibTeX if no better option
    else:
        return {
            'source': 'bibtex',
            'reason': 'No Zotero configuration found, using legacy BibTeX support',
            'features': [
                'BibTeX file parsing',
                'arXiv downloads',
                'Manual file processing'
            ],
            'upgrade_note': 'Configure Zotero API for enhanced features'
        }

def print_integration_status():
    """Print detailed status of all integration components."""
    print("📚 LITERATURE INTEGRATION STATUS")
    print("=" * 50)
    
    capabilities = get_zotero_capabilities()
    
    for component, info in capabilities.items():
        status = "✅ Available" if info['available'] else "❌ Not Available"
        print(f"{component.replace('_', ' ').title()}: {status}")
        
        if info['available']:
            for feature in info['features']:
                print(f"   • {feature.replace('_', ' ').title()}")
        print()
    
    # UPDATED: Add information about disabled modes
    print("❌ DISABLED FEATURES")
    print("-" * 30)
    print("• upload_replace mode (disabled due to API limitations)")
    print("• Use 'attach' mode instead for reliable PDF integration")
    print()
    
    print("💡 RECOMMENDATIONS")
    print("-" * 30)
    
    if ENHANCED_ZOTERO_AVAILABLE and PDF_INTEGRATION_AVAILABLE:
        print("🎉 You have the enhanced integration system!")
        print("   • Use EnhancedZoteroLiteratureSyncer for best results")
        print("   • DOI downloads and PDF integration available")
        print("   • Supported modes: download_only, attach")
    elif ENHANCED_ZOTERO_AVAILABLE:
        print("⚠️  Enhanced Zotero available but PDF integration missing")
        print("   • Check zotero_pdf_integrator_fixed imports")
    elif ZOTERO_AVAILABLE:
        print("📝 Basic Zotero available - consider upgrading")
        print("   • Install enhanced components for DOI downloads")
    else:
        print("🔧 Limited integration available")
        print("   • Install pyzotero: pip install pyzotero")
        print("   • Install selenium: pip install selenium")
        print("   • Configure Zotero API credentials")

if __name__ == "__main__":
    # Print status when module is run directly
    print_integration_status()