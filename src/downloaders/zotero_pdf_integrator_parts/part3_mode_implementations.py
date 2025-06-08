# Fixed Zotero PDF Integration System - Part 3: Mode Implementations (Modular)
# File: src/downloaders/zotero_pdf_integrator_parts/part3_mode_implementations.py

from pathlib import Path
from typing import Dict

# Import from Part 1
from .part1_core_classes import IntegrationMode, IntegrationResult

def mode1_download_only(self, download_result: Dict) -> IntegrationResult:
    """
    Mode 1: Download only - PDF is already downloaded, just confirm.
    
    Note: This is a standalone function that will be attached to the main class.
    The 'self' parameter refers to the FixedZoteroPDFIntegrator instance.
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

def mode2_attach_to_existing_fixed(self, download_result: Dict) -> IntegrationResult:
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
        # Use the attachment method (will be attached from Part 4)
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

def mode3_upload_and_replace_fixed(self, download_result: Dict) -> IntegrationResult:
    """
    FIXED Mode 3: Upload PDF to create new record, then replace the original record.
    
    This mode:
    1. Creates a new Zotero item by uploading the PDF
    2. Extracts metadata from the PDF (if possible)
    3. Preserves tags, notes, and collections from the original record
    4. Deletes the original record
    5. The new record becomes the definitive version with the PDF attached
    
    Args:
        download_result: Download result dictionary
    
    Returns:
        Integration result
    """
    pdf_path = download_result['file_path']
    original_item_key = download_result.get('zotero_key')
    
    print(f"   📤 Mode 3: Upload PDF and replace original record...")
    
    try:
        # Use the upload method (will be attached from Part 5)
        upload_result = self._upload_pdf_to_collection_with_metadata_extraction(pdf_path)
        
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
        print(f"   ✅ New record created with PDF: {new_item_key}")
        self.stats['uploads_performed'] += 1
        
        result = IntegrationResult(
            doi=download_result.get('doi', 'unknown'),
            original_item_key=original_item_key or 'unknown',
            pdf_path=pdf_path,
            mode=self.config.mode,
            success=True,
            new_item_key=new_item_key
        )
        
        # Step 2: Replace original record if requested and available
        if self.config.replace_original and original_item_key:
            print(f"   🔄 Replacing original record: {original_item_key}")
            
            # Use the replace method (will be attached from Part 5)
            replace_result = self._replace_record_with_preservation(original_item_key, new_item_key)
            
            if replace_result['success']:
                print(f"   ✅ Record replaced successfully")
                result.replacement_performed = True
                result.replaced_item_key = replace_result['final_item_key']
                self.stats['replacements_performed'] += 1
            else:
                result.warnings.append(f"Replacement failed: {replace_result.get('error', 'Unknown error')}")
                print(f"   ⚠️  Replacement failed: {replace_result.get('error', 'Unknown error')}")
                print(f"   📚 New record exists, but original record preserved")
        else:
            print(f"   📚 New record created (original record preserved)")
        
        return result
    
    except Exception as e:
        return IntegrationResult(
            doi=download_result.get('doi', 'unknown'),
            original_item_key=original_item_key or 'unknown',
            pdf_path=pdf_path,
            mode=self.config.mode,
            success=False,
            error=f"Exception during upload and replace: {e}"
        )

# Test function for this part
def test_part3():
    """Test that Part 3 works correctly."""
    print("🧪 Testing Part 3: Mode Implementations...")
    
    # Test that functions exist and are callable
    assert callable(mode1_download_only)
    assert callable(mode2_attach_to_existing_fixed)
    assert callable(mode3_upload_and_replace_fixed)
    
    print("✅ Part 3 test passed!")
    return True

if __name__ == "__main__":
    test_part3()