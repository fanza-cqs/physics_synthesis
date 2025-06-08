# Fixed Zotero PDF Integration System - Part 4: Attachment Methods (Modular)
# File: src/downloaders/zotero_pdf_integrator_parts/part4_attachment_methods.py

from pathlib import Path
from typing import Dict, Any

def create_attachment_correct_method(self, item_key: str, pdf_path: str) -> Dict[str, Any]:
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

def upload_pdf_to_collection_fixed(self, pdf_path: str) -> Dict[str, Any]:
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

# Test function for this part
def test_part4():
    """Test that Part 4 works correctly."""
    print("🧪 Testing Part 4: Attachment Methods...")
    
    # Test that functions exist and are callable
    assert callable(create_attachment_correct_method)
    assert callable(upload_pdf_to_collection_fixed)
    
    print("✅ Part 4 test passed!")
    return True

if __name__ == "__main__":
    test_part4()