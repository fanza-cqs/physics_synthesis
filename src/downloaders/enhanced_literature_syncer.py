#!/usr/bin/env python3
"""
Enhanced Zotero Literature Syncer with DOI-based PDF downloading and PDF Integration.

Provides high-level interface for syncing Zotero collections with automatic
PDF downloads for items that have DOIs but no attachments, plus seamless
PDF integration back into Zotero using the fixed integration system.
"""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .enhanced_zotero_manager import EnhancedZoteroLibraryManager, CollectionSyncResult, SELENIUM_AVAILABLE
from .zotero_pdf_integrator_fixed import integrate_pdfs_with_zotero_fixed, get_available_modes
from ..core.knowledge_base import KnowledgeBase
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class EnhancedSyncResult:
    """Result of enhanced literature synchronization with DOI downloads and PDF integration."""
    zotero_sync_result: CollectionSyncResult
    pdf_integration_results: List[Any]  # Integration results from fixed integrator
    knowledge_base_updated: bool
    documents_processed: int
    total_processing_time: float
    errors: List[str]
    
    # New integration statistics
    pdfs_integrated: int = 0
    integration_mode: str = "none"
    integration_success_rate: float = 0.0

class EnhancedZoteroLiteratureSyncer:
    """
    Enhanced literature syncer with DOI-based PDF downloading and PDF integration capabilities.
    
    Provides seamless integration between Zotero collections and knowledge base
    with automatic PDF acquisition and integration back into Zotero records.
    """
    
    def __init__(self,
                 zotero_config: Dict[str, Any],
                 knowledge_base: Optional[KnowledgeBase] = None,
                 auto_build_kb: bool = True,
                 doi_downloads_enabled: bool = True,
                 pdf_integration_enabled: bool = True,
                 default_integration_mode: str = "download_only"):
        """
        Initialize enhanced literature syncer with PDF integration.
        
        Args:
            zotero_config: Zotero configuration dictionary
            knowledge_base: Optional KnowledgeBase instance
            auto_build_kb: Whether to automatically update knowledge base
            doi_downloads_enabled: Whether to enable DOI-based downloads
            pdf_integration_enabled: Whether to enable PDF integration back to Zotero
            default_integration_mode: Default mode for PDF integration ('attach', 'upload_replace', 'download_only')
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
        self.pdf_integration_enabled = pdf_integration_enabled
        self.default_integration_mode = default_integration_mode
        
        # Validate integration mode
        available_modes = get_available_modes()
        if default_integration_mode not in available_modes:
            logger.warning(f"Invalid integration mode '{default_integration_mode}'. Using 'attach'.")
            self.default_integration_mode = "attach"
        
        # Default DOI download settings
        self.max_doi_downloads_per_sync = 10  # Limit for safety
        self.browser_headless = True
        
        logger.info(f"Enhanced literature syncer initialized:")
        logger.info(f"  DOI downloads: {self.doi_downloads_enabled}")
        logger.info(f"  PDF integration: {self.pdf_integration_enabled}")
        logger.info(f"  Default integration mode: {self.default_integration_mode}")
    
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
            
            # Add recommendations including PDF integration info
            recommendations = []
            
            if summary['items_with_dois_no_pdfs'] > 0:
                if self.doi_downloads_enabled:
                    recommendations.append({
                        'type': 'success',
                        'message': f"Can attempt DOI downloads for {summary['items_with_dois_no_pdfs']} items",
                        'action': 'Will automatically download PDFs using browser automation'
                    })
                    
                    if self.pdf_integration_enabled:
                        recommendations.append({
                            'type': 'info',
                            'message': f"Downloaded PDFs will be integrated using '{self.default_integration_mode}' mode",
                            'action': f'PDFs will be {"attached to existing records" if self.default_integration_mode == "attach" else "used to create new records" if self.default_integration_mode == "upload_replace" else "kept locally only"}'
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
                'doi_downloads_available': self.doi_downloads_enabled,
                'pdf_integration_available': self.pdf_integration_enabled,
                'integration_mode': self.default_integration_mode
            })
            
            return summary
            
        except Exception as e:
            logger.error(f"Error previewing collection sync: {e}")
            return {'error': str(e)}
    
    def sync_collection_with_doi_downloads_and_integration(self, 
                                                         collection_name: str,
                                                         max_doi_downloads: int = None,
                                                         update_knowledge_base: bool = None,
                                                         headless: bool = None,
                                                         integration_mode: str = None,
                                                         target_collection_id: str = None) -> EnhancedSyncResult:
        """
        Sync a collection with automatic DOI-based PDF downloads AND PDF integration back to Zotero.
        
        This is the main enhanced method that combines:
        1. DOI-based PDF downloads
        2. PDF integration back into Zotero records
        3. Knowledge base updates
        
        Args:
            collection_name: Name of the Zotero collection to sync
            max_doi_downloads: Maximum DOI downloads to attempt (None for default limit)
            update_knowledge_base: Whether to update KB (None for auto setting)
            headless: Run browser in headless mode (None for default)
            integration_mode: PDF integration mode ('attach', 'upload_replace', 'download_only')
            target_collection_id: Target collection for upload_replace mode
        
        Returns:
            EnhancedSyncResult with comprehensive sync and integration information
        """
        start_time = time.time()
        
        logger.info(f"Starting enhanced collection sync with PDF integration: {collection_name}")
        
        # Use defaults if not specified
        if max_doi_downloads is None:
            max_doi_downloads = self.max_doi_downloads_per_sync
        if update_knowledge_base is None:
            update_knowledge_base = self.auto_build_kb
        if headless is None:
            headless = self.browser_headless
        if integration_mode is None:
            integration_mode = self.default_integration_mode
        

        # ADDED: Validate integration mode
        if integration_mode == 'upload_replace':
            raise ValueError(
                "upload_replace mode has been disabled due to Zotero API limitations. "
                "Use 'attach' mode for reliable PDF integration."
            )
        
        available_modes = ['download_only', 'attach']
        if integration_mode not in available_modes:
            raise ValueError(f"Invalid integration mode '{integration_mode}'. Available: {available_modes}")
        

        errors = []
        pdf_integration_results = []
        
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
                    pdf_integration_results=[],
                    knowledge_base_updated=False,
                    documents_processed=0,
                    total_processing_time=time.time() - start_time,
                    errors=[error_msg],
                    integration_mode=integration_mode
                )
            
            # STEP 1: Perform Zotero sync with DOI downloads (using enhanced method)
            logger.info(f"Step 1: Syncing collection with DOI downloads: {target_collection['name']} (ID: {target_collection['key']})")
            
            zotero_sync_result = self.zotero_manager.sync_collection_with_doi_downloads_enhanced(
                collection_id=target_collection['key'],
                max_doi_downloads=max_doi_downloads,
                headless=headless
            )
            
            # STEP 2: Integrate downloaded PDFs back into Zotero (if enabled and files were downloaded)
            pdfs_integrated = 0
            integration_success_rate = 0.0
            
            if (self.pdf_integration_enabled and 
                hasattr(zotero_sync_result, 'download_metadata') and 
                zotero_sync_result.download_metadata):
                
                logger.info(f"Step 2: Integrating {len(zotero_sync_result.download_metadata)} downloaded PDFs using '{integration_mode}' mode")
                
                try:
                    # Use the fixed PDF integration system
                    pdf_integration_results = integrate_pdfs_with_zotero_fixed(
                        download_results=zotero_sync_result.download_metadata,
                        zotero_manager=self.zotero_manager,
                        mode=integration_mode,
                        target_collection_id=target_collection_id or target_collection['key'],
                        replace_original=True
                    )
                    
                    # Calculate integration statistics
                    successful_integrations = sum(1 for result in pdf_integration_results if result.success)
                    pdfs_integrated = successful_integrations
                    
                    if len(pdf_integration_results) > 0:
                        integration_success_rate = successful_integrations / len(pdf_integration_results) * 100
                    
                    logger.info(f"PDF integration complete: {successful_integrations}/{len(pdf_integration_results)} successful ({integration_success_rate:.1f}%)")
                    
                    # Collect integration errors
                    for result in pdf_integration_results:
                        if not result.success:
                            errors.append(f"PDF integration failed for {Path(result.pdf_path).name}: {result.error}")
                    
                except Exception as e:
                    error_msg = f"PDF integration failed: {e}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            elif self.pdf_integration_enabled:
                logger.info("Step 2: No PDFs to integrate (none were downloaded)")
            else:
                logger.info("Step 2: PDF integration disabled")
            
            # STEP 3: Update knowledge base if requested
            documents_processed = 0
            knowledge_base_updated = False
            
            if update_knowledge_base and self.knowledge_base:
                logger.info("Step 3: Updating knowledge base with synced content...")
                
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
                pdf_integration_results=pdf_integration_results,
                knowledge_base_updated=knowledge_base_updated,
                documents_processed=documents_processed,
                total_processing_time=total_processing_time,
                errors=errors + zotero_sync_result.errors,
                pdfs_integrated=pdfs_integrated,
                integration_mode=integration_mode,
                integration_success_rate=integration_success_rate
            )
            
            # Log comprehensive summary
            logger.info(f"Enhanced collection sync with PDF integration complete:")
            logger.info(f"  Collection: {collection_name}")
            logger.info(f"  Total items: {zotero_sync_result.total_items}")
            logger.info(f"  Items with existing PDFs: {zotero_sync_result.items_with_existing_pdfs}")
            logger.info(f"  DOI downloads attempted: {zotero_sync_result.doi_download_attempts}")
            logger.info(f"  DOI downloads successful: {zotero_sync_result.successful_doi_downloads}")
            logger.info(f"  PDFs integrated back to Zotero: {pdfs_integrated}")
            logger.info(f"  Integration mode: {integration_mode}")
            logger.info(f"  Integration success rate: {integration_success_rate:.1f}%")
            logger.info(f"  KB documents processed: {documents_processed}")
            logger.info(f"  Total processing time: {total_processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            error_msg = f"Error during enhanced sync with integration: {e}"
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
                pdf_integration_results=[],
                knowledge_base_updated=False,
                documents_processed=0,
                total_processing_time=time.time() - start_time,
                errors=errors,
                integration_mode=integration_mode
            )
    
    # Legacy method for backward compatibility
    def sync_collection_with_doi_downloads(self, 
                                         collection_name: str,
                                         max_doi_downloads: int = None,
                                         update_knowledge_base: bool = None,
                                         headless: bool = None) -> EnhancedSyncResult:
        """
        Legacy method - now calls the enhanced version with PDF integration.
        
        For backward compatibility, this method now enables PDF integration by default.
        Use sync_collection_with_doi_downloads_and_integration() for full control.
        """
        logger.info(f"Legacy sync method called - using enhanced version with PDF integration")
        
        return self.sync_collection_with_doi_downloads_and_integration(
            collection_name=collection_name,
            max_doi_downloads=max_doi_downloads,
            update_knowledge_base=update_knowledge_base,
            headless=headless,
            integration_mode=self.default_integration_mode
        )
    
    def batch_sync_collections_with_integration(self, 
                                              collection_names: List[str],
                                              max_doi_downloads_per_collection: int = 5,
                                              integration_mode: str = None) -> Dict[str, EnhancedSyncResult]:
        """
        Sync multiple collections with DOI downloads and PDF integration.
        
        Args:
            collection_names: List of collection names to sync
            max_doi_downloads_per_collection: Max DOI downloads per collection
            integration_mode: PDF integration mode for all collections
        
        Returns:
            Dict mapping collection names to their sync results
        """
        if integration_mode is None:
            integration_mode = self.default_integration_mode
            
        logger.info(f"Starting batch sync with PDF integration for {len(collection_names)} collections")
        logger.info(f"Integration mode: {integration_mode}")
        
        results = {}
        
        for i, collection_name in enumerate(collection_names, 1):
            logger.info(f"Processing collection {i}/{len(collection_names)}: {collection_name}")
            
            try:
                result = self.sync_collection_with_doi_downloads_and_integration(
                    collection_name=collection_name,
                    max_doi_downloads=max_doi_downloads_per_collection,
                    headless=True,  # Always headless for batch operations
                    integration_mode=integration_mode
                )
                results[collection_name] = result
                
                # Small delay between collections
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error syncing collection {collection_name}: {e}")
                results[collection_name] = None
        
        # Summary with integration statistics
        successful_syncs = sum(1 for r in results.values() if r is not None)
        total_doi_downloads = sum(
            r.zotero_sync_result.successful_doi_downloads 
            for r in results.values() 
            if r is not None
        )
        total_integrations = sum(
            r.pdfs_integrated 
            for r in results.values() 
            if r is not None
        )
        
        logger.info(f"Batch sync with integration complete:")
        logger.info(f"  Collections processed: {successful_syncs}/{len(collection_names)}")
        logger.info(f"  PDFs downloaded: {total_doi_downloads}")
        logger.info(f"  PDFs integrated: {total_integrations}")
        logger.info(f"  Integration mode: {integration_mode}")
        
        return results
    
    # Legacy method for backward compatibility
    def batch_sync_collections(self, 
                              collection_names: List[str],
                              max_doi_downloads_per_collection: int = 5) -> Dict[str, EnhancedSyncResult]:
        """
        Legacy method - now calls the enhanced version with PDF integration.
        """
        logger.info(f"Legacy batch sync method called - using enhanced version with PDF integration")
        
        return self.batch_sync_collections_with_integration(
            collection_names=collection_names,
            max_doi_downloads_per_collection=max_doi_downloads_per_collection,
            integration_mode=self.default_integration_mode
        )
    
    def configure_pdf_integration(self,
                                 enabled: bool = True,
                                 default_mode: str = "attach"):
        """
        Configure PDF integration settings.
        
        Args:
            enabled: Enable/disable PDF integration
            default_mode: Default integration mode ('attach', 'upload_replace', 'download_only')
        """
        available_modes = get_available_modes()
        
        if default_mode not in available_modes:
            raise ValueError(f"Invalid integration mode '{default_mode}'. Available: {available_modes}")
        
        self.pdf_integration_enabled = enabled
        self.default_integration_mode = default_mode
        
        logger.info(f"PDF integration configured:")
        logger.info(f"  Enabled: {enabled}")
        logger.info(f"  Default mode: {default_mode}")
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """
        Get summary of PDF integration capabilities and settings.
        
        Returns:
            Dict with integration information
        """
        summary = {
            'pdf_integration_enabled': self.pdf_integration_enabled,
            'default_integration_mode': self.default_integration_mode,
            'available_modes': get_available_modes(),
            'mode_descriptions': {
                'download_only': 'Keep PDFs locally without Zotero integration',
                'attach': 'Attach PDFs to existing Zotero records (recommended)',
                #DISABLE 'upload_replace': 'Create new records with PDFs and replace originals'
            }
        }
        
        return summary
    
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
    
    # Add this optimized method to enhanced_literature_syncer.py
    # Replace the existing get_recommendations() method

    def get_recommendations(self, skip_library_scan: bool = False) -> Dict[str, Any]:
        """
        Get recommendations for optimizing literature sync with DOI downloads and PDF integration.
        
        Args:
            skip_library_scan: Skip expensive library-wide analysis (recommended for large libraries)
        
        Returns:
            Dict with recommendations and analysis
        """
        recommendations = {
            'doi_downloads_status': self.doi_downloads_enabled,
            'pdf_integration_status': self.pdf_integration_enabled,
            'integration_mode': self.default_integration_mode,
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
            
            # Analyze PDF integration
            if not self.pdf_integration_enabled:
                recommendations['recommendations'].append({
                    'type': 'info',
                    'title': 'PDF Integration Disabled',
                    'message': 'Enable PDF integration to automatically add downloaded PDFs to Zotero records',
                    'action': 'Call configure_pdf_integration(enabled=True)'
                })
            else:
                recommendations['recommendations'].append({
                    'type': 'success',
                    'title': 'PDF Integration Enabled',
                    'message': f'Downloaded PDFs will be integrated using "{self.default_integration_mode}" mode',
                    'action': f'Mode can be changed with configure_pdf_integration(default_mode="new_mode")'
                })
            
            # OPTIMIZED: Only analyze collections if specifically requested
            if not skip_library_scan:
                logger.info("Analyzing collections for DOI download opportunities (this may take time for large libraries)...")
                collections_needing_downloads = self.find_collections_needing_doi_downloads()
                recommendations['collections_analysis'] = collections_needing_downloads
                
                if collections_needing_downloads:
                    total_candidates = sum(c['doi_download_candidates'] for c in collections_needing_downloads)
                    
                    recommendations['recommendations'].append({
                        'type': 'success',
                        'title': 'DOI Download + Integration Opportunities',
                        'message': f'Found {total_candidates} papers that could be downloaded and integrated via DOI',
                        'action': f'Use sync_collection_with_doi_downloads_and_integration() for: {", ".join(c["name"] for c in collections_needing_downloads[:3])}'
                    })
                    
                    # Recommend starting with smaller collections
                    small_collections = [c for c in collections_needing_downloads if c['doi_download_candidates'] <= 10]
                    if small_collections:
                        recommendations['recommendations'].append({
                            'type': 'tip',
                            'title': 'Start Small',
                            'message': f'Begin with smaller collections for testing integration',
                            'action': f'Try: {small_collections[0]["name"]} ({small_collections[0]["doi_download_candidates"]} candidates)'
                        })
                else:
                    recommendations['recommendations'].append({
                        'type': 'success',
                        'title': 'Collections Well-Covered',
                        'message': 'Most items already have PDF attachments',
                        'action': 'Focus on knowledge base integration and AI assistance'
                    })
            else:
                recommendations['recommendations'].append({
                    'type': 'info',
                    'title': 'Library Analysis Skipped',
                    'message': 'Use preview_collection_sync() for specific collections to see DOI download opportunities',
                    'action': 'Call get_recommendations(skip_library_scan=False) for full analysis (may be slow)'
                })
        
        except Exception as e:
            recommendations['recommendations'].append({
                'type': 'error',
                'title': 'Analysis Error',
                'message': f'Error analyzing collections: {e}',
                'action': 'Check Zotero connection and try again'
            })
        
        return recommendations

    # Also add this optimized find_collections method
    def find_collections_needing_doi_downloads_fast(self) -> List[Dict[str, Any]]:
        """
        Find collections that would benefit from DOI downloads (OPTIMIZED VERSION).
        
        Only checks collections, not individual items, for faster performance.
        
        Returns:
            List of collections with potential DOI download opportunities
        """
        logger.info("Analyzing collections for DOI download opportunities (fast mode)...")
        
        collections_info = []
        
        try:
            # Get collections list only (fast)
            collections = self.zotero_manager.get_collections()
            
            for collection in collections:
                if collection['num_items'] > 0:
                    # Only add collections that have items - let user preview specific ones
                    collections_info.append({
                        'name': collection['name'],
                        'key': collection['key'],
                        'total_items': collection['num_items'],
                        'analysis_needed': True,
                        'recommendation': f"Use preview_collection_sync('{collection['name']}') to see DOI download opportunities"
                    })
            
            # Sort by number of items (largest first)
            collections_info.sort(key=lambda x: x['total_items'], reverse=True)
            
            logger.info(f"Found {len(collections_info)} collections. Use preview_collection_sync() for detailed analysis.")
            
        except Exception as e:
            logger.error(f"Error analyzing collections: {e}")
        
        return collections_info[:10]  # Return top 10 largest collections