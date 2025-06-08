#!/usr/bin/env python3
"""
Detailed Attach Mode Test Script

Tests only the attach mode with detailed paper listings to debug specific download issues.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path.cwd()
if project_root.name != "physics_synthesis":
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

# Imports
from config import PipelineConfig
from src.downloaders.enhanced_literature_syncer import EnhancedZoteroLiteratureSyncer
from src.core import KnowledgeBase

def print_collection_details(syncer: EnhancedZoteroLiteratureSyncer, collection_name: str):
    """Print detailed information about all papers in the collection."""
    print(f"\n📚 DETAILED COLLECTION ANALYSIS: {collection_name}")
    print("=" * 80)
    
    try:
        # Get collections
        collections = syncer.zotero_manager.get_collections()
        target_collection = None
        
        for coll in collections:
            if coll['name'] == collection_name:
                target_collection = coll
                break
        
        if not target_collection:
            print(f"❌ Collection '{collection_name}' not found!")
            print(f"Available collections: {[c['name'] for c in collections[:10]]}")
            return False
        
        print(f"✅ Found collection: {collection_name} (ID: {target_collection['key']})")
        print(f"📊 Collection has {target_collection['num_items']} items")
        
        # Get items directly from collection
        collection_items = syncer.zotero_manager.get_collection_items_direct(target_collection['key'])
        print(f"📄 Retrieved {len(collection_items)} parseable items from collection")
        
        if not collection_items:
            print("❌ No items found in collection!")
            return False
        
        # Analyze each item in detail
        items_with_pdfs = 0
        items_with_dois_no_pdfs = 0
        items_without_dois = 0
        
        print(f"\n📋 DETAILED ITEM ANALYSIS:")
        print("-" * 80)
        
        for i, item in enumerate(collection_items, 1):
            print(f"\n📄 ITEM {i}:")
            print(f"   Title: {item.title}")
            print(f"   DOI: {item.doi if item.doi else 'NO DOI'}")
            print(f"   Key: {item.key}")
            print(f"   Authors: {', '.join(item.authors) if item.authors else 'No authors'}")
            print(f"   Year: {item.year if item.year else 'No year'}")
            
            # Check for existing attachments
            try:
                attachments = syncer.zotero_manager.get_item_attachments(item.key)
                pdf_attachments = [att for att in attachments if att.content_type == 'application/pdf']
                
                if pdf_attachments:
                    items_with_pdfs += 1
                    print(f"   📎 HAS PDF: {len(pdf_attachments)} PDF attachment(s)")
                    for j, att in enumerate(pdf_attachments):
                        print(f"      PDF {j+1}: {att.title}")
                elif item.doi and item.doi.strip():
                    items_with_dois_no_pdfs += 1
                    print(f"   🔗 NEEDS PDF: Has DOI but no PDF attachment")
                    print(f"   🎯 DOWNLOAD CANDIDATE: This item should be processed")
                else:
                    items_without_dois += 1
                    print(f"   ❓ NO DOI: Cannot download PDF automatically")
                    
            except Exception as e:
                print(f"   ⚠️  Error checking attachments: {e}")
        
        # Summary
        print(f"\n📊 COLLECTION SUMMARY:")
        print(f"   Total items: {len(collection_items)}")
        print(f"   Items with PDFs: {items_with_pdfs}")
        print(f"   Items needing DOI downloads: {items_with_dois_no_pdfs}")
        print(f"   Items without DOIs: {items_without_dois}")
        
        # Identify specific papers for download
        download_candidates = []
        for item in collection_items:
            attachments = syncer.zotero_manager.get_item_attachments(item.key)
            pdf_attachments = [att for att in attachments if att.content_type == 'application/pdf']
            
            if not pdf_attachments and item.doi and item.doi.strip():
                download_candidates.append({
                    'title': item.title,
                    'doi': item.doi,
                    'key': item.key,
                    'authors': item.authors,
                    'year': item.year
                })
        
        print(f"\n🎯 DOWNLOAD CANDIDATES ({len(download_candidates)} items):")
        print("-" * 60)
        for i, candidate in enumerate(download_candidates, 1):
            print(f"{i}. {candidate['title']}")
            print(f"   DOI: {candidate['doi']}")
            print(f"   Key: {candidate['key']}")
            print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing collection: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_attach_mode_test(collection_name: str = "test_attach", max_downloads: int = 5):
    """Run focused attach mode test with detailed analysis."""
    
    print("🧪 FOCUSED ATTACH MODE TEST")
    print("=" * 80)
    print(f"📁 Collection: {collection_name}")
    print(f"🔢 Max downloads: {max_downloads}")
    print(f"🎯 Mode: attach (PDFs will be attached to existing Zotero records)")
    
    # Initialize components
    print("\n🔧 Initializing components...")
    try:
        config = PipelineConfig()
        kb = KnowledgeBase()
        
        syncer = EnhancedZoteroLiteratureSyncer(
            zotero_config=config.get_zotero_config(),
            knowledge_base=kb,
            doi_downloads_enabled=True,
            pdf_integration_enabled=True,
            default_integration_mode="attach"
        )
        print("✅ Components initialized successfully")
        
        # Test connection
        connection_info = syncer.zotero_manager.test_connection()
        if not connection_info['connected']:
            print(f"❌ Zotero connection failed: {connection_info['error']}")
            return
        print(f"✅ Connected to Zotero library with {connection_info['total_items']} items")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Step 1: Detailed collection analysis
    print(f"\n📋 STEP 1: DETAILED COLLECTION ANALYSIS")
    if not print_collection_details(syncer, collection_name):
        return
    
    # Step 2: Run the enhanced sync
    print(f"\n🚀 STEP 2: ENHANCED SYNC WITH ATTACH MODE")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        result = syncer.sync_collection_with_doi_downloads_and_integration(
            collection_name=collection_name,
            max_doi_downloads=max_downloads,
            integration_mode="attach",
            headless=False  # Show browser for debugging
        )
        
        processing_time = time.time() - start_time
        
        # Step 3: Detailed results analysis
        print(f"\n📊 STEP 3: DETAILED RESULTS ANALYSIS")
        print("=" * 60)
        
        zr = result.zotero_sync_result
        
        print(f"📚 Collection Processing:")
        print(f"   Total items in collection: {zr.total_items}")
        print(f"   Items with existing PDFs: {zr.items_with_existing_pdfs}")
        print(f"   Items identified for DOI download: {zr.items_with_dois_no_pdfs}")
        
        print(f"\n📥 DOI Download Results:")
        print(f"   Downloads attempted: {zr.doi_download_attempts}")
        print(f"   Downloads successful: {zr.successful_doi_downloads}")
        print(f"   Downloads failed: {zr.failed_doi_downloads}")
        
        if zr.doi_download_attempts > 0:
            success_rate = (zr.successful_doi_downloads / zr.doi_download_attempts) * 100
            print(f"   Success rate: {success_rate:.1f}%")
        
        print(f"\n🔧 PDF Integration Results:")
        print(f"   Integration mode: {result.integration_mode}")
        print(f"   PDFs integrated: {result.pdfs_integrated}")
        print(f"   Integration success rate: {result.integration_success_rate:.1f}%")
        
        # Detailed file-by-file results
        if result.pdf_integration_results:
            print(f"\n📄 DETAILED INTEGRATION RESULTS:")
            for i, ir in enumerate(result.pdf_integration_results, 1):
                status = "✅" if ir.success else "❌"
                file_name = Path(ir.pdf_path).name
                print(f"   {status} {i}. {file_name}")
                print(f"      Original DOI: {ir.doi}")
                print(f"      Original Key: {ir.original_item_key}")
                
                if ir.success:
                    print(f"      ✅ Successfully attached to Zotero record")
                    if ir.attachment_key:
                        print(f"      📎 Attachment key: {ir.attachment_key}")
                else:
                    print(f"      ❌ Error: {ir.error}")
                print()
        
        # Check for any missing papers
        print(f"\n🔍 MISSING PAPER ANALYSIS:")
        if zr.doi_download_attempts > zr.successful_doi_downloads:
            missing_count = zr.doi_download_attempts - zr.successful_doi_downloads
            print(f"   ⚠️  {missing_count} paper(s) failed to download")
            print(f"   📋 Check the detailed logs above for specific failure reasons")
            
            # Look for specific error patterns
            if result.errors:
                print(f"   📝 Errors encountered:")
                for error in result.errors:
                    print(f"      • {error}")
        else:
            print(f"   ✅ All attempted downloads succeeded!")
        
        print(f"\n⏱️  Performance:")
        print(f"   Total processing time: {processing_time:.2f}s")
        print(f"   DOI download time: {zr.processing_time:.2f}s")
        
        # Final success assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        if result.pdfs_integrated == zr.successful_doi_downloads and zr.successful_doi_downloads > 0:
            print(f"   🎉 PERFECT SUCCESS: All downloaded PDFs were successfully integrated!")
        elif result.pdfs_integrated > 0:
            print(f"   ✅ PARTIAL SUCCESS: {result.pdfs_integrated} PDFs integrated successfully")
        else:
            print(f"   ⚠️  NO INTEGRATION: No PDFs were successfully integrated")
        
        return result
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("🧪 Starting focused attach mode test...")
    print("🎯 This test will show detailed information about each paper in the collection")
    print("📋 We'll identify exactly which papers should download and which ones fail")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
        
        # Run the test
        result = run_attach_mode_test(
            collection_name="test_attach",
            max_downloads=10  # Increased to ensure we catch all papers
        )
        
        if result:
            print(f"\n✅ Test completed successfully!")
        else:
            print(f"\n❌ Test encountered issues")
            
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()