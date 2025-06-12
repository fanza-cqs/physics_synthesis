#!/usr/bin/env python3
"""
Zotero source processor for Knowledge Base Orchestrator.

Handles processing documents from Zotero collections.

Location: src/core/source_processors/zotero_processor.py
"""

from pathlib import Path
from typing import Dict, List

from .base_processor import BaseSourceProcessor, SourceScanResult, SourceProcessingResult
from ..knowledge_base import KnowledgeBase
from ...downloaders import create_literature_syncer

class ZoteroProcessor(BaseSourceProcessor):
    """
    Processes documents from Zotero collections.
    
    Leverages existing Zotero sync functionality and processes
    documents from the zotero_sync folder.
    """
    
    def __init__(self, config):
        """Initialize Zotero processor."""
        super().__init__(config)
        self._syncer = None
    
    def _get_syncer(self):
        """Get or create literature syncer instance."""
        if self._syncer is None:
            try:
                self._syncer = create_literature_syncer(self.config)
            except Exception as e:
                self.logger.error(f"Failed to create literature syncer: {e}")
                return None
        return self._syncer
    
    def scan_sources(self, source_selection) -> SourceScanResult:
        """
        Scan Zotero collections for available documents.
        
        Args:
            source_selection: SourceSelection with Zotero configuration
            
        Returns:
            SourceScanResult with document counts per collection
        """
        self.logger.info("Scanning Zotero collections for documents")
        
        result = SourceScanResult(success=True)
        
        try:
            syncer = self._get_syncer()
            if not syncer:
                result.success = False
                result.error_message = "Zotero syncer not available"
                return result
            
            # Get available collections
            try:
                all_collections = syncer.zotero_manager.get_collections()
            except Exception as e:
                result.success = False
                result.error_message = f"Failed to fetch Zotero collections: {str(e)}"
                return result
            
            # Filter to selected collections
            selected_collections = []
            if source_selection.zotero_collections:
                collection_dict = {coll['name']: coll for coll in all_collections}
                for coll_name in source_selection.zotero_collections:
                    if coll_name in collection_dict:
                        selected_collections.append(collection_dict[coll_name])
                    else:
                        self.logger.warning(f"Collection '{coll_name}' not found in Zotero")
            
            # Count documents in each collection
            for collection in selected_collections:
                coll_name = collection['name']
                item_count = collection.get('num_items', 0)
                result.document_counts[coll_name] = item_count
                result.total_documents += item_count
                self.logger.debug(f"Collection '{coll_name}': {item_count} items")
            
            # Also check for already synced files in zotero_sync folder
            if self.config.zotero_sync_folder.exists():
                synced_docs = self._count_documents_in_directory(self.config.zotero_sync_folder)
                result.additional_info['synced_documents'] = synced_docs
                self.logger.debug(f"Found {synced_docs} already synced documents")
            
            result.additional_info['collections_available'] = len(all_collections)
            result.additional_info['collections_selected'] = len(selected_collections)
            
            self.logger.info(f"Zotero scan complete: {result.total_documents} documents in {len(selected_collections)} collections")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Error scanning Zotero collections: {str(e)}"
            self.logger.error(f"Error during Zotero scan: {e}")
        
        return result
    
    def process_source(self, knowledge_base: KnowledgeBase, source_selection) -> SourceProcessingResult:
        """
        Process documents from Zotero collections and add to knowledge base.
        
        Args:
            knowledge_base: KnowledgeBase to add documents to
            source_selection: SourceSelection with Zotero configuration
            
        Returns:
            SourceProcessingResult with processing details
        """
        self.logger.info("Processing documents from Zotero collections")
        
        result = SourceProcessingResult(success=True)
        
        try:
            syncer = self._get_syncer()
            if not syncer:
                result.success = False
                result.error_message = "Zotero syncer not available"
                return result
            
            if not source_selection.zotero_collections:
                result.success = False
                result.error_message = "No Zotero collections selected"
                return result
            
            # Get collection details
            all_collections = syncer.zotero_manager.get_collections()
            collection_dict = {coll['name']: coll for coll in all_collections}
            
            selected_collections = []
            for coll_name in source_selection.zotero_collections:
                if coll_name in collection_dict:
                    selected_collections.append(collection_dict[coll_name])
            
            if not selected_collections:
                result.success = False
                result.error_message = "Selected Zotero collections not found"
                return result
            
            # Sync collections (reuse existing logic from quick_start_rag.py)
            sync_successful = self._sync_collections(selected_collections, syncer)
            
            if not sync_successful:
                result.success = False
                result.error_message = "Failed to sync Zotero collections"
                return result
            
            # Process synced documents by building KB from zotero_sync folder
            # Count documents before processing
            docs_before = len(knowledge_base.processed_documents)
            
            # Build from zotero sync folder
            stats = knowledge_base.build_from_directories(
                zotero_folder=self.config.zotero_sync_folder,
                force_rebuild=False  # We're adding to existing KB
            )
            
            # Calculate what was added
            docs_after = len(knowledge_base.processed_documents)
            result.documents_added = docs_after - docs_before
            result.chunks_created = stats.get('total_chunks', 0) - result.chunks_created if hasattr(result, 'chunks_created') else stats.get('total_chunks', 0)
            
            # Store processing details
            result.processing_details = {
                'collections_processed': [coll['name'] for coll in selected_collections],
                'kb_stats': stats,
                'sync_folder': str(self.config.zotero_sync_folder)
            }
            
            self.logger.info(f"Zotero processing complete: {result.documents_added} documents added from {len(selected_collections)} collections")
            
        except Exception as e:
            result.success = False
            result.error_message = f"Error processing Zotero collections: {str(e)}"
            self.logger.error(f"Error during Zotero processing: {e}")
        
        return result
    
    def _sync_collections(self, selected_collections: List[Dict], syncer) -> bool:
        """
        Sync selected Zotero collections to local storage.
        
        This reuses the existing logic from quick_start_rag.py
        """
        try:
            self.logger.info(f"Syncing {len(selected_collections)} Zotero collections")
            
            for collection in selected_collections:
                coll_name = collection['name']
                self.logger.info(f"Syncing collection: {coll_name}")
                
                # Use the existing enhanced sync method
                result = syncer.sync_collection_with_doi_downloads_and_integration(
                    collection_name=coll_name,
                    max_doi_downloads=15,  # Reasonable default
                    update_knowledge_base=False,  # We handle KB building separately
                    headless=True,
                    integration_mode="download_only"  # Just download, don't modify Zotero
                )
                
                # Check if sync was successful
                zotero_result = result.zotero_sync_result
                if zotero_result.total_items > 0:
                    self.logger.info(f"Successfully synced {zotero_result.total_items} items from {coll_name}")
                else:
                    self.logger.warning(f"No items synced from collection {coll_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error syncing Zotero collections: {e}")
            return False