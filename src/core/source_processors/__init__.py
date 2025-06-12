#!/usr/bin/env python3
"""
Source processors package for Knowledge Base Orchestrator.

Location: src/core/source_processors/__init__.py
"""

from .base_processor import BaseSourceProcessor, SourceProcessingResult, SourceScanResult
from .local_folder_processor import LocalFolderProcessor
from .zotero_processor import ZoteroProcessor
from .custom_folder_processor import CustomFolderProcessor

__all__ = [
    'BaseSourceProcessor',
    'SourceProcessingResult', 
    'SourceScanResult',
    'LocalFolderProcessor',
    'ZoteroProcessor',
    'CustomFolderProcessor'
]