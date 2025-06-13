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
    get_available_modes,
    get_mode_info,
    print_mode_help,
    create_download_only_integrator,
    create_attach_integrator,
)

# Assembly function to attach methods to the main class
def _assemble_modular_methods():
    """Attach all modular methods to the main integrator class."""
    
    # Attach mode implementation methods (only available ones)
    FixedZoteroPDFIntegrator._mode1_download_only = mode1_download_only
    FixedZoteroPDFIntegrator._mode2_attach_to_existing_fixed = mode2_attach_to_existing_fixed
    
    # Attach attachment methods
    FixedZoteroPDFIntegrator._create_attachment_correct_method = create_attachment_correct_method
    FixedZoteroPDFIntegrator._upload_pdf_to_collection_fixed = upload_pdf_to_collection_fixed
    
    # Attach upload and replace methods (keep for potential future use, but not exposed)
    FixedZoteroPDFIntegrator._upload_pdf_to_collection_with_metadata_extraction = upload_pdf_to_collection_with_metadata_extraction
    FixedZoteroPDFIntegrator._replace_record_with_preservation = replace_record_with_preservation

# Perform assembly when module is imported
_assemble_modular_methods()


# Export everything for easy import
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
    'get_available_modes',
    'get_mode_info',
    'print_mode_help',
    
    # Compatibility functions (only available ones)
    'create_download_only_integrator',
    'create_attach_integrator', 
    
    # Example configs
    'FIXED_EXAMPLE_CONFIGS',
]

