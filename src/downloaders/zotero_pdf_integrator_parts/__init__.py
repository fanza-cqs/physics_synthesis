# Fixed Zotero PDF Integration System - Parts Package
# File: src/downloaders/zotero_pdf_integrator_parts/__init__.py

"""
Modular parts for the Fixed Zotero PDF Integration System.

This package contains the individual components that are assembled
into the complete integration system.
"""

# Individual parts can be imported if needed
from .part1_core_classes import IntegrationMode, IntegrationConfig, IntegrationResult
from .part2_main_class import FixedZoteroPDFIntegrator
from .part6_main_function import integrate_pdfs_with_zotero_fixed

__all__ = [
    'IntegrationMode',
    'IntegrationConfig', 
    'IntegrationResult',
    'FixedZoteroPDFIntegrator',
    'integrate_pdfs_with_zotero_fixed'
]
