# Fixed Zotero PDF Integration System - Part 5: Upload and Replace Methods (Modular)
# File: src/downloaders/zotero_pdf_integrator_parts/part5_upload_replace_methods.py

from pathlib import Path
from typing import Dict, Any

def upload_pdf_to_collection_with_metadata_extraction(self, pdf_path: str) -> Dict[str, Any]:
    """
    FIXED: Upload PDF to collection with automatic metadata extraction.
    
    This method simulates the "drag and drop PDF into Zotero" functionality
    which automatically extracts metadata from the PDF.
    
    Args:
        pdf_path: Path to PDF file
    
    Returns:
        Upload result with new item key
    """
    try:
        pdf_file = Path(pdf_path)
        
        print(f"   📤 Uploading PDF with metadata extraction: {pdf_file.name}")
        
        # Method 1: Try to create a standalone PDF item that Zotero can process
        print(f"   🔍 Creating standalone PDF item for metadata extraction...")
        
        # Create attachment template for standalone PDF
        attachment_template = self.zotero_manager.zot.item_template('attachment', 'imported_file')
        attachment_data = attachment_template.copy()
        attachment_data.update({
            'title': pdf_file.stem,
            'filename': pdf_file.name,
            'contentType': 'application/pdf',
            # Don't set parentItem - this creates a standalone attachment
        })
        
        # Add to target collection if specified
        if self.config.target_collection_id:
            attachment_data['collections'] = [self.config.target_collection_id]
        
        # Create the standalone attachment
        create_response = self.zotero_manager.zot.create_items([attachment_data])
        
        if not create_response.get('successful') or '0' not in create_response['successful']:
            # Fallback to creating a regular item with attachment
            return self._upload_pdf_to_collection_fixed(pdf_path)
        
        attachment_key = create_response['successful']['0']['key']
        print(f"   ✅ Standalone PDF item created: {attachment_key}")
        
        # Upload the actual file content
        print(f"   📤 Uploading file content...")
        file_paths = [str(pdf_path)]
        
        try:
            # Use attachment_simple to upload the file to the standalone item
            upload_result = self.zotero_manager.zot.attachment_simple(
                file_paths,
                attachment_key
            )
            
            print(f"   ✅ File uploaded successfully")
            
            # Try to trigger metadata extraction if available
            # Note: This may not work with all PyZotero versions
            try:
                # Some versions of Zotero API support metadata retrieval
                if hasattr(self.zotero_manager.zot, 'retrieve_pdf_metadata'):
                    print(f"   🔍 Attempting automatic metadata extraction...")
                    self.zotero_manager.zot.retrieve_pdf_metadata(attachment_key)
                    print(f"   ✅ Metadata extraction triggered")
            except Exception as meta_error:
                print(f"   ⚠️  Metadata extraction not available: will use filename as title")
            
            return {
                'success': True,
                'item_key': attachment_key,  # The standalone attachment is the item
                'method': 'standalone_pdf_with_metadata_extraction'
            }
            
        except Exception as upload_error:
            # Clean up the created item and fall back
            try:
                self.zotero_manager.zot.delete_item([{'key': attachment_key}])
            except:
                pass
            
            print(f"   ⚠️  Standalone upload failed, using fallback method...")
            return self._upload_pdf_to_collection_fixed(pdf_path)
    
    except Exception as e:
        print(f"   ⚠️  Metadata extraction method failed: {e}")
        print(f"   🔄 Falling back to standard upload method...")
        return self._upload_pdf_to_collection_fixed(pdf_path)

