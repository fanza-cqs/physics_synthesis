#!/usr/bin/env python3
"""
Focused Zotero PDF Integration Test Script

A simple, focused test script that tests ONLY Zotero PDF download and integration
functionality without any LLM/knowledge base complexity.

User specifies:
1. Mode: download_only or attach
2. Collection name to test
3. Max downloads (optional)

The script then runs the test and provides clear results.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path.cwd()
if project_root.name != "physics_synthesis":
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

# Imports
from config import PipelineConfig
from src.downloaders.enhanced_literature_syncer import EnhancedZoteroLiteratureSyncer

def get_user_input():
    """Get test configuration from user."""
    print("🔧 ZOTERO PDF INTEGRATION TEST CONFIGURATION")
    print("=" * 50)
    
    # Get mode
    print("\n📋 Available integration modes:")
    print("   1. download_only - Download PDFs locally (no Zotero integration)")
    print("   2. attach - Download PDFs and attach to existing Zotero records")
    
    while True:
        mode_choice = input("\nSelect mode (1 or 2): ").strip()
        if mode_choice == "1":
            mode = "download_only"
            break
        elif mode_choice == "2":
            mode = "attach"
            break
        else:
            print("❌ Invalid choice. Please enter 1 or 2.")
    
    # Get collection name
    collection_name = input(f"\n📁 Enter Zotero collection name to test: ").strip()
    if not collection_name:
        print("❌ Collection name cannot be empty")
        return None
    
    # Get max downloads
    while True:
        max_input = input(f"\n🔢 Max downloads to attempt (default: 5): ").strip()
        if not max_input:
            max_downloads = 5
            break
        try:
            max_downloads = int(max_input)
            if max_downloads > 0:
                break
            else:
                print("❌ Please enter a positive number")
        except ValueError:
            print("❌ Please enter a valid number")
    
    return {
        'mode': mode,
        'collection_name': collection_name,
        'max_downloads': max_downloads
    }

def test_zotero_connection(syncer: EnhancedZoteroLiteratureSyncer) -> bool:
    """Test Zotero connection and display library info."""
    print("\n🔗 TESTING ZOTERO CONNECTION")
    print("-" * 40)
    
    try:
        connection_info = syncer.zotero_manager.test_connection()
        
        if connection_info['connected']:
            print("✅ Zotero connection successful!")
            print(f"   📚 Library type: {connection_info['library_type']}")
            print(f"   📄 Total items: {connection_info['total_items']}")
            return True
        else:
            print(f"❌ Zotero connection failed: {connection_info['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

def preview_collection(syncer: EnhancedZoteroLiteratureSyncer, collection_name: str) -> Dict[str, Any]:
    """Preview collection and show what will be processed."""
    print(f"\n🔍 PREVIEWING COLLECTION: {collection_name}")
    print("-" * 50)
    
    try:
        preview = syncer.preview_collection_sync(collection_name)
        
        if 'error' in preview:
            print(f"❌ Collection preview failed: {preview['error']}")
            
            if 'available_collections' in preview:
                print(f"\n📋 Available collections:")
                for i, coll in enumerate(preview['available_collections'][:10], 1):
                    print(f"   {i}. {coll}")
                if len(preview['available_collections']) > 10:
                    print(f"   ... and {len(preview['available_collections']) - 10} more")
            
            return preview
        
        print(f"✅ Collection found: {collection_name}")
        print(f"   📚 Total items: {preview['total_items']}")
        print(f"   📄 Items with PDFs: {preview['items_with_pdfs']}")
        print(f"   🔗 Items needing DOI downloads: {preview['items_with_dois_no_pdfs']}")
        print(f"   ❓ Items without DOIs: {preview['items_without_dois']}")
        
        if preview['items_with_dois_no_pdfs'] == 0:
            print("\n⚠️  No items need PDF downloads (all items already have PDFs or no DOIs)")
            return preview
        
        print(f"\n💡 Ready to download {preview['items_with_dois_no_pdfs']} PDFs")
        return preview
        
    except Exception as e:
        print(f"❌ Error previewing collection: {e}")
        return {'error': str(e)}

def run_pdf_download_test(syncer: EnhancedZoteroLiteratureSyncer, 
                         collection_name: str, 
                         mode: str, 
                         max_downloads: int) -> Optional[Dict[str, Any]]:
    """Run the actual PDF download and integration test."""
    print(f"\n🚀 RUNNING {mode.upper()} TEST")
    print("=" * 50)
    print(f"📁 Collection: {collection_name}")
    print(f"🔧 Mode: {mode}")
    print(f"🔢 Max downloads: {max_downloads}")
    print(f"👀 Browser visibility: Enabled (headless=False)")
    
    start_time = time.time()
    
    try:
        # Run the enhanced sync without knowledge base (focused test)
        result = syncer.sync_collection_with_doi_downloads_and_integration(
            collection_name=collection_name,
            max_doi_downloads=max_downloads,
            integration_mode=mode,
            update_knowledge_base=False,  # Skip KB for focused test
            headless=False  # Show browser for debugging
        )
        
        test_time = time.time() - start_time
        
        print(f"\n📊 TEST RESULTS ({test_time:.1f}s)")
        print("=" * 30)
        
        # Zotero collection results
        zr = result.zotero_sync_result
        print(f"📚 Collection Analysis:")
        print(f"   Total items: {zr.total_items}")
        print(f"   Items with existing PDFs: {zr.items_with_existing_pdfs}")
        print(f"   Items identified for download: {zr.items_with_dois_no_pdfs}")
        
        # Download results
        print(f"\n📥 DOI Download Results:")
        print(f"   Downloads attempted: {zr.doi_download_attempts}")
        print(f"   Downloads successful: {zr.successful_doi_downloads}")
        print(f"   Downloads failed: {zr.failed_doi_downloads}")
        
        if zr.doi_download_attempts > 0:
            download_rate = (zr.successful_doi_downloads / zr.doi_download_attempts) * 100
            print(f"   Download success rate: {download_rate:.1f}%")
        
        # Integration results (mode-specific)
        if mode == "attach":
            print(f"\n🔧 PDF Integration Results:")
            print(f"   PDFs integrated to Zotero: {result.pdfs_integrated}")
            print(f"   Integration success rate: {result.integration_success_rate:.1f}%")
            
            if result.pdf_integration_results:
                print(f"\n📄 Individual Integration Results:")
                for i, ir in enumerate(result.pdf_integration_results, 1):
                    status = "✅" if ir.success else "❌"
                    file_name = Path(ir.pdf_path).name
                    print(f"   {status} {i}. {file_name}")
                    if ir.success:
                        print(f"      → Attached to Zotero record: {ir.original_item_key}")
                    else:
                        print(f"      → Error: {ir.error}")
        
        elif mode == "download_only":
            print(f"\n📁 Local Download Results:")
            print(f"   PDFs saved locally: {zr.successful_doi_downloads}")
            if zr.downloaded_files:
                print(f"   Download folder: {Path(zr.downloaded_files[0]).parent}")
                print(f"   Downloaded files:")
                for i, file_path in enumerate(zr.downloaded_files, 1):
                    file_size = Path(file_path).stat().st_size / (1024 * 1024)
                    print(f"      {i}. {Path(file_path).name} ({file_size:.1f} MB)")
        
        # Error summary
        if result.errors:
            print(f"\n⚠️  Errors Encountered ({len(result.errors)}):")
            for i, error in enumerate(result.errors, 1):
                print(f"   {i}. {error}")
        
        # Final assessment
        print(f"\n🎯 FINAL ASSESSMENT:")
        if zr.successful_doi_downloads > 0:
            if mode == "attach" and result.pdfs_integrated == zr.successful_doi_downloads:
                print("🎉 PERFECT SUCCESS: All downloaded PDFs were integrated into Zotero!")
            elif mode == "download_only":
                print("🎉 SUCCESS: All PDFs downloaded locally!")
            elif mode == "attach" and result.pdfs_integrated > 0:
                print(f"✅ PARTIAL SUCCESS: {result.pdfs_integrated}/{zr.successful_doi_downloads} PDFs integrated")
            else:
                print("⚠️  MIXED RESULTS: Downloads succeeded but integration had issues")
        else:
            print("❌ NO DOWNLOADS: No PDFs were successfully downloaded")
            if zr.doi_download_attempts == 0:
                print("   Reason: No items needed downloads")
            else:
                print("   Reason: All download attempts failed")
        
        return {
            'success': zr.successful_doi_downloads > 0,
            'downloads': zr.successful_doi_downloads,
            'integrations': result.pdfs_integrated if mode == "attach" else zr.successful_doi_downloads,
            'test_time': test_time,
            'mode': mode
        }
        
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function."""
    print("🧪 FOCUSED ZOTERO PDF INTEGRATION TEST")
    print("=" * 60)
    print("This script tests ONLY Zotero PDF download and integration.")
    print("No knowledge base or LLM functionality is involved.")
    
    # Get user configuration
    config = get_user_input()
    if not config:
        print("❌ Configuration failed")
        return
    
    print(f"\n✅ Test Configuration:")
    print(f"   Mode: {config['mode']}")
    print(f"   Collection: {config['collection_name']}")
    print(f"   Max downloads: {config['max_downloads']}")
    
    # Initialize syncer (no knowledge base)
    print(f"\n🔧 INITIALIZING ZOTERO SYNCER")
    print("-" * 40)
    
    try:
        pipeline_config = PipelineConfig()
        
        # Create syncer without knowledge base for focused testing
        syncer = EnhancedZoteroLiteratureSyncer(
            zotero_config=pipeline_config.get_zotero_config(),
            knowledge_base=None,  # No KB needed for focused test
            auto_build_kb=False,
            doi_downloads_enabled=True,
            pdf_integration_enabled=True,
            default_integration_mode=config['mode']
        )
        
        print("✅ Syncer initialized successfully")
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # Test connection
    if not test_zotero_connection(syncer):
        print("\n❌ Cannot proceed without Zotero connection")
        return
    
    # Preview collection
    preview = preview_collection(syncer, config['collection_name'])
    if 'error' in preview:
        print("\n❌ Cannot proceed without valid collection")
        return
    
    # Confirm test
    if preview['items_with_dois_no_pdfs'] == 0:
        print("\n⚠️  This collection has no items that need PDF downloads.")
        choice = input("Continue anyway? (y/N): ").strip().lower()
        if choice != 'y':
            print("Test cancelled")
            return
    
    print(f"\n🎯 About to test {config['mode']} mode with {config['collection_name']}")
    print(f"   Will attempt to download up to {config['max_downloads']} PDFs")
    if config['mode'] == 'attach':
        print("   Downloaded PDFs will be attached to existing Zotero records")
    else:
        print("   Downloaded PDFs will be saved locally only")
    
    choice = input("\nProceed with test? (Y/n): ").strip().lower()
    if choice == 'n':
        print("Test cancelled")
        return
    
    # Run the test
    result = run_pdf_download_test(
        syncer=syncer,
        collection_name=config['collection_name'],
        mode=config['mode'],
        max_downloads=config['max_downloads']
    )
    
    # Final summary
    print(f"\n🏁 TEST COMPLETE")
    print("=" * 30)
    
    if result:
        if result['success']:
            print(f"✅ Test successful!")
            print(f"   Downloaded: {result['downloads']} PDFs")
            if config['mode'] == 'attach':
                print(f"   Integrated: {result['integrations']} PDFs")
            print(f"   Time: {result['test_time']:.1f}s")
        else:
            print(f"⚠️  Test completed with issues")
    else:
        print(f"❌ Test failed")
    
    print(f"\n💡 Next steps:")
    if result and result['success']:
        print("   • Try with other collections")
        print("   • Test the other integration mode")
        print("   • Use with your actual research workflow")
    else:
        print("   • Check Zotero collection setup")
        print("   • Verify items have DOIs")
        print("   • Check network connectivity")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()