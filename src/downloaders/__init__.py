# src/downloaders/__init__.py
"""
Download modules for literature acquisition from multiple sources.

ZOTERO MANAGER ARCHITECTURE:
===========================
We maintain TWO Zotero managers with clear separation of concerns:

1. ZoteroLibraryManager (zotero_manager.py):
   - Core Zotero Web API functionality  
   - Lightweight dependencies (PyZotero only)
   - ~650 lines, essential operations

2. EnhancedZoteroLibraryManager (enhanced_zotero_manager.py):
   - Inherits ALL basic functionality
   - Adds DOI-based PDF downloads via browser automation  
   - Heavy dependencies (Selenium + ChromeDriver)
   - ~800 lines, advanced features

LITERATURE SYNCER ARCHITECTURE:
==============================
Literature syncers have been CONSOLIDATED:
- Basic ZoteroLiteratureSyncer was merged into EnhancedZoteroLiteratureSyncer
- EnhancedZoteroLiteratureSyncer gracefully degrades when dependencies unavailable
- ZoteroLiteratureSyncer is now an alias for backward compatibility
   
This separation provides:
✅ Single Responsibility Principle
✅ Dependency isolation
✅ Deployment flexibility  
✅ Better maintainability
✅ Graceful degradation
"""

# Legacy BibTeX support (backward compatibility)
from .bibtex_parser import BibtexParser, PaperMetadata
from .arxiv_searcher import ArxivSearcher, ArxivSearchResult, DownloadResult
from .literature_downloader import LiteratureDownloader, PaperDownloadResult

# Basic Zotero integration (core functionality)
try:
    from .zotero_manager import (
        ZoteroLibraryManager,      # Base manager - core functionality
        ZoteroItem, 
        ZoteroAttachment, 
        SyncResult
    )
    ZOTERO_AVAILABLE = True
except ImportError:
    ZOTERO_AVAILABLE = False

# Enhanced Zotero integration (with DOI downloads)
try:
    from .enhanced_zotero_manager import (
        EnhancedZoteroLibraryManager,  # Enhanced manager - inherits + adds DOI features
        CollectionSyncResult,
        DOIDownloadResult,
        SELENIUM_AVAILABLE
    )
    from .enhanced_literature_syncer import (
        EnhancedZoteroLiteratureSyncer,
        EnhancedSyncResult  # This comes from enhanced syncer now
    )
    
    # Backward compatibility alias (since basic syncer was consolidated)
    ZoteroLiteratureSyncer = EnhancedZoteroLiteratureSyncer
    # Backward compatibility alias for the result class
    LiteratureSyncResult = EnhancedSyncResult
    
    ENHANCED_ZOTERO_AVAILABLE = True
except ImportError:
    ENHANCED_ZOTERO_AVAILABLE = False
    SELENIUM_AVAILABLE = False

# PDF Integration system
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
    )
    PDF_INTEGRATION_AVAILABLE = True
except ImportError:
    PDF_INTEGRATION_AVAILABLE = False

