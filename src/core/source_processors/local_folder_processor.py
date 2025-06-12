#!/usr/bin/env python3
"""
Local folder source processor for Knowledge Base Orchestrator.

Handles processing documents from predefined local folders.

Location: src/core/source_processors/local_folder_processor.py
"""

from pathlib import Path
from typing import Dict, Optional

from .base_processor import BaseSourceProcessor, SourceScanResult, SourceProcessingResult
from ..knowledge_base import KnowledgeBase

class LocalFolderProcessor(BaseSourceProcessor):
    """
    Processes documents from predefined local folders.
    
    Handles literature, your_work, current_drafts, and manual_references folders
    based on the source selection configuration.
    """
    
    def scan_sources(self, source_selection) -> SourceScanResult:
        """
        Scan local folders for available documents.
        
        Args:
            source_selection: SourceSelection with local folder configuration
            
        Returns:
            SourceScanResult with document counts per folder
        """
        self.logger.info("Scanning local folders for documents")
        
        result = SourceScanResult(success=True)
        
        try:
            # Get folder configurations
            folders_to_scan = self._get_folders_to_scan(source_selection)
            
            # Scan each folder
            for folder_name, folder_path in folders_to_scan.items():
                if self._validate_directory(folder_path, folder_name):
                    doc_count = self._count_documents_in_directory(folder_path)
                    result.document_counts[folder_name] = doc_count
                    result.total_documents += doc_count
                    self.logger.debug(f"Found {doc_count} documents in {folder_name}")
                else:
                    result.document_counts[folder_name] = 0
                    if result.error_message is None:
                        result.error_message = f"Invalid folder: {folder_name}"
                    else:
                        result.error_message += f", {folder_name}"
            
            # Add folder paths to additional info
            result.additional_info['folder_paths'] = {
                name: str(path) for name, path in folders_to_scan.items()
            }
            
            self.logger.info(f"Local folder scan complete: {result.total_documents} documents found")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Error scanning local folders: {str(e)}"
            self.logger.error(f"Error during local folder scan: {e}")
        
        return result
    
    def process_source(self, knowledge_base: KnowledgeBase, source_selection) -> SourceProcessingResult:
        """
        Process documents from local folders and add to knowledge base.
        
        Args:
            knowledge_base: KnowledgeBase to add documents to
            source_selection: SourceSelection with local folder configuration
            
        Returns:
            SourceProcessingResult with processing details
        """
        self.logger.info("Processing documents from local folders")
        
        result = SourceProcessingResult(success=True)
        
        try:
            # Get folders to process
            folders_to_process = self._get_folders_to_process(source_selection)
            
            if not folders_to_process:
                result.success = False
                result.error_message = "No valid local folders to process"
                return result
            
            # Build knowledge base from directories
            # Note: This reuses the existing tested logic from KnowledgeBase
            stats = knowledge_base.build_from_directories(
                literature_folder=folders_to_process.get('literature'),
                your_work_folder=folders_to_process.get('your_work'),
                current_drafts_folder=folders_to_process.get('current_drafts'),
                manual_references_folder=folders_to_process.get('manual_references'),
                force_rebuild=False  # We're adding to existing KB
            )
            
            # Extract results from stats
            result.documents_added = stats.get('successful_documents', 0)
            result.documents_failed = stats.get('failed_documents', 0)
            result.chunks_created = stats.get('total_chunks', 0)
            
            # Store processing details
            result.processing_details = {
                'folders_processed': list(folders_to_process.keys()),
                'kb_stats': stats
            }
            
            self.logger.info(f"Local folder processing complete: {result.documents_added} documents added")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Error processing local folders: {str(e)}"
            self.logger.error(f"Error during local folder processing: {e}")
        
        return result
    
    def _get_folders_to_scan(self, source_selection) -> Dict[str, Path]:
        """Get dictionary of folder names to paths for scanning."""
        folders = {}
        
        if source_selection.literature_folder:
            folders['literature'] = self.config.literature_folder
        
        if source_selection.your_work_folder:
            folders['your_work'] = self.config.your_work_folder
        
        if source_selection.current_drafts_folder:
            folders['current_drafts'] = self.config.current_drafts_folder
        
        if source_selection.manual_references_folder:
            folders['manual_references'] = self.config.manual_references_folder
        
        return folders
    
    def _get_folders_to_process(self, source_selection) -> Dict[str, Optional[Path]]:
        """Get dictionary of folder types to paths for processing (None if not selected)."""
        folders = {}
        
        # Only include folders that are selected and valid
        if source_selection.literature_folder and self._validate_directory(self.config.literature_folder, 'literature'):
            folders['literature'] = self.config.literature_folder
        
        if source_selection.your_work_folder and self._validate_directory(self.config.your_work_folder, 'your_work'):
            folders['your_work'] = self.config.your_work_folder
        
        if source_selection.current_drafts_folder and self._validate_directory(self.config.current_drafts_folder, 'current_drafts'):
            folders['current_drafts'] = self.config.current_drafts_folder
        
        if source_selection.manual_references_folder and self._validate_directory(self.config.manual_references_folder, 'manual_references'):
            folders['manual_references'] = self.config.manual_references_folder
        
        return folders