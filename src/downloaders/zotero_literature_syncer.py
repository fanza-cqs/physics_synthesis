#!/usr/bin/env python3
"""
Zotero Literature Syncer for the Physics Literature Synthesis Pipeline.

Replaces the BibTeX-based literature downloader with direct Zotero integration.
Provides seamless synchronization between Zotero libraries and the knowledge base.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass

from .zotero_manager import ZoteroLibraryManager, ZoteroItem, SyncResult
from ..core.knowledge_base import KnowledgeBase
from ..core.document_processor import ProcessedDocument
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class LiteratureSyncResult:
    """Result of literature synchronization operation."""
    zotero_items_found: int
    files_downloaded: int
    documents_processed: int
    knowledge_base_updated: bool
    processing_time: float
    errors: List[str]

class ZoteroLiteratureSyncer:
    """
    Comprehensive literature synchronization using Zotero integration.
    
    Replaces the BibTeX-based approach with direct Zotero Web API integration,
    providing seamless literature management and knowledge base building.
    """
    
    def __init__(self,
                 zotero_config: Dict[str, Any],
                 knowledge_base: Optional[KnowledgeBase] = None,
                 auto_build_kb: bool = True):
        """
        Initialize Zotero literature syncer.
        
        Args:
            zotero_config: Dictionary with Zotero configuration
            knowledge_base: Optional existing KnowledgeBase instance
            auto_build_kb: Whether to automatically update knowledge base
        """
        # Initialize Zotero manager
        self.zotero_manager = ZoteroLibraryManager(
            library_id=zotero_config['library_id'],
            library_type=zotero_config['library_type'],
            api_key=zotero_config['api_key'],
            output_directory=Path(zotero_config['output_directory'])
        )
        
        # Initialize or use provided knowledge base
        self.knowledge_base = knowledge_base
        self.auto_build_kb = auto_build_kb
        
        # Sync configuration
        self.download_attachments = zotero_config.get('download_attachments', True)
        self.file_types = zotero_config.get('file_types', {'application/pdf'})
        self.overwrite_files = zotero_config.get('overwrite_files', False)
        self.sync_collections = zotero_config.get('sync_collections', None)
        
        logger.info("Zotero literature syncer initialized")
    
    def test_zotero_connection(self) -> Dict[str, Any]:
        """
        Test connection to Zotero and get library information.
        
        Returns:
            Dictionary with connection status and library info
        """
        logger.info("Testing Zotero connection...")
        return self.zotero_manager.test_connection()
    
    def sync_literature(self, 
                       update_knowledge_base: bool = None,
                       collections: List[str] = None) -> LiteratureSyncResult:
        """
        Perform complete literature synchronization from Zotero.
        
        Args:
            update_knowledge_base: Whether to update the knowledge base
            collections: Specific collections to sync (overrides config)
        
        Returns:
            LiteratureSyncResult with sync statistics
        """
        start_time = time.time()
        logger.info("Starting Zotero literature synchronization...")
        
        if update_knowledge_base is None:
            update_knowledge_base = self.auto_build_kb
        
        # Use provided collections or fall back to config
        sync_collections = collections or self.sync_collections
        
        errors = []
        
        try:
            # Step 1: Sync Zotero library (download files)
            logger.info("Step 1: Synchronizing Zotero library...")
            zotero_sync_result = self.zotero_manager.sync_library(
                download_attachments=self.download_attachments,
                file_types=self.file_types,
                collections=sync_collections,
                overwrite_files=self.overwrite_files
            )
            
            # Step 2: Get all synced items
            logger.info("Step 2: Retrieving synchronized items...")
            zotero_items = self.zotero_manager.get_all_items(
                collections=sync_collections
            )
            
            # Step 3: Update knowledge base if requested
            documents_processed = 0
            knowledge_base_updated = False
            
            if update_knowledge_base and self.knowledge_base:
                logger.info("Step 3: Updating knowledge base...")
                
                # Process downloaded files and add to knowledge base
                documents_processed = self._update_knowledge_base_from_zotero(zotero_items)
                knowledge_base_updated = True
                
                logger.info(f"Knowledge base updated with {documents_processed} documents")
            
            processing_time = time.time() - start_time
            
            result = LiteratureSyncResult(
                zotero_items_found=len(zotero_items),
                files_downloaded=zotero_sync_result.files_downloaded,
                documents_processed=documents_processed,
                knowledge_base_updated=knowledge_base_updated,
                processing_time=processing_time,
                errors=errors + zotero_sync_result.errors
            )
            
            logger.info(f"Literature synchronization complete: "
                       f"{result.zotero_items_found} items, "
                       f"{result.files_downloaded} files downloaded, "
                       f"{result.documents_processed} documents processed "
                       f"in {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during literature synchronization: {e}")
            errors.append(f"Sync error: {e}")
            
            return LiteratureSyncResult(
                zotero_items_found=0,
                files_downloaded=0,
                documents_processed=0,
                knowledge_base_updated=False,
                processing_time=time.time() - start_time,
                errors=errors
            )
    
    def sync_specific_collections(self, 
                                 collection_names: List[str]) -> LiteratureSyncResult:
        """
        Sync specific collections by name.
        
        Args:
            collection_names: List of collection names to sync
        
        Returns:
            LiteratureSyncResult
        """
        # Get all collections and find matching IDs
        all_collections = self.zotero_manager.get_collections()
        
        collection_ids = []
        for collection in all_collections:
            if collection['name'] in collection_names:
                collection_ids.append(collection['key'])
        
        if not collection_ids:
            logger.warning(f"No collections found matching: {collection_names}")
            return LiteratureSyncResult(
                zotero_items_found=0,
                files_downloaded=0,
                documents_processed=0,
                knowledge_base_updated=False,
                processing_time=0.0,
                errors=[f"No collections found matching: {collection_names}"]
            )
        
        logger.info(f"Syncing collections: {collection_names} (IDs: {collection_ids})")
        return self.sync_literature(collections=collection_ids)
    
    def get_library_overview(self) -> Dict[str, Any]:
        """
        Get comprehensive overview of the Zotero library.
        
        Returns:
            Dictionary with library statistics and information
        """
        logger.info("Getting Zotero library overview...")
        
        try:
            # Test connection
            connection_info = self.zotero_manager.test_connection()
            
            # Get library stats
            library_stats = self.zotero_manager.get_library_stats()
            
            # Get collections info
            collections = self.zotero_manager.get_collections()
            
            # Find items with attachments
            items_with_pdfs = self.zotero_manager.find_items_with_attachments(
                content_types={'application/pdf'}
            )
            
            overview = {
                'connection_status': connection_info,
                'library_stats': library_stats,
                'collections': {
                    'total': len(collections),
                    'details': collections[:10]  # First 10 collections
                },
                'items_with_pdfs': len(items_with_pdfs),
                'sync_ready': connection_info.get('connected', False)
            }
            
            return overview
            
        except Exception as e:
            logger.error(f"Error getting library overview: {e}")
            return {
                'connection_status': {'connected': False, 'error': str(e)},
                'sync_ready': False
            }
    
    def export_zotero_to_bibtex(self, 
                               output_path: Path = None,
                               collections: List[str] = None) -> Path:
        """
        Export Zotero library to BibTeX format.
        
        Args:
            output_path: Path for output BibTeX file
            collections: Specific collections to export
        
        Returns:
            Path to created BibTeX file
        """
        logger.info("Exporting Zotero library to BibTeX...")
        
        # Get items to export
        if collections:
            items = self.zotero_manager.get_all_items(collections=collections)
        else:
            items = None  # Export all items
        
        return self.zotero_manager.export_items_to_bibtex(
            items=items,
            output_path=output_path
        )
    
    def find_physics_papers(self, 
                           physics_tags: List[str] = None,
                           physics_collections: List[str] = None) -> List[ZoteroItem]:
        """
        Find papers related to physics in the Zotero library.
        
        Args:
            physics_tags: List of physics-related tags to search for
            physics_collections: List of physics collection names
        
        Returns:
            List of physics-related ZoteroItem objects
        """
        if physics_tags is None:
            physics_tags = [
                'physics', 'quantum', 'condensed matter', 'statistical mechanics',
                'quantum mechanics', 'thermodynamics', 'optics', 'electromagnetism',
                'particle physics', 'astrophysics', 'cosmology', 'relativity'
            ]
        
        logger.info(f"Searching for physics papers with tags: {physics_tags}")
        
        # Get all items
        all_items = self.zotero_manager.get_all_items()
        
        physics_items = []
        for item in all_items:
            # Check for physics-related tags
            has_physics_tag = any(
                any(physics_tag.lower() in tag.lower() for physics_tag in physics_tags)
                for tag in item.tags
            )
            
            # Check for physics terms in title/abstract
            physics_terms_in_text = any(
                term.lower() in (item.title + ' ' + item.abstract).lower()
                for term in physics_tags
            )
            
            if has_physics_tag or physics_terms_in_text:
                physics_items.append(item)
        
        logger.info(f"Found {len(physics_items)} physics-related papers")
        return physics_items
    
    def _update_knowledge_base_from_zotero(self, 
                                         zotero_items: List[ZoteroItem]) -> int:
        """
        Update knowledge base with Zotero items and their attachments.
        
        Args:
            zotero_items: List of ZoteroItem objects with downloaded attachments
        
        Returns:
            Number of documents successfully processed
        """
        if not self.knowledge_base:
            logger.warning("No knowledge base provided, skipping KB update")
            return 0
        
        documents_processed = 0
        
        for item in zotero_items:
            try:
                # Process each attachment file
                for attachment in item.attachments:
                    local_path = attachment.get('local_path')
                    if local_path and Path(local_path).exists():
                        
                        # Create ProcessedDocument with rich metadata
                        content_path = Path(local_path)
                        
                        # Add document to knowledge base
                        success = self.knowledge_base.add_document(
                            content_path, 
                            source_type="zotero_literature"
                        )
                        
                        if success:
                            documents_processed += 1
                            logger.debug(f"Added to KB: {content_path.name}")
                        else:
                            logger.warning(f"Failed to add to KB: {content_path.name}")
                
            except Exception as e:
                logger.error(f"Error processing item {item.key} for KB: {e}")
        
        return documents_processed
    
    def create_enhanced_metadata(self, zotero_item: ZoteroItem) -> str:
        """
        Create enhanced metadata string for better embeddings.
        
        Args:
            zotero_item: ZoteroItem object
        
        Returns:
            Rich metadata string for embedding context
        """
        metadata_parts = []
        
        # Basic bibliographic info
        metadata_parts.append(f"Title: {zotero_item.title}")
        
        if zotero_item.authors:
            metadata_parts.append(f"Authors: {', '.join(zotero_item.authors)}")
        
        if zotero_item.journal:
            metadata_parts.append(f"Journal: {zotero_item.journal}")
        
        if zotero_item.year:
            metadata_parts.append(f"Year: {zotero_item.year}")
        
        if zotero_item.abstract:
            metadata_parts.append(f"Abstract: {zotero_item.abstract}")
        
        # Zotero-specific metadata
        if zotero_item.tags:
            metadata_parts.append(f"Tags: {', '.join(zotero_item.tags)}")
        
        if zotero_item.doi:
            metadata_parts.append(f"DOI: {zotero_item.doi}")
        
        metadata_parts.append(f"Item Type: {zotero_item.item_type}")
        metadata_parts.append(f"Zotero Key: {zotero_item.key}")
        
        return " | ".join(metadata_parts)
    
    def get_sync_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for optimizing literature synchronization.
        
        Returns:
            Dictionary with sync recommendations
        """
        try:
            library_stats = self.zotero_manager.get_library_stats()
            collections = self.zotero_manager.get_collections()
            items_with_pdfs = self.zotero_manager.find_items_with_attachments()
            
            recommendations = {
                'total_items': library_stats.get('total_items', 0),
                'items_with_pdfs': len(items_with_pdfs),
                'collections_available': len(collections),
                'recommendations': []
            }
            
            # Generate recommendations
            if recommendations['items_with_pdfs'] == 0:
                recommendations['recommendations'].append({
                    'type': 'warning',
                    'message': 'No PDF attachments found in Zotero library',
                    'suggestion': 'Consider adding PDF attachments to your Zotero items'
                })
            
            if recommendations['total_items'] > 1000:
                recommendations['recommendations'].append({
                    'type': 'info',
                    'message': f"Large library ({recommendations['total_items']} items)",
                    'suggestion': 'Consider syncing specific collections for faster processing'
                })
            
            if recommendations['collections_available'] > 0:
                recommendations['recommendations'].append({
                    'type': 'tip',
                    'message': f"{recommendations['collections_available']} collections available",
                    'suggestion': 'Use collection-based sync for targeted literature management'
                })
            
            # Physics-specific recommendations
            physics_items = self.find_physics_papers()
            if physics_items:
                recommendations['physics_items_found'] = len(physics_items)
                recommendations['recommendations'].append({
                    'type': 'success',
                    'message': f"Found {len(physics_items)} physics-related papers",
                    'suggestion': 'Consider creating a dedicated physics collection'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating sync recommendations: {e}")
            return {
                'error': str(e),
                'recommendations': [{
                    'type': 'error',
                    'message': 'Unable to analyze library',
                    'suggestion': 'Check Zotero connection and API permissions'
                }]
            }