def create_zotero_manager(config, 
                         prefer_enhanced: bool = True,
                         require_doi_downloads: bool = False):
    """
    Factory function to create the appropriate Zotero manager.
    
    ARCHITECTURE DECISION: Automatically select the best available manager
    based on dependencies and requirements.
    
    Args:
        config: Configuration object with Zotero settings
        prefer_enhanced: Prefer enhanced manager if available (default: True)
        require_doi_downloads: Require DOI download capability (raises error if unavailable)
        
    Returns:
        ZoteroLibraryManager or EnhancedZoteroLibraryManager instance
        
    Raises:
        ImportError: If required features are unavailable
    """
    from pathlib import Path
    from ..utils.logging_config import get_logger
    
    logger = get_logger(__name__)
    zotero_config = config.get_zotero_config()
    
    # Check requirements
    if require_doi_downloads and not ENHANCED_ZOTERO_AVAILABLE:
        raise ImportError(
            "DOI downloads required but enhanced Zotero manager unavailable. "
            "Install with: pip install selenium"
        )
    
    # Try enhanced manager first (if preferred and available)
    if prefer_enhanced and ENHANCED_ZOTERO_AVAILABLE:
        logger.info("Creating Enhanced Zotero manager (includes DOI downloads)")
        return EnhancedZoteroLibraryManager(
            library_id=zotero_config['library_id'],
            library_type=zotero_config['library_type'],
            api_key=zotero_config['api_key'],
            output_directory=Path(zotero_config['output_directory']),
            doi_downloads_enabled=SELENIUM_AVAILABLE
        )
    
    # Fallback to basic manager
    elif ZOTERO_AVAILABLE:
        logger.info("Creating basic Zotero manager (core functionality only)")
        if prefer_enhanced:
            logger.info("Enhanced features unavailable - install Selenium for DOI downloads")
        return ZoteroLibraryManager(
            library_id=zotero_config['library_id'],
            library_type=zotero_config['library_type'],
            api_key=zotero_config['api_key'],
            output_directory=Path(zotero_config['output_directory'])
        )
    
    else:
        raise ImportError(
            "Zotero integration unavailable. Install with: pip install pyzotero"
        )

def create_literature_syncer(config, 
                           enable_doi_downloads: bool = True,
                           enable_pdf_integration: bool = True):
    """
    Factory function to create literature syncer with enhanced error handling.
    
    Note: Since basic literature syncer was consolidated into enhanced version,
    this always returns EnhancedZoteroLiteratureSyncer (with graceful degradation).
    
    Args:
        config: Configuration object
        enable_doi_downloads: Enable DOI-based downloads (if available)
        enable_pdf_integration: Enable PDF integration (if available)
        
    Returns:
        EnhancedZoteroLiteratureSyncer instance (with graceful degradation)
        
    Raises:
        ImportError: If Zotero integration is not available
        AttributeError: If config object doesn't have required methods
    """
    from ..utils.logging_config import get_logger
    logger = get_logger(__name__)
    
    if not ENHANCED_ZOTERO_AVAILABLE:
        raise ImportError(
            "Zotero literature syncer unavailable. Install with: pip install pyzotero"
        )
    
    # Check for required method first (cleaner logic)
    if not hasattr(config, 'get_zotero_config'):
        error_msg = (
            f"Configuration object of type '{type(config).__name__}' "
            f"does not have 'get_zotero_config()' method. "
            f"Please use a valid PipelineConfig object."
        )
        logger.error(f"Configuration error: {error_msg}")
        raise AttributeError(error_msg)
    
    # If we get here, the method exists - now try to use it
    try:
        zotero_config = config.get_zotero_config()
        
        logger.info("Creating Literature Syncer (enhanced version with graceful degradation)")
        return EnhancedZoteroLiteratureSyncer(
            zotero_config=zotero_config,
            doi_downloads_enabled=enable_doi_downloads and SELENIUM_AVAILABLE,
            pdf_integration_enabled=enable_pdf_integration and PDF_INTEGRATION_AVAILABLE
        )
        
    except Exception as e:
        # Handle errors from get_zotero_config() or syncer creation
        logger.error(f"Failed to create literature syncer: {e}")
        raise

def create_literature_manager(source_type: str, config):
    """
    Factory function to create appropriate literature manager.
    
    Note: 'zotero' and 'enhanced_zotero' both return the same enhanced syncer
    since basic syncer was consolidated into enhanced version.
    
    Args:
        source_type: Type of literature source ('enhanced_zotero', 'zotero', 'bibtex', 'manual')
        config: Configuration object (not dictionary)
    
    Returns:
        Appropriate literature manager instance
    """
    if source_type in ['zotero', 'enhanced_zotero']:
        if not ENHANCED_ZOTERO_AVAILABLE:
            raise ImportError(
                "Zotero integration not available. Install with: pip install pyzotero"
            )
        return create_literature_syncer(config)
    
    elif source_type == 'bibtex':
        # Legacy support
        return LiteratureDownloader(
            output_directory=config.literature_folder,
            arxiv_config=config.get_arxiv_config()
        )
    
    elif source_type == 'manual':
        # For manual uploads, return None (handle in calling code)
        return None
    
    else:
        raise ValueError(f"Unknown literature source type: {source_type}")

