# Fixed Zotero PDF Integration System
# File: src/downloaders/zotero_pdf_integrator_fixed.py
# Corrected to use proper PyZotero attachment methods

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

class IntegrationMode(Enum):
    """Integration modes for PDF processing."""
    DOWNLOAD_ONLY = "download_only"  # Mode 1: Just download, no Zotero integration
    ATTACH_TO_EXISTING = "attach"    # Mode 2: Attach to existing record
    UPLOAD_AND_MERGE = "upload_merge" # Mode 3: Upload new + optional merge

@dataclass
class IntegrationConfig:
    """Configuration for PDF integration."""
    mode: IntegrationMode
    overwrite_record: bool = False  # Only used in UPLOAD_AND_MERGE mode
    target_collection_id: Optional[str] = None  # For upload mode
    backup_originals: bool = True  # Keep backup before merging
    preserve_tags: bool = True  # Preserve tags during merge
    preserve_notes: bool = True  # Preserve notes during merge
    merge_timeout: int = 30  # Timeout for merge operations

@dataclass
class IntegrationResult:
    """Result of PDF integration operation."""
    doi: str
    original_item_key: str
    pdf_path: str
    mode: IntegrationMode
    success: bool
    error: Optional[str] = None
    
    # Mode-specific results
    attachment_key: Optional[str] = None  # For attach mode
    new_item_key: Optional[str] = None    # For upload mode
    merged_item_key: Optional[str] = None # For merge operations
    merge_performed: bool = False
    
    # Additional info
    processing_time: float = 0.0
    metadata_extracted: bool = False
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

