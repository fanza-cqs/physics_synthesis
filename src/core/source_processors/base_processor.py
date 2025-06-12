#!/usr/bin/env python3
"""
Base source processor for Knowledge Base Orchestrator.

Defines the interface and common functionality for all source processors.

Location: src/core/source_processors/base_processor.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from ...utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class SourceScanResult:
    """Result of scanning a source for available documents."""
    success: bool
    document_counts: Dict[str, int] = None
    total_documents: int = 0
    error_message: Optional[str] = None
    additional_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.document_counts is None:
            self.document_counts = {}
        if self.additional_info is None:
            self.additional_info = {}

@dataclass 
class SourceProcessingResult:
    """Result of processing documents from a source."""
    success: bool
    documents_added: int = 0
    documents_failed: int = 0
    chunks_created: int = 0
    error_message: Optional[str] = None
    processing_details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.processing_details is None:
            self.processing_details = {}

class BaseSourceProcessor(ABC):
    """
    Abstract base class for source processors.
    
    Each source processor handles scanning and processing documents
    from a specific type of source (local folders, Zotero, etc.).
    """
    
    def __init__(self, config):
        """
        Initialize the source processor.
        
        Args:
            config: PipelineConfig instance
        """
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
    
    @abstractmethod
    def scan_sources(self, source_selection) -> SourceScanResult:
        """
        Scan the source for available documents without processing them.
        
        Args:
            source_selection: SourceSelection configuration
            
        Returns:
            SourceScanResult with document counts and information
        """
        pass
    
    @abstractmethod
    def process_source(self, knowledge_base, source_selection) -> SourceProcessingResult:
        """
        Process documents from the source and add them to the knowledge base.
        
        Args:
            knowledge_base: KnowledgeBase instance to add documents to
            source_selection: SourceSelection configuration
            
        Returns:
            SourceProcessingResult with processing details
        """
        pass
    
    def _count_documents_in_directory(self, 
                                     directory: Path, 
                                     extensions: set = None) -> int:
        """
        Count documents in a directory with supported extensions.
        
        Args:
            directory: Directory to scan
            extensions: Set of extensions to count (default: PDF, TEX, TXT)
            
        Returns:
            Number of documents found
        """
        if not directory or not directory.exists():
            return 0
        
        if extensions is None:
            extensions = {'.pdf', '.tex', '.txt'}
        
        try:
            count = 0
            for file_path in directory.rglob("*"):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in extensions):
                    count += 1
            return count
        except Exception as e:
            self.logger.warning(f"Error counting documents in {directory}: {e}")
            return 0
    
    def _validate_directory(self, directory: Path, name: str) -> bool:
        """
        Validate that a directory exists and is accessible.
        
        Args:
            directory: Directory path to validate
            name: Human-readable name for error messages
            
        Returns:
            True if directory is valid and accessible
        """
        if not directory:
            self.logger.warning(f"{name} directory is None")
            return False
        
        if not directory.exists():
            self.logger.warning(f"{name} directory does not exist: {directory}")
            return False
        
        if not directory.is_dir():
            self.logger.warning(f"{name} path is not a directory: {directory}")
            return False
        
        try:
            # Test read access
            list(directory.iterdir())
            return True
        except PermissionError:
            self.logger.error(f"No read permission for {name} directory: {directory}")
            return False
        except Exception as e:
            self.logger.error(f"Error accessing {name} directory {directory}: {e}")
            return False