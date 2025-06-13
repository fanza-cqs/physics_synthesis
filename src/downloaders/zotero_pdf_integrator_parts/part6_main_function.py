# Fixed Zotero PDF Integration System - Part 6: Main Integration Function (Modular)
# File: src/downloaders/zotero_pdf_integrator_parts/part6_main_function.py

from typing import Dict, List, Optional

# Import from other parts
from .part1_core_classes import IntegrationMode, IntegrationConfig, IntegrationResult
from .part2_main_class import FixedZoteroPDFIntegrator

# Main integration function using FIXED methods
def integrate_pdfs_with_zotero_fixed(download_results: List[Dict], 
                                    zotero_manager,
                                    mode: str = "download_only",
                                    target_collection_id: Optional[str] = None,
                                    replace_original: bool = True) -> List[IntegrationResult]:
    """
    FIXED main function to integrate PDFs with Zotero using correct PyZotero methods.
    
    Args:
        download_results: Results from PDF download process
        zotero_manager: Zotero manager instance
        mode: Integration mode ('download_only', 'attach') # REMOVED upload_replace
        target_collection_id: Collection ID (deprecated for upload mode)
        replace_original: Whether to replace records (deprecated)
    
    Returns:
        List of integration results
    """
    # UPDATED: Remove upload_replace from available modes
    mode_map = {
        'download_only': IntegrationMode.DOWNLOAD_ONLY,
        'attach': IntegrationMode.ATTACH_TO_EXISTING,
    }
    
    if mode not in mode_map:
        raise ValueError(f"Invalid mode: {mode}. Must be one of {list(mode_map.keys())}")
    
    # Create configuration
    config = IntegrationConfig(
        mode=mode_map[mode],
        target_collection_id=target_collection_id,
        replace_original=replace_original
    )
    
    # Create FIXED integrator and process
    if mode == 'download_only':
        # For download-only mode, we don't need the zotero_manager
        integrator = FixedZoteroPDFIntegrator(None, config)
    else:
        integrator = FixedZoteroPDFIntegrator(zotero_manager, config)
    
    return integrator.process_download_results(download_results)

# UPDATED: Example usage configurations (removed upload_replace)
FIXED_EXAMPLE_CONFIGS = {
    'download_only': {
        'description': 'Just download PDFs locally, no Zotero integration',
        'usage': "integrate_pdfs_with_zotero_fixed(results, None, mode='download_only')",
        'note': 'PDFs remain in local folder only'
    },
    'attach': {
        'description': 'Attach PDFs to existing Zotero records using FIXED attachment_simple',
        'usage': "integrate_pdfs_with_zotero_fixed(results, zotero_manager, mode='attach')",
        'note': 'Adds PDF as attachment to existing record, preserves original metadata'
    },
    # REMOVED: upload_replace configuration - disabled due to API limitations
}

# Quick setup functions for available modes only
def setup_download_only_mode():
    """Set up download-only integration mode."""
    return IntegrationConfig(mode=IntegrationMode.DOWNLOAD_ONLY)

def setup_attach_mode():
    """Set up attach-to-existing integration mode."""
    return IntegrationConfig(mode=IntegrationMode.ATTACH_TO_EXISTING)

# DISABLED: upload_replace setup function
# def setup_upload_replace_mode(target_collection_id: str, 
#                              replace_original: bool = True,
#                              preserve_tags: bool = True,
#                              preserve_notes: bool = True,
#                              preserve_collections: bool = True):
#     """DISABLED: upload_replace mode has been disabled due to API limitations."""
#     raise NotImplementedError(
#         "upload_replace mode has been disabled due to Zotero API limitations. "
#         "Use 'attach' mode instead for reliable PDF integration."
#     )

# Compatibility functions for easy migration (updated)
def create_download_only_integrator():
    """Create integrator for download-only mode (compatibility function)."""
    return setup_download_only_mode()

def create_attach_integrator(zotero_manager):
    """Create integrator for attach-to-existing mode (compatibility function)."""
    config = setup_attach_mode()
    return FixedZoteroPDFIntegrator(zotero_manager, config)

# DISABLED: upload_replace integrator
# def create_upload_replace_integrator(zotero_manager, target_collection_id: str, replace_original: bool = True):
#     """DISABLED: upload_replace mode has been disabled."""
#     raise NotImplementedError(
#         "upload_replace mode has been disabled due to API limitations. "
#         "Use 'attach' mode instead."
#     )

# Mode validation and information (updated)
def get_available_modes():
    """Get list of available integration modes."""
    return ['download_only', 'attach']  # Removed upload_replace

def get_mode_info(mode: str):
    """Get information about a specific integration mode."""
    if mode == 'upload_replace':
        raise ValueError(
            "upload_replace mode has been disabled due to Zotero API limitations. "
            "Use 'attach' mode instead for reliable PDF integration."
        )
    
    if mode in FIXED_EXAMPLE_CONFIGS:
        return FIXED_EXAMPLE_CONFIGS[mode]
    else:
        available = get_available_modes()
        raise ValueError(f"Unknown mode: {mode}. Available modes: {available}")

def print_mode_help():
    """Print help information about available modes."""
    print("🔧 FIXED ZOTERO PDF INTEGRATION MODES")
    print("=" * 50)
    
    for mode_name, mode_info in FIXED_EXAMPLE_CONFIGS.items():
        print(f"\n📋 Mode: {mode_name}")
        print(f"   Description: {mode_info['description']}")
        print(f"   Usage: {mode_info['usage']}")
        print(f"   Note: {mode_info['note']}")
    
    print(f"\n❌ Disabled Mode: upload_replace")
    print(f"   Reason: Zotero API field validation issues")
    print(f"   Alternative: Use 'attach' mode for reliable integration")
    
    print(f"\n💡 Quick Start Examples:")
    print(f"   # Download only (no Zotero integration)")
    print(f"   results = integrate_pdfs_with_zotero_fixed(downloads, None, 'download_only')")
    print(f"   ")
    print(f"   # Attach to existing records (recommended)")
    print(f"   results = integrate_pdfs_with_zotero_fixed(downloads, zotero_mgr, 'attach')")

# Test function for this part
def test_part6():
    """Test that Part 6 works correctly."""
    print("🧪 Testing Part 6: Main Integration Function...")
    
    # Test that functions exist and are callable
    assert callable(integrate_pdfs_with_zotero_fixed)
    assert callable(setup_download_only_mode)
    assert callable(setup_attach_mode)
    
    # Test mode mapping
    available_modes = get_available_modes()
    assert 'download_only' in available_modes
    assert 'attach' in available_modes
    assert 'upload_replace' not in available_modes  # Should be disabled
    
    # Test configuration creation
    config1 = setup_download_only_mode()
    assert config1.mode == IntegrationMode.DOWNLOAD_ONLY
    
    config2 = setup_attach_mode()
    assert config2.mode == IntegrationMode.ATTACH_TO_EXISTING
    
    # Test that upload_replace is properly disabled
    try:
        get_mode_info('upload_replace')
        assert False, "upload_replace should raise an error"
    except ValueError as e:
        assert "disabled" in str(e).lower()
    
    print("✅ Part 6 test passed!")
    return True

if __name__ == "__main__":
    test_part6()