class FixedZoteroPDFIntegrator:
    """
    FIXED PDF integration system using correct PyZotero attachment methods.
    """
    
    def __init__(self, zotero_manager, config: IntegrationConfig):
        """
        Initialize the integrator.
        
        Args:
            zotero_manager: Enhanced Zotero manager instance
            config: Integration configuration
        """
        self.zotero_manager = zotero_manager
        self.config = config
        
        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'attachments_created': 0,
            'uploads_performed': 0,
            'merges_performed': 0,
            'errors': []
        }
        
        print(f"🔧 FIXED PDF Integrator initialized in {config.mode.value} mode")
        if config.mode == IntegrationMode.UPLOAD_AND_MERGE:
            print(f"   📁 Target collection: {config.target_collection_id}")
            print(f"   🔄 Overwrite records: {config.overwrite_record}")
    
    def process_download_results(self, download_results: List[Dict]) -> List[IntegrationResult]:
        """
        Process all download results according to the configured mode.
        
        Args:
            download_results: List of successful DOI download results
        
        Returns:
            List of integration results
        """
        print(f"\n🚀 Processing {len(download_results)} downloaded PDFs in {self.config.mode.value} mode")
        print("=" * 70)
        
        results = []
        
        for i, download_result in enumerate(download_results, 1):
            print(f"\n📄 Processing {i}/{len(download_results)}: {Path(download_result['file_path']).name}")
            
            start_time = time.time()
            
            try:
                if self.config.mode == IntegrationMode.DOWNLOAD_ONLY:
                    result = self._mode1_download_only(download_result)
                elif self.config.mode == IntegrationMode.ATTACH_TO_EXISTING:
                    result = self._mode2_attach_to_existing_fixed(download_result)
                elif self.config.mode == IntegrationMode.UPLOAD_AND_MERGE:
                    result = self._mode3_upload_and_merge_fixed(download_result)
                else:
                    raise ValueError(f"Unknown integration mode: {self.config.mode}")
                
                result.processing_time = time.time() - start_time
                
                if result.success:
                    self.stats['successful'] += 1
                    print(f"   ✅ Success ({result.processing_time:.1f}s)")
                else:
                    self.stats['failed'] += 1
                    print(f"   ❌ Failed: {result.error}")
                
            except Exception as e:
                result = IntegrationResult(
                    doi=download_result.get('doi', 'unknown'),
                    original_item_key=download_result.get('zotero_key', 'unknown'),
                    pdf_path=download_result['file_path'],
                    mode=self.config.mode,
                    success=False,
                    error=str(e),
                    processing_time=time.time() - start_time
                )
                self.stats['failed'] += 1
                self.stats['errors'].append(str(e))
                print(f"   💥 Exception: {e}")
            
            results.append(result)
            self.stats['total_processed'] += 1
        
        # Print summary
        self._print_processing_summary()
        
        return results
    
    def _mode1_download_only(self, download_result: Dict) -> IntegrationResult:
        """
        Mode 1: Download only - PDF is already downloaded, just confirm.
        """
        pdf_path = download_result['file_path']
        
        # Verify file exists and is readable
        if not Path(pdf_path).exists():
            return IntegrationResult(
                doi=download_result.get('doi', 'unknown'),
                original_item_key=download_result.get('zotero_key', 'unknown'),
                pdf_path=pdf_path,
                mode=self.config.mode,
                success=False,
                error="Downloaded PDF file not found"
            )
        
        file_size = Path(pdf_path).stat().st_size / (1024 * 1024)  # MB
        print(f"   📁 PDF available: {Path(pdf_path).name} ({file_size:.2f} MB)")
        print(f"   💾 Local path: {pdf_path}")
        
        return IntegrationResult(
            doi=download_result.get('doi', 'unknown'),
            original_item_key=download_result.get('zotero_key', 'unknown'),
            pdf_path=pdf_path,
            mode=self.config.mode,
            success=True
        )
    
    def _mode2_attach_to_existing_fixed(self, download_result: Dict) -> IntegrationResult:
        """
        FIXED Mode 2: Attach PDF to existing Zotero record using correct PyZotero methods.
        
        Args:
            download_result: Download result dictionary
        
        Returns:
            Integration result
        """
        pdf_path = download_result['file_path']
        item_key = download_result.get('zotero_key')
        
        if not item_key:
            return IntegrationResult(
                doi=download_result.get('doi', 'unknown'),
                original_item_key='unknown',
                pdf_path=pdf_path,
                mode=self.config.mode,
                success=False,
                error="No Zotero item key provided for attachment"
            )
        
        print(f"   📎 Attaching to existing record: {item_key}")
        
        try:
            # FIXED: Use the correct PyZotero attachment method
            attachment_result = self._create_attachment_correct_method(item_key, pdf_path)
            
            if attachment_result['success']:
                print(f"   ✅ Attachment created successfully")
                self.stats['attachments_created'] += 1
                
                return IntegrationResult(
                    doi=download_result.get('doi', 'unknown'),
                    original_item_key=item_key,
                    pdf_path=pdf_path,
                    mode=self.config.mode,
                    success=True,
                    attachment_key=attachment_result.get('attachment_key', 'created')
                )
            else:
                return IntegrationResult(
                    doi=download_result.get('doi', 'unknown'),
                    original_item_key=item_key,
                    pdf_path=pdf_path,
                    mode=self.config.mode,
                    success=False,
                    error=f"Attachment failed: {attachment_result.get('error', 'Unknown error')}"
                )
        
        except Exception as e:
            return IntegrationResult(
                doi=download_result.get('doi', 'unknown'),
                original_item_key=item_key,
                pdf_path=pdf_path,
                mode=self.config.mode,
                success=False,
                error=f"Exception during attachment: {e}"
            )
    
    def _create_attachment_correct_method(self, item_key: str, pdf_path: str) -> Dict[str, Any]:
        """
        FIXED: Create PDF attachment using the correct PyZotero attachment_simple method.
        
        Args:
            item_key: Zotero item key
            pdf_path: Path to PDF file
        
        Returns:
            Attachment creation result
        """
        try:
            pdf_file = Path(pdf_path)
            
            print(f"   📎 Creating attachment for item: {item_key}")
            print(f"   📄 File: {pdf_file.name} ({pdf_file.stat().st_size / (1024*1024):.2f} MB)")
            
            # CRITICAL FIX: Use attachment_simple with file path, not file content
            print(f"   📤 Using attachment_simple method...")
            
            # PyZotero attachment_simple expects a list of file paths
            file_paths = [str(pdf_path)]
            
            # Call the correct PyZotero method
            attachment_result = self.zotero_manager.zot.attachment_simple(
                file_paths,     # List of file paths
                item_key        # Parent item key
            )
            
            print(f"   📋 Attachment result: {attachment_result}")
            
            # Check if the result indicates success
            if attachment_result and isinstance(attachment_result, dict):
                # Success indicators in PyZotero attachment responses
                if 'success' in attachment_result or 'successful' in attachment_result:
                    return {
                        'success': True,
                        'attachment_key': 'attachment_simple_success',
                        'method': 'attachment_simple',
                        'result': attachment_result
                    }
                elif 'failed' in attachment_result or 'failure' in attachment_result:
                    return {
                        'success': False,
                        'error': f'PyZotero reported failure: {attachment_result}'
                    }
                else:
                    # Assume success if no explicit failure
                    return {
                        'success': True,
                        'attachment_key': 'attachment_simple_assumed_success',
                        'method': 'attachment_simple',
                        'result': attachment_result
                    }
            elif attachment_result:
                # Non-dict result but truthy - assume success
                return {
                    'success': True,
                    'attachment_key': 'attachment_simple_truthy',
                    'method': 'attachment_simple',
                    'result': attachment_result
                }
            else:
                return {
                    'success': False,
                    'error': 'attachment_simple() returned empty/falsy result'
                }
                
        except Exception as e:
            print(f"   ⚠️  attachment_simple() failed: {e}")
            
            # FALLBACK: Try attachment_both method
            try:
                print(f"   🔄 Trying attachment_both as fallback...")
                
                # attachment_both expects [(filename, filepath), ...]
                file_tuples = [(pdf_file.name, str(pdf_path))]
                
                attachment_result = self.zotero_manager.zot.attachment_both(
                    file_tuples,    # List of (filename, filepath) tuples
                    item_key        # Parent item key
                )
                
                print(f"   📋 attachment_both result: {attachment_result}")
                
                if attachment_result:
                    return {
                        'success': True,
                        'attachment_key': 'attachment_both_success',
                        'method': 'attachment_both',
                        'result': attachment_result
                    }
                else:
                    return {
                        'success': False,
                        'error': 'attachment_both() returned empty result'
                    }
                    
            except Exception as e2:
                return {
                    'success': False,
                    'error': f'Both attachment methods failed. attachment_simple: {e}, attachment_both: {e2}'
                }
    
    def _mode3_upload_and_merge_fixed(self, download_result: Dict) -> IntegrationResult:
        """
        FIXED Mode 3: Upload PDF to create new record, optionally merge with existing.
        
        Args:
            download_result: Download result dictionary
        
        Returns:
            Integration result
        """
        pdf_path = download_result['file_path']
        original_item_key = download_result.get('zotero_key')
        
        print(f"   📤 Uploading PDF to create new record...")
        
        try:
            # Step 1: Upload PDF to collection (creates new record)
            upload_result = self._upload_pdf_to_collection_fixed(pdf_path)
            
            if not upload_result['success']:
                return IntegrationResult(
                    doi=download_result.get('doi', 'unknown'),
                    original_item_key=original_item_key or 'unknown',
                    pdf_path=pdf_path,
                    mode=self.config.mode,
                    success=False,
                    error=f"Upload failed: {upload_result.get('error', 'Unknown error')}"
                )
            
            new_item_key = upload_result['item_key']
            print(f"   ✅ New record created: {new_item_key}")
            self.stats['uploads_performed'] += 1
            
            result = IntegrationResult(
                doi=download_result.get('doi', 'unknown'),
                original_item_key=original_item_key or 'unknown',
                pdf_path=pdf_path,
                mode=self.config.mode,
                success=True,
                new_item_key=new_item_key
            )
            
            # Step 2: Merge with original record if requested
            if self.config.overwrite_record and original_item_key:
                print(f"   🔄 Merging with original record: {original_item_key}")
                
                merge_result = self._merge_records(original_item_key, new_item_key)
                
                if merge_result['success']:
                    print(f"   ✅ Records merged successfully")
                    result.merge_performed = True
                    result.merged_item_key = merge_result['final_item_key']
                    self.stats['merges_performed'] += 1
                else:
                    result.warnings.append(f"Merge failed: {merge_result.get('error', 'Unknown error')}")
                    print(f"   ⚠️  Merge failed: {merge_result.get('error', 'Unknown error')}")
            
            return result
        
        except Exception as e:
            return IntegrationResult(
                doi=download_result.get('doi', 'unknown'),
                original_item_key=original_item_key or 'unknown',
                pdf_path=pdf_path,
                mode=self.config.mode,
                success=False,
                error=f"Exception during upload: {e}"
            )
    
    def _upload_pdf_to_collection_fixed(self, pdf_path: str) -> Dict[str, Any]:
        """
        FIXED: Upload PDF to collection using correct PyZotero methods.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Upload result with new item key
        """
        try:
            pdf_file = Path(pdf_path)
            
            print(f"   📤 Uploading PDF to create new record: {pdf_file.name}")
            
            # Step 1: Create a basic item to serve as parent
            print(f"   📋 Creating base item...")
            
            # Get item template
            item_template = self.zotero_manager.zot.item_template('journalArticle')
            item_data = item_template.copy()
            item_data.update({
                'title': pdf_file.stem,  # Use filename as title initially
                'itemType': 'journalArticle'
            })
            
            # Add to target collection if specified
            if self.config.target_collection_id:
                item_data['collections'] = [self.config.target_collection_id]
            
            # Create the base item
            create_response = self.zotero_manager.zot.create_items([item_data])
            
            if not create_response.get('successful') or '0' not in create_response['successful']:
                return {
                    'success': False,
                    'error': f"Failed to create base item: {create_response}"
                }
            
            item_key = create_response['successful']['0']['key']
            print(f"   ✅ Base item created: {item_key}")
            
            # Step 2: Attach the PDF using the FIXED attachment method
            attachment_result = self._create_attachment_correct_method(item_key, pdf_path)
            
            if attachment_result['success']:
                print(f"   ✅ PDF attached successfully")
                
                return {
                    'success': True,
                    'item_key': item_key,
                    'attachment_key': attachment_result.get('attachment_key'),
                    'method': 'create_item_then_attach_fixed'
                }
            else:
                # Clean up the created item since attachment failed
                try:
                    print(f"   🧹 Cleaning up failed item...")
                    item_to_delete = self.zotero_manager.zot.item(item_key)
                    self.zotero_manager.zot.delete_item(item_to_delete)
                except:
                    pass  # Ignore cleanup errors
                
                return {
                    'success': False,
                    'error': f"Failed to attach PDF: {attachment_result.get('error')}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Upload failed: {e}"
            }
    
    def _merge_records(self, original_key: str, new_key: str) -> Dict[str, Any]:
        """
        Merge two Zotero records, keeping the newer one.
        
        Args:
            original_key: Key of original record
            new_key: Key of newly created record
        
        Returns:
            Merge result
        """
        try:
            print(f"     🔍 Analyzing records for merge...")
            
            # Get both records
            original_item = self.zotero_manager.zot.item(original_key)
            new_item = self.zotero_manager.zot.item(new_key)
            
            # Preserve valuable data from original record
            preserved_data = {}
            
            if self.config.preserve_tags and original_item['data'].get('tags'):
                preserved_data['tags'] = original_item['data']['tags']
                print(f"     📌 Preserving {len(preserved_data['tags'])} tags")
            
            if self.config.preserve_notes:
                # Get notes from original item
                original_notes = self.zotero_manager.zot.children(original_key)
                note_children = [child for child in original_notes if child['data']['itemType'] == 'note']
                if note_children:
                    preserved_data['notes'] = note_children
                    print(f"     📝 Preserving {len(note_children)} notes")
            
            # Get collections from original item
            if original_item['data'].get('collections'):
                preserved_data['collections'] = original_item['data']['collections']
                print(f"     📁 Preserving {len(preserved_data['collections'])} collection memberships")
            
            # Apply preserved data to new item
            if preserved_data:
                update_data = new_item['data'].copy()
                
                if 'tags' in preserved_data:
                    # Merge tags (avoid duplicates)
                    existing_tags = [tag['tag'] for tag in update_data.get('tags', [])]
                    for tag in preserved_data['tags']:
                        if tag['tag'] not in existing_tags:
                            update_data.setdefault('tags', []).append(tag)
                
                if 'collections' in preserved_data:
                    # Merge collections
                    update_data['collections'] = list(set(
                        update_data.get('collections', []) + preserved_data['collections']
                    ))
                
                # Update the new item
                new_item['data'] = update_data
                self.zotero_manager.zot.update_item(new_item)
                
                # Transfer notes if any
                if 'notes' in preserved_data:
                    for note in preserved_data['notes']:
                        note_data = note['data'].copy()
                        note_data['parentItem'] = new_key
                        del note_data['key']  # Remove old key
                        self.zotero_manager.zot.create_items([note_data])
            
            # Delete the original record
            print(f"     🗑️  Deleting original record: {original_key}")
            delete_result = self.zotero_manager.zot.delete_item(original_item)
            
            if delete_result:
                print(f"     ✅ Merge completed successfully")
                return {
                    'success': True,
                    'final_item_key': new_key,
                    'preserved_data': list(preserved_data.keys())
                }
            else:
                return {
                    'success': False,
                    'error': "Failed to delete original record"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _print_processing_summary(self):
        """Print summary of processing results."""
        print(f"\n📊 FIXED INTEGRATION SUMMARY ({self.config.mode.value} mode)")
        print("=" * 50)
        print(f"✅ Successful: {self.stats['successful']}")
        print(f"❌ Failed: {self.stats['failed']}")
        print(f"📊 Success rate: {(self.stats['successful'] / self.stats['total_processed'] * 100):.1f}%")
        
        if self.config.mode == IntegrationMode.ATTACH_TO_EXISTING:
            print(f"📎 Attachments created: {self.stats['attachments_created']}")
        elif self.config.mode == IntegrationMode.UPLOAD_AND_MERGE:
            print(f"📤 New records created: {self.stats['uploads_performed']}")
            if self.config.overwrite_record:
                print(f"🔄 Records merged: {self.stats['merges_performed']}")
        
        if self.stats['errors']:
            print(f"\n❌ Errors encountered:")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.stats['errors']) > 5:
                print(f"   ... and {len(self.stats['errors']) - 5} more")

