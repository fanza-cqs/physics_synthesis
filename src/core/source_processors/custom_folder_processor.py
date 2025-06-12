#!/usr/bin/env python3
"""
Custom folder source processor for Knowledge Base Orchestrator.

Handles processing documents from user-selected custom folders.

Location: src/core/source_processors/custom_folder_processor.py
"""

from pathlib import Path
from typing import Dict

from .base_processor import BaseSourceProcessor, SourceScanResult, SourceProcessingResult
from ..knowledge_base import KnowledgeBase
from ..document_processor import DocumentProcessor

class CustomFolderProcessor(BaseSourceProcessor):
    """
    Processes documents from user-selected custom folders.
    
    Allows users to select any folder on their system to include
    in the knowledge base creation process.
    """
    
    def __init__(self, config):
        """Initialize custom folder processor."""
        super().__init__(config)
        self.document_processor = DocumentProcessor()
    
    def scan_sources(self, source_selection) -> SourceScanResult:
        """
        Scan custom folder for available documents.
        
        Args:
            source_selection: SourceSelection with custom folder configuration
            
        Returns:
            SourceScanResult with document counts
        """
        self.logger.info("Scanning custom folder for documents")
        
        result = SourceScanResult(success=True)
        
        try:
            custom_folder = source_selection.custom_folder_path
            
            if not custom_folder:
                result.success = False
                result.error_message = "No custom folder path provided"
                return result
            
            # Validate the custom folder
            if not self._validate_directory(custom_folder, 'custom folder'):
                result.success = False
                result.error_message = f"Invalid custom folder: {custom_folder}"
                return result
            
            # Count documents in the folder
            doc_count = self._count_documents_in_directory(custom_folder)
            result.document_counts['custom_folder'] = doc_count
            result.total_documents = doc_count
            
            # Store additional information
            result.additional_info['folder_path'] = str(custom_folder)
            result.additional_info['folder_name'] = custom_folder.name
            
            self.logger.info(f"Custom folder scan complete: {doc_count} documents found in {custom_folder}")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Error scanning custom folder: {str(e)}"
            self.logger.error(f"Error during custom folder scan: {e}")
        
        return result
    
    def process_source(self, knowledge_base: KnowledgeBase, source_selection) -> SourceProcessingResult:
        """
        Process documents from custom folder and add to knowledge base.
        
        Args:
            knowledge_base: KnowledgeBase to add documents to
            source_selection: SourceSelection with custom folder configuration
            
        Returns:
            SourceProcessingResult with processing details
        """
        self.logger.info("Processing documents from custom folder")
        
        result = SourceProcessingResult(success=True)
        
        try:
            custom_folder = source_selection.custom_folder_path
            
            if not custom_folder:
                result.success = False
                result.error_message = "No custom folder path provided"
                return result
            
            # Validate the custom folder
            if not self._validate_directory(custom_folder, 'custom folder'):
                result.success = False
                result.error_message = f"Invalid custom folder: {custom_folder}"
                return result
            
            # Process documents in the folder
            docs_before = len(knowledge_base.processed_documents)
            
            # Process all documents in the custom folder
            processed_docs = self.document_processor.process_directory(
                custom_folder, 
                source_type="custom_folder"
            )
            
            if not processed_docs:
                result.success = False
                result.error_message = "No documents could be processed from custom folder"
                return result
            
            # Add documents to knowledge base
            successful_docs = [doc for doc in processed_docs if doc.processing_success]
            failed_docs = [doc for doc in processed_docs if not doc.processing_success]
            
            # Add to knowledge base processed documents
            knowledge_base.processed_documents.extend(processed_docs)
            
            # Add to embeddings manager
            if successful_docs:
                knowledge_base.embeddings_manager.add_documents(successful_docs)
            
            # Update knowledge base config
            knowledge_base.config['last_updated'] = knowledge_base.embeddings_manager.get_statistics().get('last_updated', 0)
            
            # Calculate results
            result.documents_added = len(successful_docs)
            result.documents_failed = len(failed_docs)
            
            # Get chunk count (approximate - would need to sum chunks for these docs)
            if successful_docs:
                # Estimate chunks created (this is approximate)
                total_words = sum(doc.word_count for doc in successful_docs)
                estimated_chunks = max(1, total_words // knowledge_base.embeddings_manager.chunk_size)
                result.chunks_created = estimated_chunks
            
            # Store processing details
            result.processing_details = {
                'folder_processed': str(custom_folder),
                'total_files_found': len(processed_docs),
                'successful_processing': len(successful_docs),
                'failed_processing': len(failed_docs),
                'file_types_processed': self._get_file_type_breakdown(processed_docs)
            }
            
            self.logger.info(f"Custom folder processing complete: {result.documents_added} documents added, {result.documents_failed} failed")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Error processing custom folder: {str(e)}"
            self.logger.error(f"Error during custom folder processing: {e}")
        
        return result
    
    def _get_file_type_breakdown(self, processed_docs) -> Dict[str, int]:
        """Get breakdown of file types processed."""
        breakdown = {}
        for doc in processed_docs:
            file_path = Path(doc.file_path)
            extension = file_path.suffix.lower()
            breakdown[extension] = breakdown.get(extension, 0) + 1
        return breakdown