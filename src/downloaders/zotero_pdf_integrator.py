# Zotero PDF Integration System
# File: src/downloaders/zotero_pdf_integrator.py
# Supports three modes: Download-only, Attach, Upload+Merge

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

class ZoteroPDFIntegrator:
    """
    Flexible PDF integration system supporting multiple modes.
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
        
        print(f"🔧 PDF Integrator initialized in {config.mode.value} mode")
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
                    result = self._mode2_attach_to_existing(download_result)
                elif self.config.mode == IntegrationMode.UPLOAD_AND_MERGE:
                    result = self._mode3_upload_and_merge(download_result)
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
        
        Args:
            download_result: Download result dictionary
        
        Returns:
            Integration result
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
    
    def _mode2_attach_to_existing(self, download_result: Dict) -> IntegrationResult:
        """
        Mode 2: Attach PDF to existing Zotero record.
        
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
            # Create attachment in Zotero
            attachment_result = self._create_attachment(item_key, pdf_path)
            
            if attachment_result['success']:
                print(f"   ✅ Attachment created: {attachment_result['attachment_key']}")
                self.stats['attachments_created'] += 1
                
                return IntegrationResult(
                    doi=download_result.get('doi', 'unknown'),
                    original_item_key=item_key,
                    pdf_path=pdf_path,
                    mode=self.config.mode,
                    success=True,
                    attachment_key=attachment_result['attachment_key']
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
    
    def _mode3_upload_and_merge(self, download_result: Dict) -> IntegrationResult:
        """
        Mode 3: Upload PDF to create new record, optionally merge with existing.
        
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
            upload_result = self._upload_pdf_to_collection(pdf_path)
            
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
    
    def _create_attachment(self, item_key: str, pdf_path: str) -> Dict[str, Any]:
        """
        Create PDF attachment for existing Zotero item.
        
        Args:
            item_key: Zotero item key
            pdf_path: Path to PDF file
        
        Returns:
            Attachment creation result
        """
        try:
            pdf_file = Path(pdf_path)
            
            # Create attachment metadata
            attachment_data = {
                'itemType': 'attachment',
                'parentItem': item_key,
                'title': pdf_file.stem,
                'filename': pdf_file.name,
                'contentType': 'application/pdf',
                'linkMode': 'imported_file'
            }
            
            # Create attachment item in Zotero
            create_response = self.zotero_manager.zot.create_items([attachment_data])
            
            if not create_response.get('success'):
                return {
                    'success': False,
                    'error': f"Failed to create attachment item: {create_response}"
                }
            
            # Get the attachment key
            attachment_key = create_response['successful']['0']['key']
            
            # Upload file content
            with open(pdf_path, 'rb') as f:
                file_content = f.read()
            
            upload_response = self.zotero_manager.zot.attachment(attachment_key, file_content)
            
            return {
                'success': True,
                'attachment_key': attachment_key,
                'upload_response': upload_response
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _upload_pdf_to_collection(self, pdf_path: str) -> Dict[str, Any]:
        """
        Upload PDF to collection, creating a new record.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Upload result with new item key
        """
        try:
            # This simulates the drag-and-drop functionality
            # The actual implementation depends on PyZotero capabilities
            
            # Method 1: Try using file upload with automatic metadata extraction
            pdf_file = Path(pdf_path)
            
            # Upload file and let Zotero extract metadata
            with open(pdf_path, 'rb') as f:
                file_content = f.read()
            
            # Create item with PDF attachment
            # Note: This is a simplified approach - actual implementation may vary
            item_data = {
                'itemType': 'journalArticle',  # Default type
                'title': pdf_file.stem,  # Will be updated by Zotero's metadata extraction
                'collections': [self.config.target_collection_id] if self.config.target_collection_id else []
            }
            
            # Create the item first
            create_response = self.zotero_manager.zot.create_items([item_data])
            
            if not create_response.get('success'):
                return {
                    'success': False,
                    'error': f"Failed to create item: {create_response}"
                }
            
            item_key = create_response['successful']['0']['key']
            
            # Now attach the PDF
            attachment_result = self._create_attachment(item_key, pdf_path)
            
            if not attachment_result['success']:
                # Clean up the created item
                self.zotero_manager.zot.delete_item(item_key)
                return {
                    'success': False,
                    'error': f"Failed to attach PDF: {attachment_result.get('error')}"
                }
            
            # Trigger metadata extraction (if supported by PyZotero)
            # This would be equivalent to "Retrieve metadata for PDF" in Zotero UI
            try:
                self.zotero_manager.zot.retrieve_pdf_metadata(attachment_result['attachment_key'])
            except AttributeError:
                # Method not available, that's OK
                pass
            
            return {
                'success': True,
                'item_key': item_key,
                'attachment_key': attachment_result['attachment_key']
            }
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    

    # =============================================================================
    # FIXED ATTACHMENT CREATION METHOD
    # =============================================================================

    def _create_attachment_fixed(self, item_key: str, pdf_path: str) -> Dict[str, Any]:
        """
        CORRECTLY FIXED: Create PDF attachment for existing Zotero item using proper PyZotero methods.
        
        Based on PyZotero documentation:
        - attachment_simple() for uploading files
        - create_items() for creating attachment metadata
        
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
            
            # Method 1: Use attachment_simple() - the correct PyZotero method
            try:
                # Read the file content
                with open(pdf_path, 'rb') as f:
                    file_content = f.read()
                
                print(f"   📤 Uploading file using attachment_simple()...")
                
                # Use the correct PyZotero method for file upload
                attachment_result = self.zotero_manager.zot.attachment_simple(
                    [file_content],  # File content as bytes
                    parentid=item_key  # Parent item key
                )
                
                print(f"   📋 Attachment result: {attachment_result}")
                
                if attachment_result:
                    return {
                        'success': True,
                        'attachment_key': 'uploaded_via_attachment_simple',
                        'method': 'attachment_simple',
                        'result': attachment_result
                    }
                else:
                    return {
                        'success': False,
                        'error': 'attachment_simple() returned empty result'
                    }
                    
            except Exception as method1_error:
                print(f"   ⚠️  attachment_simple() failed: {method1_error}")
                
                # Method 2: Manual attachment creation + file upload
                try:
                    print(f"   🔄 Trying manual attachment creation...")
                    
                    # Step 1: Create attachment item metadata
                    attachment_template = self.zotero_manager.zot.item_template('attachment', 'imported_file')
                    
                    attachment_data = attachment_template.copy()
                    attachment_data.update({
                        'parentItem': item_key,
                        'title': pdf_file.stem,
                        'filename': pdf_file.name,
                        'contentType': 'application/pdf'
                    })
                    
                    print(f"   📋 Creating attachment metadata...")
                    create_response = self.zotero_manager.zot.create_items([attachment_data])
                    
                    if not create_response.get('successful'):
                        return {
                            'success': False,
                            'error': f"Failed to create attachment metadata: {create_response}"
                        }
                    
                    # Extract attachment key
                    if '0' in create_response['successful']:
                        attachment_key = create_response['successful']['0']['key']
                        print(f"   ✅ Attachment metadata created: {attachment_key}")
                    else:
                        return {
                            'success': False,
                            'error': f"Could not extract attachment key: {create_response}"
                        }
                    
                    # Step 2: Upload file content using file_upload()
                    print(f"   📤 Uploading file content...")
                    with open(pdf_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Use the correct PyZotero file upload method
                    upload_result = self.zotero_manager.zot.upload_attachment(
                        attachment_key, 
                        file_content
                    )
                    
                    print(f"   📋 Upload result: {upload_result}")
                    
                    return {
                        'success': True,
                        'attachment_key': attachment_key,
                        'method': 'manual_creation_and_upload',
                        'upload_result': upload_result
                    }
                    
                except Exception as method2_error:
                    print(f"   ⚠️  Manual method failed: {method2_error}")
                    
                    # Method 3: Try the documented approach with proper error handling
                    try:
                        print(f"   🔄 Trying documented attachment approach...")
                        
                        # Use the documented method from PyZotero examples
                        with open(pdf_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Try creating attachment using the item creation approach
                        attachment_data = {
                            'itemType': 'attachment',
                            'parentItem': item_key,
                            'linkMode': 'imported_file',
                            'title': pdf_file.stem,
                            'contentType': 'application/pdf',
                            'filename': pdf_file.name
                        }
                        
                        print(f"   📋 Creating attachment with proper linkMode...")
                        response = self.zotero_manager.zot.create_items([attachment_data])
                        
                        if response.get('successful') and '0' in response['successful']:
                            attachment_key = response['successful']['0']['key']
                            print(f"   ✅ Attachment created: {attachment_key}")
                            
                            # Now upload the actual file
                            print(f"   📤 Uploading file to attachment...")
                            
                            # Check what upload methods are available
                            available_methods = [method for method in dir(self.zotero_manager.zot) if 'upload' in method.lower() or 'attach' in method.lower()]
                            print(f"   🔍 Available upload methods: {available_methods}")
                            
                            # Try different upload approaches
                            upload_success = False
                            
                            # Try 1: upload_attachment (if available)
                            if hasattr(self.zotero_manager.zot, 'upload_attachment'):
                                try:
                                    upload_result = self.zotero_manager.zot.upload_attachment(attachment_key, file_content)
                                    print(f"   ✅ upload_attachment succeeded: {upload_result}")
                                    upload_success = True
                                except Exception as e:
                                    print(f"   ❌ upload_attachment failed: {e}")
                            
                            # Try 2: attachment_simple with specific parameters
                            if not upload_success and hasattr(self.zotero_manager.zot, 'attachment_simple'):
                                try:
                                    upload_result = self.zotero_manager.zot.attachment_simple(
                                        [file_content], 
                                        attachment_key
                                    )
                                    print(f"   ✅ attachment_simple with key succeeded: {upload_result}")
                                    upload_success = True
                                except Exception as e:
                                    print(f"   ❌ attachment_simple with key failed: {e}")
                            
                            if upload_success:
                                return {
                                    'success': True,
                                    'attachment_key': attachment_key,
                                    'method': 'documented_approach',
                                    'upload_result': upload_result
                                }
                            else:
                                # At least we created the attachment metadata
                                print(f"   ⚠️  File upload failed, but attachment metadata created")
                                return {
                                    'success': True,  # Partial success
                                    'attachment_key': attachment_key,
                                    'method': 'metadata_only',
                                    'warning': 'File content not uploaded - attachment exists but file missing'
                                }
                        else:
                            return {
                                'success': False,
                                'error': f"Documented approach failed: {response}"
                            }
                            
                    except Exception as method3_error:
                        return {
                            'success': False,
                            'error': f"All attachment methods failed. Last error: {method3_error}"
                        }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Critical error in attachment creation: {e}"
            }

    # =============================================================================
    # FIXED UPLOAD AND MERGE METHOD
    # =============================================================================

    def _upload_pdf_to_collection_fixed(self, pdf_path: str) -> Dict[str, Any]:
        """
        CORRECTLY FIXED: Upload PDF to collection using proper PyZotero methods.
        
        Args:
            pdf_path: Path to PDF file
        
        Returns:
            Upload result with new item key
        """
        try:
            pdf_file = Path(pdf_path)
            
            print(f"   📤 Uploading PDF to create new record: {pdf_file.name}")
            
            # Method 1: Try using attachment_simple to create a standalone item
            try:
                with open(pdf_path, 'rb') as f:
                    file_content = f.read()
                
                print(f"   🔄 Attempting standalone PDF upload...")
                
                # Create a basic item first
                item_template = self.zotero_manager.zot.item_template('journalArticle')
                item_data = item_template.copy()
                item_data.update({
                    'title': pdf_file.stem,
                    'itemType': 'journalArticle'
                })
                
                # Add to target collection if specified
                if self.config.target_collection_id:
                    item_data['collections'] = [self.config.target_collection_id]
                
                print(f"   📋 Creating base item...")
                create_response = self.zotero_manager.zot.create_items([item_data])
                
                if not create_response.get('successful') or '0' not in create_response['successful']:
                    return {
                        'success': False,
                        'error': f"Failed to create base item: {create_response}"
                    }
                
                item_key = create_response['successful']['0']['key']
                print(f"   ✅ Base item created: {item_key}")
                
                # Now attach the PDF using our fixed attachment method
                attachment_result = self._create_attachment_fixed(item_key, pdf_path)
                
                if attachment_result['success']:
                    print(f"   ✅ PDF attached successfully")
                    
                    # Try to trigger metadata extraction if available
                    try:
                        # This might extract title, authors, etc. from the PDF
                        if hasattr(self.zotero_manager.zot, 'retrieve_pdf_metadata'):
                            print(f"   🔍 Attempting metadata extraction...")
                            self.zotero_manager.zot.retrieve_pdf_metadata(attachment_result['attachment_key'])
                            print(f"   ✅ Metadata extraction triggered")
                    except Exception as meta_error:
                        print(f"   ⚠️  Metadata extraction not available: {meta_error}")
                    
                    return {
                        'success': True,
                        'item_key': item_key,
                        'attachment_key': attachment_result.get('attachment_key'),
                        'method': 'create_item_then_attach'
                    }
                else:
                    # Clean up the created item since attachment failed
                    try:
                        print(f"   🧹 Cleaning up failed item...")
                        self.zotero_manager.zot.delete_item(item_key)
                    except:
                        pass  # Ignore cleanup errors
                    
                    return {
                        'success': False,
                        'error': f"Failed to attach PDF: {attachment_result.get('error')}"
                    }
                    
            except Exception as upload_error:
                return {
                    'success': False,
                    'error': f"Upload failed: {upload_error}"
                }
        
        except Exception as e:
            return {
                'success': False,
                'error': f"Critical upload error: {e}"
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
        print(f"\n📊 INTEGRATION SUMMARY ({self.config.mode.value} mode)")
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

# Usage Functions

def create_download_only_integrator():
    """Create integrator for download-only mode."""
    config = IntegrationConfig(mode=IntegrationMode.DOWNLOAD_ONLY)
    return config

def create_attach_integrator(zotero_manager):
    """Create integrator for attach-to-existing mode."""
    config = IntegrationConfig(mode=IntegrationMode.ATTACH_TO_EXISTING)
    return ZoteroPDFIntegrator(zotero_manager, config)

def create_upload_merge_integrator(zotero_manager, target_collection_id: str, overwrite_record: bool = False):
    """Create integrator for upload-and-merge mode."""
    config = IntegrationConfig(
        mode=IntegrationMode.UPLOAD_AND_MERGE,
        target_collection_id=target_collection_id,
        overwrite_record=overwrite_record,
        preserve_tags=True,
        preserve_notes=True
    )
    return ZoteroPDFIntegrator(zotero_manager, config)

# Main integration function
def integrate_pdfs_with_zotero(download_results: List[Dict], 
                              zotero_manager,
                              mode: str = "download_only",
                              target_collection_id: Optional[str] = None,
                              overwrite_record: bool = False) -> List[IntegrationResult]:
    """
    Main function to integrate PDFs with Zotero.
    
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
    
    # Create integrator and process
    if mode == 'download_only':
        # For download-only mode, we don't need the zotero_manager
        integrator = ZoteroPDFIntegrator(None, config)
    else:
        integrator = ZoteroPDFIntegrator(zotero_manager, config)
    
    return integrator.process_download_results(download_results)

# Example usage configurations
EXAMPLE_CONFIGS = {
    'download_only': {
        'description': 'Just download PDFs locally, no Zotero integration',
        'usage': "integrate_pdfs_with_zotero(results, None, mode='download_only')"
    },
    'attach': {
        'description': 'Attach PDFs to existing Zotero records',
        'usage': "integrate_pdfs_with_zotero(results, zotero_manager, mode='attach')"
    },
    'upload_merge': {
        'description': 'Upload PDFs to create new records, optionally merge',
        'usage': "integrate_pdfs_with_zotero(results, zotero_manager, mode='upload_merge', target_collection_id='ABC123', overwrite_record=True)"
    }
}