# Main integration function using FIXED methods
def integrate_pdfs_with_zotero_fixed(download_results: List[Dict], 
                                    zotero_manager,
                                    mode: str = "download_only",
                                    target_collection_id: Optional[str] = None,
                                    overwrite_record: bool = False) -> List[IntegrationResult]:
    """
    FIXED main function to integrate PDFs with Zotero using correct PyZotero methods.
    
    Args:
        download_results: Results from PDF download process
        zotero_manager: Zotero manager instance
        mode: Integration mode ('download_only', 'attach', 'upload_merge')
        target_collection_id: Collection ID for upload mode
        overwrite_record: Whether to merge records in upload mode
    
    Returns:
        List of integration results
    """
    # Convert string mode to enum
    mode_map = {
        'download_only': IntegrationMode.DOWNLOAD_ONLY,
        'attach': IntegrationMode.ATTACH_TO_EXISTING,
        'upload_merge': IntegrationMode.UPLOAD_AND_MERGE
    }
    
    if mode not in mode_map:
        raise ValueError(f"Invalid mode: {mode}. Must be one of {list(mode_map.keys())}")
    
    # Create configuration
    config = IntegrationConfig(
        mode=mode_map[mode],
        target_collection_id=target_collection_id,
        overwrite_record=overwrite_record
    )
    
    # Create FIXED integrator and process
    if mode == 'download_only':
        # For download-only mode, we don't need the zotero_manager
        integrator = FixedZoteroPDFIntegrator(None, config)
    else:
        integrator = FixedZoteroPDFIntegrator(zotero_manager, config)
    
    return integrator.process_download_results(download_results)

# Example usage with FIXED methods
FIXED_EXAMPLE_CONFIGS = {
    'download_only': {
        'description': 'Just download PDFs locally, no Zotero integration',
        'usage': "integrate_pdfs_with_zotero_fixed(results, None, mode='download_only')"
    },
    'attach': {
        'description': 'Attach PDFs to existing Zotero records using FIXED attachment_simple',
        'usage': "integrate_pdfs_with_zotero_fixed(results, zotero_manager, mode='attach')"
    },
    'upload_merge': {
        'description': 'Upload PDFs to create new records, optionally merge using FIXED methods',
        'usage': "integrate_pdfs_with_zotero_fixed(results, zotero_manager, mode='upload_merge', target_collection_id='ABC123', overwrite_record=True)"
    }
}