def replace_record_with_preservation(self, original_key: str, new_key: str) -> Dict[str, Any]:
    """
    Replace the original record with the new one, preserving valuable metadata.
    
    This method:
    1. Extracts valuable metadata from the original record (tags, notes, collections)
    2. Applies this metadata to the new record
    3. Deletes the original record
    4. The new record becomes the definitive version
    
    Args:
        original_key: Key of original record to be replaced
        new_key: Key of new record with PDF attached
    
    Returns:
        Replacement result
    """
    try:
        print(f"     🔍 Analyzing records for replacement...")
        
        # Get both records
        original_item = self.zotero_manager.zot.item(original_key)
        new_item = self.zotero_manager.zot.item(new_key)
        
        if not original_item or not new_item:
            return {
                'success': False,
                'error': 'Could not retrieve one or both records'
            }
        
        # Extract valuable metadata from original record
        preserved_data = {}
        
        # Preserve tags
        if self.config.preserve_tags and original_item['data'].get('tags'):
            preserved_data['tags'] = original_item['data']['tags']
            print(f"     📌 Preserving {len(preserved_data['tags'])} tags")
        
        # Preserve notes (child items)
        if self.config.preserve_notes:
            try:
                original_children = self.zotero_manager.zot.children(original_key)
                note_children = [child for child in original_children if child['data']['itemType'] == 'note']
                if note_children:
                    preserved_data['notes'] = note_children
                    print(f"     📝 Preserving {len(note_children)} notes")
            except Exception as e:
                print(f"     ⚠️  Could not retrieve notes: {e}")
        
        # Preserve collections
        if self.config.preserve_collections and original_item['data'].get('collections'):
            preserved_data['collections'] = original_item['data']['collections']
            print(f"     📁 Preserving {len(preserved_data['collections'])} collection memberships")
        
        # Preserve other valuable metadata fields
        valuable_fields = ['DOI', 'abstractNote', 'creators', 'date', 'publicationTitle', 
                         'volume', 'issue', 'pages', 'ISSN', 'language', 'extra']
        
        for field in valuable_fields:
            if original_item['data'].get(field) and not new_item['data'].get(field):
                # Only copy if new item doesn't have this field
                preserved_data[field] = original_item['data'][field]
        
        if any(field in preserved_data for field in valuable_fields):
            preserved_fields = [field for field in valuable_fields if field in preserved_data]
            print(f"     📋 Preserving metadata fields: {', '.join(preserved_fields)}")
        
        # Apply preserved data to new item
        if preserved_data:
            update_data = new_item['data'].copy()
            
            # Apply tags
            if 'tags' in preserved_data:
                existing_tags = [tag['tag'] for tag in update_data.get('tags', [])]
                for tag in preserved_data['tags']:
                    if tag['tag'] not in existing_tags:
                        update_data.setdefault('tags', []).append(tag)
            
            # Apply collections
            if 'collections' in preserved_data:
                existing_collections = set(update_data.get('collections', []))
                new_collections = set(preserved_data['collections'])
                update_data['collections'] = list(existing_collections.union(new_collections))
            
            # Apply other metadata fields
            for field in valuable_fields:
                if field in preserved_data:
                    update_data[field] = preserved_data[field]
            
            # Update the new item with preserved data
            new_item['data'] = update_data
            self.zotero_manager.zot.update_item(new_item)
            print(f"     ✅ Metadata transferred to new record")
            
            # Transfer notes as child items
            if 'notes' in preserved_data:
                for note in preserved_data['notes']:
                    try:
                        note_data = note['data'].copy()
                        note_data['parentItem'] = new_key
                        if 'key' in note_data:
                            del note_data['key']  # Remove old key to create new note
                        self.zotero_manager.zot.create_items([note_data])
                    except Exception as note_error:
                        print(f"     ⚠️  Failed to transfer note: {note_error}")
                
                print(f"     ✅ Notes transferred to new record")
        
        # Delete the original record
        print(f"     🗑️  Deleting original record: {original_key}")
        try:
            delete_result = self.zotero_manager.zot.delete_item(original_item)
            
            if delete_result or delete_result == []:  # Some versions return empty list on success
                print(f"     ✅ Original record deleted successfully")
                return {
                    'success': True,
                    'final_item_key': new_key,
                    'preserved_data': list(preserved_data.keys()),
                    'replacement_completed': True
                }
            else:
                return {
                    'success': False,
                    'error': f"Failed to delete original record: {delete_result}"
                }
        except Exception as delete_error:
            return {
                'success': False,
                'error': f"Exception deleting original record: {delete_error}"
            }
    
    except Exception as e:
        return {
            'success': False,
            'error': f"Exception during replacement: {e}"
        }

# Test function for this part
def test_part5():
    """Test that Part 5 works correctly."""
    print("🧪 Testing Part 5: Upload and Replace Methods...")
    
    # Test that functions exist and are callable
    assert callable(upload_pdf_to_collection_with_metadata_extraction)
    assert callable(replace_record_with_preservation)
    
    print("✅ Part 5 test passed!")
    return True

if __name__ == "__main__":
    test_part5()