def get_zotero_capabilities():
    """
    Get detailed information about available Zotero capabilities.
    
    Returns:
        Dictionary with capability analysis and recommendations
    """
    capabilities = {
        'basic_zotero': {
            'available': ZOTERO_AVAILABLE,
            'description': 'Core Zotero Web API integration',
            'dependencies': ['pyzotero'],
            'features': [
                'Library synchronization',
                'Item and attachment retrieval', 
                'Collection management',
                'BibTeX export',
                'File downloads (existing attachments)'
            ]
        },
        'enhanced_zotero': {
            'available': ENHANCED_ZOTERO_AVAILABLE,
            'description': 'Enhanced Zotero with DOI-based PDF downloads',
            'dependencies': ['pyzotero', 'selenium', 'ChromeDriver'],
            'features': [
                'All basic features (inherited)',
                'DOI-based PDF downloads',
                'Browser automation',
                'Publisher-specific strategies',
                'Optimized collection processing'
            ],
            'publisher_support': {
                'APS (Physical Review)': '95%',
                'MDPI': '95%', 
                'Nature Publishing': '90%',
                'arXiv': '99%',
                'IEEE': '60-80%',
                'Springer': '60-80%'
            }
        },
        'pdf_integration': {
            'available': PDF_INTEGRATION_AVAILABLE,
            'description': 'PDF integration back to Zotero records',
            'features': ['attach_to_existing', 'download_only']
        },
        'selenium_automation': {
            'available': SELENIUM_AVAILABLE,
            'description': 'Browser automation for PDF downloads',
            'features': ['browser_automation', 'publisher_specific_downloads']
        }
    }
    
    # Generate recommendations
    recommendations = []
    
    if not ZOTERO_AVAILABLE:
        recommendations.append({
            'type': 'error',
            'message': 'Basic Zotero integration unavailable',
            'action': 'Install with: pip install pyzotero'
        })
    elif not ENHANCED_ZOTERO_AVAILABLE:
        recommendations.append({
            'type': 'upgrade',
            'message': 'Enhanced features available with additional dependencies',
            'action': 'Install with: pip install selenium (plus ChromeDriver setup)'
        })
    else:
        recommendations.append({
            'type': 'success',
            'message': 'Full Zotero integration available',
            'action': 'Use create_zotero_manager() for automatic selection'
        })
    
    return {
        'capabilities': capabilities,
        'recommendations': recommendations,
        'suggested_manager': 'enhanced' if ENHANCED_ZOTERO_AVAILABLE else 'basic' if ZOTERO_AVAILABLE else None
    }

