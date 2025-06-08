#!/usr/bin/env python3
"""
Fixed Zotero PDF Integration System - Main Assembly File

This file assembles all the modular parts into a complete integration system.
upload_replace mode has been disabled due to API limitations.
"""

# Core imports
from pathlib import Path
from typing import Dict, List, Optional

# Import all parts
from .zotero_pdf_integrator_parts.part1_core_classes import (
    IntegrationMode, 
    IntegrationConfig, 
    IntegrationResult
)

from .zotero_pdf_integrator_parts.part2_main_class import (
    FixedZoteroPDFIntegrator
)

from .zotero_pdf_integrator_parts.part3_mode_implementations import (
    mode1_download_only,
    mode2_attach_to_existing_fixed,
    # mode3_upload_and_replace_fixed  # DISABLED - commented out
)

from .zotero_pdf_integrator_parts.part4_attachment_methods import (
    create_attachment_correct_method,
    upload_pdf_to_collection_fixed
)

from .zotero_pdf_integrator_parts.part5_upload_replace_methods import (
    upload_pdf_to_collection_with_metadata_extraction,
    replace_record_with_preservation
)

from .zotero_pdf_integrator_parts.part6_main_function import (
    integrate_pdfs_with_zotero_fixed,
    FIXED_EXAMPLE_CONFIGS,
    setup_download_only_mode,
    setup_attach_mode,
    # setup_upload_replace_mode,  # DISABLED - removed
    get_available_modes,
    get_mode_info,
    print_mode_help,
    create_download_only_integrator,
    create_attach_integrator,
    # create_upload_replace_integrator  # DISABLED - removed
)

# Assembly function to attach methods to the main class
def _assemble_modular_methods():
    """Attach all modular methods to the main integrator class."""
    
    # Attach mode implementation methods (only available ones)
    FixedZoteroPDFIntegrator._mode1_download_only = mode1_download_only
    FixedZoteroPDFIntegrator._mode2_attach_to_existing_fixed = mode2_attach_to_existing_fixed
    # FixedZoteroPDFIntegrator._mode3_upload_and_replace_fixed = mode3_upload_and_replace_fixed  # DISABLED
    
    # Attach attachment methods
    FixedZoteroPDFIntegrator._create_attachment_correct_method = create_attachment_correct_method
    FixedZoteroPDFIntegrator._upload_pdf_to_collection_fixed = upload_pdf_to_collection_fixed
    
    # Attach upload and replace methods (keep for potential future use, but not exposed)
    FixedZoteroPDFIntegrator._upload_pdf_to_collection_with_metadata_extraction = upload_pdf_to_collection_with_metadata_extraction
    FixedZoteroPDFIntegrator._replace_record_with_preservation = replace_record_with_preservation

# Perform assembly when module is imported
_assemble_modular_methods()

def test_modular_assembly():
    """Test that the modular assembly works correctly."""
    print("🧪 Testing modular assembly...")
    
    # Test that core classes are available
    assert IntegrationMode.DOWNLOAD_ONLY.value == "download_only"
    print("   ✅ Core classes available")
    
    # Test that main class is available
    config = IntegrationConfig(mode=IntegrationMode.DOWNLOAD_ONLY)
    integrator = FixedZoteroPDFIntegrator(None, config)
    print("   ✅ Main integrator class available")
    
    # Test that required methods are attached (only reliable ones)
    required_methods = [
        '_mode1_download_only',
        '_mode2_attach_to_existing_fixed', 
        # '_mode3_upload_and_replace_fixed',  # DISABLED - removed from requirements
        '_create_attachment_correct_method',
        '_upload_pdf_to_collection_fixed',
        '_upload_pdf_to_collection_with_metadata_extraction',
        '_replace_record_with_preservation'
    ]
    
    for method_name in required_methods:
        assert hasattr(integrator, method_name), f"Missing method: {method_name}"
    
    print("   ✅ All required methods attached")
    
    # Test that main function is available
    assert callable(integrate_pdfs_with_zotero_fixed)
    print("   ✅ Main integration function available")
    
    # Test that only reliable modes are available
    available_modes = get_available_modes()
    assert 'download_only' in available_modes
    assert 'attach' in available_modes
    assert 'upload_replace' not in available_modes  # Should be disabled
    print(f"   ✅ Available modes: {available_modes}")
    
    print("🎉 Modular assembly test PASSED!")
    return True

# Export everything for easy import (updated to remove disabled components)
__all__ = [
    # Core classes
    'IntegrationMode',
    'IntegrationConfig', 
    'IntegrationResult',
    
    # Main class
    'FixedZoteroPDFIntegrator',
    
    # Main function
    'integrate_pdfs_with_zotero_fixed',
    
    # Configuration helpers (only available ones)
    'setup_download_only_mode',
    'setup_attach_mode', 
    # 'setup_upload_replace_mode',  # DISABLED - removed
    'get_available_modes',
    'get_mode_info',
    'print_mode_help',
    
    # Compatibility functions (only available ones)
    'create_download_only_integrator',
    'create_attach_integrator', 
    # 'create_upload_replace_integrator',  # DISABLED - removed
    
    # Example configs
    'FIXED_EXAMPLE_CONFIGS',
    
    # Test function
    'test_modular_assembly'
]

if __name__ == "__main__":
    # Run assembly test if file is executed directly
    test_modular_assembly()
    print("\n💡 Usage example:")
    print("from src.downloaders.zotero_pdf_integrator_fixed import integrate_pdfs_with_zotero_fixed")
    print("results = integrate_pdfs_with_zotero_fixed(download_data, zotero_manager, mode='attach')")
    print("\n📋 Available modes: download_only, attach")
    print("❌ Disabled modes: upload_replace (due to API limitations)")