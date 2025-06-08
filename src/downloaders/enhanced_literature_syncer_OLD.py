#!/usr/bin/env python3
"""
Enhanced Zotero Literature Syncer with DOI-based PDF downloading.

Provides high-level interface for syncing Zotero collections with automatic
PDF downloads for items that have DOIs but no attachments.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .enhanced_zotero_manager import EnhancedZoteroLibraryManager, CollectionSyncResult, SELENIUM_AVAILABLE
from ..core.knowledge_base import KnowledgeBase
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class EnhancedSyncResult:
    """Result of enhanced literature synchronization with DOI downloads."""
    zotero_sync_result: CollectionSyncResult
    knowledge_base_updated: bool
    documents_processed: int
    total_processing_time: float
    errors: List[str]

class EnhancedZoteroLiteratureSyncer:
    """
    Enhanced literature syncer with DOI-based PDF downloading capabilities.
    
    Provides seamless integration between Zotero collections and knowledge base
    with automatic PDF acquisition for items missing attachments.
    """
    
    def __init__(self,
                 zotero_config: Dict[str, Any],
                 knowledge_base: Optional[KnowledgeBase] = None,
                 auto_build_kb: bool = True,
                 doi_downloads_enabled: bool = True):
        """
        Initialize enhanced literature syncer.
        
        Args:
            zotero_config: Zotero configuration dictionary
            knowledge_base: Optional KnowledgeBase instance
            auto_build_kb: Whether to automatically update knowledge base
            doi_downloads_enabled: Whether to enable DOI-based downloads
        """
        # Initialize enhanced Zotero manager
        self.zotero_manager = EnhancedZoteroLibraryManager(
            library_id=zotero_config['library_id'],
            library_type=zotero_config['library_type'],
            api_key=zotero_config['api_key'],
            output_directory=Path(zotero_config['output_directory']),
            doi_downloads_enabled=doi_downloads_enabled
        )
        
        # Configuration
        self.knowledge_base = knowledge_base
        self.auto_build_kb = auto_build_kb
        self.doi_downloads_enabled = doi_downloads_enabled and SELENIUM_AVAILABLE
        
        # Default DOI download settings
        self.max_doi_downloads_per_sync = 10  # Limit for safety
        self.browser_headless = True
        
        logger.info(f"Enhanced literature syncer initialized (DOI downloads: {self.doi_downloads_enabled})")
    
    def preview_collection_sync(self, collection_name: str) -> Dict[str, Any]:
        """
        Preview what would happen in a collection sync without actually doing it.
        
        Args:
            collection_name: Name of the Zotero collection
        
        Returns:
            Dictionary with sync preview information
        """
        logger.info(f"Previewing sync for collection: {collection_name}")
        
        try:
            # Find collection by name
            collections = self.zotero_manager.get_collections()
            target_collection = None
            
            for coll in collections:
                if coll['name'] == collection_name:
                    target_collection = coll
                    break
            
            if not target_collection:
                return {
                    'error': f"Collection '{collection_name}' not found",
                    'available_collections': [c['name'] for c in collections]
                }
            
            # Get sync summary
            summary = self.zotero_manager.get_collection_sync_summary_fast(target_collection['key'])
            
            if 'error' in summary:
                return summary
            
            # Add recommendations
            recommendations = []
            
            if summary['items_with_dois_no_pdfs'] > 0:
                if self.doi_downloads_enabled:
                    recommendations.append({
                        'type': 'success',
                        'message': f"Can attempt DOI downloads for {summary['items_with_dois_no_pdfs']} items",
                        'action': 'Will automatically download PDFs using browser automation'
                    })
                else:
                    recommendations.append({
                        'type': 'info',
                        'message': f"{summary['items_with_dois_no_pdfs']} items could benefit from DOI downloads",
                        'action': 'Enable DOI downloads to automatically acquire PDFs'
                    })
            
            if summary['items_without_dois'] > 0:
                recommendations.append({
                    'type': 'warning',
                    'message': f"{summary['items_without_dois']} items have no DOIs",
                    'action': 'Consider adding DOIs to these items in Zotero'
                })
            
            if summary['items_with_pdfs'] == summary['total_items']:
                recommendations.append({
                    'type': 'success',
                    'message': "All items already have PDF attachments",
                    'action': 'Ready for knowledge base integration'
                })
            
            summary.update({
                'collection_name': collection_name,
                'collection_key': target_collection['key'],
                'recommendations': recommendations,
                'doi_downloads_available': self.doi_downloads_enabled
            })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error previewing collection sync: {e}")
            return {'error': str(e)}
    
    def sync_collection_with_doi_downloads(self, 
                                         collection_name: str,
                                         max_doi_downloads: int = None,
                                         update_knowledge_base: bool = None,
                                         headless: bool = None) -> EnhancedSyncResult:
        """
        Sync a collection with automatic DOI-based PDF downloads.
        
        Args:
            collection_name: Name of the Zotero collection to sync
            max_doi_downloads: Maximum DOI downloads to attempt (None for default limit)
            update_knowledge_base: Whether to update KB (None for auto setting)
            headless: Run browser in headless mode (None for default)
        
        Returns:
            EnhancedSyncResult with comprehensive sync information
        """
        start_time = time.time()
        
        logger.info(f"Starting enhanced collection sync: {collection_name}")
        
        # Use defaults if not specified
        if max_doi_downloads is None:
            max_doi_downloads = self.max_doi_downloads_per_sync
        if update_knowledge_base is None:
            update_knowledge_base = self.auto_build_kb
        if headless is None:
            headless = self.browser_headless
        
        errors = []
        
        try:
            # Find collection
            collections = self.zotero_manager.get_collections()
            target_collection = None
            
            for coll in collections:
                if coll['name'] == collection_name:
                    target_collection = coll
                    break
            
            if not target_collection:
                available_collections = [c['name'] for c in collections]
                error_msg = f"Collection '{collection_name}' not found. Available: {available_collections}"
                logger.error(error_msg)
                
                return EnhancedSyncResult(
                    zotero_sync_result=CollectionSyncResult(
                        total_items=0,
                        items_with_existing_pdfs=0,
                        items_with_dois_no_pdfs=0,
                        doi_download_attempts=0,
                        successful_doi_downloads=0,
                        failed_doi_downloads=0,
                        processing_time=0.0,
                        downloaded_files=[],
                        errors=[error_msg]
                    ),
                    knowledge_base_updated=False,
                    documents_processed=0,
                    total_processing_time=time.time() - start_time,
                    errors=[error_msg]
                )
            
            # Perform Zotero sync with DOI downloads
            logger.info(f"Syncing collection: {target_collection['name']} (ID: {target_collection['key']})")
            
            zotero_sync_result = self.zotero_manager.sync_collection_with_doi_downloads_fast(
                collection_id=target_collection['key'],
                max_doi_downloads=max_doi_downloads,
                headless=headless
            )
            
            # Update knowledge base if requested
            documents_processed = 0
            knowledge_base_updated = False
            
            if update_knowledge_base and self.knowledge_base:
                logger.info("Updating knowledge base with synced content...")
                
                try:
                    # Add downloaded PDFs to knowledge base
                    for file_path in zotero_sync_result.downloaded_files:
                        success = self.knowledge_base.add_document(
                            Path(file_path), 
                            source_type="zotero_doi_downloads"
                        )
                        if success:
                            documents_processed += 1
                    
                    # Also add any existing Zotero PDFs from this collection
                    zotero_pdf_folder = self.zotero_manager.pdf_directory
                    if zotero_pdf_folder.exists():
                        for pdf_file in zotero_pdf_folder.glob("*.pdf"):
                            # Check if this PDF is recent (from this sync)
                            try:
                                success = self.knowledge_base.add_document(
                                    pdf_file, 
                                    source_type="zotero_literature"
                                )
                                if success:
                                    documents_processed += 1
                            except Exception as e:
                                logger.warning(f"Failed to add {pdf_file.name} to KB: {e}")
                    
                    knowledge_base_updated = True
                    logger.info(f"Added {documents_processed} documents to knowledge base")
                    
                except Exception as e:
                    error_msg = f"Error updating knowledge base: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            total_processing_time = time.time() - start_time
            
            result = EnhancedSyncResult(
                zotero_sync_result=zotero_sync_result,
                knowledge_base_updated=knowledge_base_updated,
                documents_processed=documents_processed,
                total_processing_time=total_processing_time,
                errors=errors + zotero_sync_result.errors
            )
            
            # Log comprehensive summary
            logger.info(f"Enhanced collection sync complete:")
            logger.info(f"  Collection: {collection_name}")
            logger.info(f"  Total items: {zotero_sync_result.total_items}")
            logger.info(f"  Items with existing PDFs: {zotero_sync_result.items_with_existing_pdfs}")
            logger.info(f"  DOI downloads attempted: {zotero_sync_result.doi_download_attempts}")
            logger.info(f"  DOI downloads successful: {zotero_sync_result.successful_doi_downloads}")
            logger.info(f"  KB documents processed: {documents_processed}")
            logger.info(f"  Total processing time: {total_processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Error during enhanced sync: {e}"
            errors.append(error_msg)
            logger.error(error_msg)
            
            return EnhancedSyncResult(
                zotero_sync_result=CollectionSyncResult(
                    total_items=0,
                    items_with_existing_pdfs=0,
                    items_with_dois_no_pdfs=0,
                    doi_download_attempts=0,
                    successful_doi_downloads=0,
                    failed_doi_downloads=0,
                    processing_time=0.0,
                    downloaded_files=[],
                    errors=errors
                ),
                knowledge_base_updated=False,
                documents_processed=0,
                total_processing_time=time.time() - start_time,
                errors=errors
            )
    
    def batch_sync_collections(self, 
                              collection_names: List[str],
                              max_doi_downloads_per_collection: int = 5) -> Dict[str, EnhancedSyncResult]:
        """
        Sync multiple collections with DOI downloads.
        
        Args:
            collection_names: List of collection names to sync
            max_doi_downloads_per_collection: Max DOI downloads per collection
        
        Returns:
            Dict mapping collection names to their sync results
        """
        logger.info(f"Starting batch sync for {len(collection_names)} collections")
        
        results = {}
        
        for i, collection_name in enumerate(collection_names, 1):
            logger.info(f"Processing collection {i}/{len(collection_names)}: {collection_name}")
            
            try:
                result = self.sync_collection_with_doi_downloads(
                    collection_name=collection_name,
                    max_doi_downloads=max_doi_downloads_per_collection,
                    headless=True  # Always headless for batch operations
                )
                results[collection_name] = result
                
                # Small delay between collections
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error syncing collection {collection_name}: {e}")
                results[collection_name] = None
        
        # Summary
        successful_syncs = sum(1 for r in results.values() if r is not None)
        total_doi_downloads = sum(
            r.zotero_sync_result.successful_doi_downloads 
            for r in results.values() 
            if r is not None
        )
        
        logger.info(f"Batch sync complete: {successful_syncs}/{len(collection_names)} successful, "
                   f"{total_doi_downloads} PDFs downloaded")
        
        return results
    
    def get_doi_downloads_summary(self) -> Dict[str, Any]:
        """
        Get summary of DOI downloads functionality and files.
        
        Returns:
            Dict with DOI downloads information
        """
        summary = {
            'doi_downloads_enabled': self.doi_downloads_enabled,
            'selenium_available': SELENIUM_AVAILABLE,
            'download_folder': str(self.zotero_manager.doi_downloads_folder),
            'downloaded_files': [],
            'total_files': 0,
            'total_size_mb': 0
        }
        
        if not SELENIUM_AVAILABLE:
            summary['error'] = 'Selenium not available - install with: pip install selenium'
            return summary
        
        # Get downloaded files
        downloaded_files = self.zotero_manager.list_doi_downloaded_files()
        summary['downloaded_files'] = downloaded_files
        summary['total_files'] = len(downloaded_files)
        summary['total_size_mb'] = sum(f['size_mb'] for f in downloaded_files)
        
        return summary
    
    def configure_doi_downloads(self, 
                               enabled: bool = True,
                               max_per_sync: int = 10,
                               headless: bool = True,
                               timeout: int = 30):
        """
        Configure DOI download settings.
        
        Args:
            enabled: Enable/disable DOI downloads
            max_per_sync: Maximum downloads per sync operation
            headless: Run browser in headless mode
            timeout: Download timeout in seconds
        """
        self.doi_downloads_enabled = enabled and SELENIUM_AVAILABLE
        self.max_doi_downloads_per_sync = max_per_sync
        self.browser_headless = headless
        
        # Configure the manager
        self.zotero_manager.configure_doi_downloads(
            enabled=enabled,
            headless=headless,
            timeout=timeout
        )
        
        logger.info(f"DOI downloads configured: enabled={self.doi_downloads_enabled}, "
                   f"max_per_sync={max_per_sync}, headless={headless}")
    
    def find_collections_needing_doi_downloads(self) -> List[Dict[str, Any]]:
        """
        Find collections that would benefit from DOI downloads.
        
        Returns:
            List of collections with DOI download opportunities
        """
        logger.info("Analyzing collections for DOI download opportunities...")
        
        collections_info = []
        
        try:
            collections = self.zotero_manager.get_collections()
            
            for collection in collections:
                if collection['num_items'] > 0:
                    summary = self.zotero_manager.get_collection_sync_summary(collection['key'])
                    
                    if 'error' not in summary and summary['items_with_dois_no_pdfs'] > 0:
                        collections_info.append({
                            'name': collection['name'],
                            'key': collection['key'],
                            'total_items': summary['total_items'],
                            'items_with_pdfs': summary['items_with_pdfs'],
                            'doi_download_candidates': summary['items_with_dois_no_pdfs'],
                            'items_without_dois': summary['items_without_dois'],
                            'completion_percentage': (summary['items_with_pdfs'] / summary['total_items'] * 100)
                        })
            
            # Sort by number of DOI download candidates (most opportunities first)
            collections_info.sort(key=lambda x: x['doi_download_candidates'], reverse=True)
            
            logger.info(f"Found {len(collections_info)} collections with DOI download opportunities")
            
        except Exception as e:
            logger.error(f"Error analyzing collections: {e}")
        
        return collections_info
    
    def get_recommendations(self) -> Dict[str, Any]:
        """
        Get recommendations for optimizing literature sync with DOI downloads.
        
        Returns:
            Dict with recommendations and analysis
        """
        recommendations = {
            'doi_downloads_status': self.doi_downloads_enabled,
            'recommendations': [],
            'collections_analysis': []
        }
        
        try:
            # Analyze DOI download capability
            if not SELENIUM_AVAILABLE:
                recommendations['recommendations'].append({
                    'type': 'error',
                    'title': 'Selenium Not Available',
                    'message': 'DOI-based PDF downloads require Selenium',
                    'action': 'Install with: pip install selenium'
                })
            elif not self.doi_downloads_enabled:
                recommendations['recommendations'].append({
                    'type': 'info',
                    'title': 'DOI Downloads Disabled',
                    'message': 'Enable DOI downloads to automatically acquire missing PDFs',
                    'action': 'Call configure_doi_downloads(enabled=True)'
                })
            
            # Analyze collections
            collections_needing_downloads = self.find_collections_needing_doi_downloads()
            recommendations['collections_analysis'] = collections_needing_downloads
            
            if collections_needing_downloads:
                total_candidates = sum(c['doi_download_candidates'] for c in collections_needing_downloads)
                
                recommendations['recommendations'].append({
                    'type': 'success',
                    'title': 'DOI Download Opportunities Found',
                    'message': f'Found {total_candidates} papers that could be downloaded via DOI',
                    'action': f'Focus on collections: {", ".join(c["name"] for c in collections_needing_downloads[:3])}'
                })
                
                # Recommend starting with smaller collections
                small_collections = [c for c in collections_needing_downloads if c['doi_download_candidates'] <= 10]
                if small_collections:
                    recommendations['recommendations'].append({
                        'type': 'tip',
                        'title': 'Start Small',
                        'message': f'Begin with smaller collections for testing',
                        'action': f'Try: {small_collections[0]["name"]} ({small_collections[0]["doi_download_candidates"]} candidates)'
                    })
            else:
                recommendations['recommendations'].append({
                    'type': 'success',
                    'title': 'Collections Well-Covered',
                    'message': 'Most items already have PDF attachments',
                    'action': 'Focus on knowledge base integration and AI assistance'
                })
        
        except Exception as e:
            recommendations['recommendations'].append({
                'type': 'error',
                'title': 'Analysis Error',
                'message': f'Error analyzing collections: {e}',
                'action': 'Check Zotero connection and try again'
            })
        
        return recommendations