def get_available_downloaders():
    """
    Get list of available literature download methods.
    
    Returns:
        Dictionary with available downloaders and their status
    """
    return {
        'arxiv_direct': {
            'available': True,
            'description': 'Direct arXiv API downloads',
            'status': 'active',
            'recommended': False
        },
        'bibtex_arxiv': {
            'available': True,
            'description': 'Legacy BibTeX parsing with arXiv downloads',
            'status': 'legacy',
            'recommended': False
        },
        'zotero': {
            'available': ZOTERO_AVAILABLE,
            'description': 'Basic Zotero Web API integration',
            'status': 'active' if ZOTERO_AVAILABLE else 'unavailable',
            'recommended': ZOTERO_AVAILABLE and not ENHANCED_ZOTERO_AVAILABLE
        },
        'enhanced_zotero': {
            'available': ENHANCED_ZOTERO_AVAILABLE,
            'description': 'Enhanced Zotero with DOI-based PDF downloads and integration',
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

def get_integration_capabilities():
    """
    Get detailed information about PDF integration capabilities.
    
    Returns:
        Dictionary with integration feature availability
    """
    return get_zotero_capabilities()['capabilities']  # Reuse the detailed function

def recommend_literature_source(config) -> dict:
    """
    Recommend the best literature source based on configuration.
    
    Args:
        config: Pipeline configuration
    
    Returns:
        Dictionary with recommended source and explanation
    """
    # Check if Enhanced Zotero is configured and available (BEST OPTION)
    if (ENHANCED_ZOTERO_AVAILABLE and 
        hasattr(config, 'zotero_api_key') and 
        config.zotero_api_key):
        return {
            'source': 'enhanced_zotero',
            'reason': 'Enhanced Zotero with DOI downloads and PDF integration available',
            'features': [
                'Automatic DOI-based PDF downloads',
                'Multi-publisher support (APS, MDPI, Nature, arXiv)',
                'PDF integration back to Zotero records',
                'Knowledge base synchronization'
            ]
        }
    
    # Check if basic Zotero is configured and available
    elif (ZOTERO_AVAILABLE and 
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

def print_zotero_status():
    """Print detailed status of Zotero integration capabilities."""
    print("📚 ZOTERO INTEGRATION STATUS")
    print("=" * 50)
    
    capabilities = get_zotero_capabilities()
    
    for name, info in capabilities['capabilities'].items():
        status = "✅ Available" if info['available'] else "❌ Not Available"
        print(f"\n{name.replace('_', ' ').title()}: {status}")
        print(f"   {info['description']}")
        
        if info['available']:
            print("   Features:")
            for feature in info['features']:
                print(f"     • {feature}")
                
            if 'publisher_support' in info:
                print("   Publisher Success Rates:")
                for publisher, rate in info['publisher_support'].items():
                    print(f"     • {publisher}: {rate}")
    
    print(f"\n💡 RECOMMENDATIONS:")
    for rec in capabilities['recommendations']:
        icon = "🎉" if rec['type'] == 'success' else "⚠️" if rec['type'] == 'upgrade' else "❌"
        print(f"   {icon} {rec['message']}")
        print(f"      → {rec['action']}")

def print_integration_status():
    """Print detailed status of all integration components (legacy alias)."""
    print_zotero_status()

# Export list with clear hierarchy
__all__ = [
    # Legacy BibTeX support
    'BibtexParser', 'PaperMetadata',
    'ArxivSearcher', 'ArxivSearchResult', 'DownloadResult',
    'LiteratureDownloader', 'PaperDownloadResult',
    
    # Core Zotero (basic functionality)
    'ZoteroLibraryManager',        # Base manager
    'ZoteroItem', 'ZoteroAttachment', 'SyncResult',
    'ZoteroLiteratureSyncer', 'LiteratureSyncResult',
    
    # Enhanced Zotero (advanced functionality)  
    'EnhancedZoteroLibraryManager',  # Enhanced manager (inherits from basic)
    'CollectionSyncResult', 'DOIDownloadResult',
    'EnhancedZoteroLiteratureSyncer', 'EnhancedSyncResult',
    
    # PDF Integration
    'integrate_pdfs_with_zotero_fixed',
    'IntegrationMode', 'IntegrationConfig', 'IntegrationResult',
    'FixedZoteroPDFIntegrator',
    'get_available_modes', 'setup_download_only_mode', 'setup_attach_mode',
    
    # Factory and utility functions
    'create_zotero_manager',
    'create_literature_syncer', 
    'create_literature_manager',
    'get_zotero_capabilities',
    'get_available_downloaders',
    'get_integration_capabilities', 
    'recommend_literature_source',
    'print_zotero_status',
    'print_integration_status',  # Legacy alias
    
    # Availability flags
    'ZOTERO_AVAILABLE', 'ENHANCED_ZOTERO_AVAILABLE', 
    'PDF_INTEGRATION_AVAILABLE', 'SELENIUM_AVAILABLE'
]

if __name__ == "__main__":
    # Print status when module is run directly
    print_zotero_status()