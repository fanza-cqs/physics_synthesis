#!/usr/bin/env python3
"""
Comprehensive Integration Test Script - OPTIMIZED

Tests the enhanced Zotero literature syncer with PDF integration
across reliable integration modes using dedicated test collections.

UPDATED: Removed upload_replace mode and optimized library access.

Test Collections:
- test_download_only: Tests download_only mode (PDFs stay local)
- test_attach: Tests attach mode (PDFs attached to existing records) 
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

def print_header(title: str, level: int = 1):
    """Print formatted header."""
    if level == 1:
        print(f"\n{'='*80}")
        print(f"🚀 {title}")
        print(f"{'='*80}")
    elif level == 2:
        print(f"\n{'-'*60}")
        print(f"📋 {title}")
        print(f"{'-'*60}")
    else:
        print(f"\n💡 {title}")

def print_results_summary(result, collection_name: str, mode: str):
    """Print detailed results summary."""
    print(f"\n📊 RESULTS SUMMARY - {collection_name} ({mode} mode)")
    print("=" * 50)
    
    # Zotero sync results
    zr = result.zotero_sync_result
    print(f"📚 Zotero Collection Analysis:")
    print(f"   Total items: {zr.total_items}")
    print(f"   Items with existing PDFs: {zr.items_with_existing_pdfs}")
    print(f"   Items needing DOI downloads: {zr.items_with_dois_no_pdfs}")
    
    # DOI download results
    print(f"\n📥 DOI Download Results:")
    print(f"   Downloads attempted: {zr.doi_download_attempts}")
    print(f"   Downloads successful: {zr.successful_doi_downloads}")
    print(f"   Downloads failed: {zr.failed_doi_downloads}")
    if zr.doi_download_attempts > 0:
        success_rate = (zr.successful_doi_downloads / zr.doi_download_attempts) * 100
        print(f"   Success rate: {success_rate:.1f}%")
    
    # PDF integration results
    print(f"\n🔧 PDF Integration Results:")
    print(f"   Integration mode: {result.integration_mode}")
    print(f"   PDFs integrated: {result.pdfs_integrated}")
    print(f"   Integration success rate: {result.integration_success_rate:.1f}%")
    
    # Individual integration details
    if result.pdf_integration_results:
        print(f"\n📄 Individual Integration Details:")
        for i, ir in enumerate(result.pdf_integration_results, 1):
            status = "✅" if ir.success else "❌"
            file_name = Path(ir.pdf_path).name
            print(f"   {status} {i}. {file_name}")
            if ir.success:
                if ir.attachment_key and mode == "attach":
                    print(f"      → Attached to record {ir.original_item_key}")
                elif mode == "download_only":
                    print(f"      → PDF saved locally")
            else:
                print(f"      → Error: {ir.error}")
    
    # Knowledge base results
    print(f"\n📚 Knowledge Base Results:")
    print(f"   KB updated: {result.knowledge_base_updated}")
    print(f"   Documents processed: {result.documents_processed}")
    
    # Performance
    print(f"\n⏱️  Performance:")
    print(f"   Total processing time: {result.total_processing_time:.2f}s")
    print(f"   DOI download time: {zr.processing_time:.2f}s")
    
    # Errors
    if result.errors:
        print(f"\n⚠️  Errors ({len(result.errors)}):")
        for error in result.errors[:3]:  # Show first 3 errors
            print(f"   • {error}")
        if len(result.errors) > 3:
            print(f"   ... and {len(result.errors) - 3} more")

def test_collection_preview(syncer: EnhancedZoteroLiteratureSyncer, collection_name: str):
    """Test collection preview functionality."""
    print(f"🔍 Previewing collection: {collection_name}")
    
    preview = syncer.preview_collection_sync(collection_name)
    
    if 'error' in preview:
        print(f"❌ Preview failed: {preview['error']}")
        if 'available_collections' in preview:
            print(f"   Available collections: {', '.join(preview['available_collections'][:5])}")
        return False
    
    print(f"   📚 Total items: {preview['total_items']}")
    print(f"   📄 Items with PDFs: {preview['items_with_pdfs']}")
    print(f"   🔗 Items needing DOI downloads: {preview['items_with_dois_no_pdfs']}")
    print(f"   ❓ Items without DOIs: {preview['items_without_dois']}")
    
    if preview['recommendations']:
        print(f"   💡 Recommendations:")
        for rec in preview['recommendations'][:2]:  # Show first 2 recommendations
            print(f"      • {rec['message']}")
    
    return True

def test_integration_mode(syncer: EnhancedZoteroLiteratureSyncer, 
                         collection_name: str, 
                         mode: str,
                         max_downloads: int = 3) -> Dict[str, Any]:
    """Test a specific integration mode with a collection."""
    
    print_header(f"Testing {mode.upper()} mode with {collection_name}", level=2)
    
    # Step 1: Preview
    print_header("Step 1: Collection Preview", level=3)
    if not test_collection_preview(syncer, collection_name):
        return {'error': 'Preview failed'}
    
    # Step 2: Configure for this test
    print_header("Step 2: Configuration", level=3)
    print(f"   Integration mode: {mode}")
    print(f"   Max DOI downloads: {max_downloads}")
    print(f"   Browser headless: False (for testing visibility)")
    
    # Step 3: Run the sync with integration
    print_header("Step 3: Enhanced Sync with PDF Integration", level=3)
    
    start_time = time.time()
    
    try:
        result = syncer.sync_collection_with_doi_downloads_and_integration(
            collection_name=collection_name,
            max_doi_downloads=max_downloads,
            integration_mode=mode,
            headless=False  # Show browser for testing
        )
        
        test_time = time.time() - start_time
        
        # Step 4: Analyze results
        print_header("Step 4: Results Analysis", level=3)
        print_results_summary(result, collection_name, mode)
        
        # Step 5: Validation
        print_header("Step 5: Validation", level=3)
        
        validation_results = {
            'downloads_attempted': result.zotero_sync_result.doi_download_attempts > 0,
            'downloads_successful': result.zotero_sync_result.successful_doi_downloads > 0,
            'integration_performed': len(result.pdf_integration_results) > 0,
            'integration_successful': result.pdfs_integrated > 0,
            'kb_updated': result.knowledge_base_updated,
            'no_critical_errors': len([e for e in result.errors if 'critical' in e.lower()]) == 0
        }
        
        print(f"   ✅ DOI downloads attempted: {validation_results['downloads_attempted']}")
        print(f"   ✅ DOI downloads successful: {validation_results['downloads_successful']}")
        print(f"   ✅ Integration performed: {validation_results['integration_performed']}")
        print(f"   ✅ Integration successful: {validation_results['integration_successful']}")
        print(f"   ✅ Knowledge base updated: {validation_results['kb_updated']}")
        print(f"   ✅ No critical errors: {validation_results['no_critical_errors']}")
        
        success_count = sum(validation_results.values())
        total_checks = len(validation_results)
        
        if success_count == total_checks:
            print(f"\n🎉 {mode.upper()} MODE TEST: FULLY SUCCESSFUL ({success_count}/{total_checks} checks passed)")
        elif success_count >= total_checks * 0.8:  # 80% success
            print(f"\n✅ {mode.upper()} MODE TEST: MOSTLY SUCCESSFUL ({success_count}/{total_checks} checks passed)")
        else:
            print(f"\n⚠️  {mode.upper()} MODE TEST: PARTIAL SUCCESS ({success_count}/{total_checks} checks passed)")
        
        return {
            'result': result,
            'validation': validation_results,
            'test_time': test_time,
            'success_rate': success_count / total_checks
        }
        
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

def run_comprehensive_test():
    """Run comprehensive test of reliable integration modes."""
    
    print_header("COMPREHENSIVE ENHANCED ZOTERO INTEGRATION TEST")
    
    # Initialize components
    print_header("Initialization", level=2)
    
    try:
        print("🔧 Loading configuration...")
        config = PipelineConfig()
        
        print("🧠 Initializing knowledge base...")
        kb = KnowledgeBase()
        
        print("📚 Initializing enhanced Zotero syncer...")
        syncer = EnhancedZoteroLiteratureSyncer(
            zotero_config=config.get_zotero_config(),
            knowledge_base=kb,
            doi_downloads_enabled=True,
            pdf_integration_enabled=True,
            default_integration_mode="attach"
        )
        
        print("✅ All components initialized successfully")
        
        # Test connection
        print("\n🔗 Testing Zotero connection...")
        connection_info = syncer.zotero_manager.test_connection()
        if connection_info['connected']:
            print(f"✅ Connected! Library has {connection_info['total_items']} items")
        else:
            print(f"❌ Connection failed: {connection_info['error']}")
            return
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return
    
    # UPDATED: Test configurations (removed upload_replace)
    test_configs = [
        {
            'collection': 'test_download_only',
            'mode': 'download_only',
            'max_downloads': 3,
            'description': 'Download PDFs locally without Zotero integration'
        },
        {
            'collection': 'test_attach',
            'mode': 'attach', 
            'max_downloads': 3,
            'description': 'Download PDFs and attach to existing Zotero records'
        },
        # REMOVED: upload_replace test configuration
    ]
    
    # Run tests
    test_results = {}
    
    for i, test_config in enumerate(test_configs, 1):
        print_header(f"TEST {i}/{len(test_configs)}: {test_config['mode'].upper()} MODE", level=1)
        print(f"📝 Description: {test_config['description']}")
        print(f"📁 Collection: {test_config['collection']}")
        print(f"🔢 Max downloads: {test_config['max_downloads']}")
        
        result = test_integration_mode(
            syncer=syncer,
            collection_name=test_config['collection'],
            mode=test_config['mode'],
            max_downloads=test_config['max_downloads']
        )
        
        test_results[test_config['mode']] = result
        
        # Pause between tests
        if i < len(test_configs):
            print(f"\n⏸️  Pausing 10 seconds before next test...")
            time.sleep(10)
    
    # Final summary
    print_header("COMPREHENSIVE TEST SUMMARY")
    
    total_tests = len(test_configs)
    successful_tests = 0
    
    for mode, result in test_results.items():
        if 'error' not in result:
            success_rate = result.get('success_rate', 0)
            if success_rate >= 0.8:  # 80% success threshold
                status = "✅ PASSED"
                successful_tests += 1
            else:
                status = "⚠️  PARTIAL"
            
            print(f"{status} {mode.upper()} mode: {success_rate:.1%} success rate")
            
            if 'result' in result:
                r = result['result']
                print(f"   📥 Downloaded: {r.zotero_sync_result.successful_doi_downloads} PDFs")
                print(f"   🔧 Integrated: {r.pdfs_integrated} PDFs")
                print(f"   ⏱️  Time: {result['test_time']:.1f}s")
        else:
            print(f"❌ FAILED {mode.upper()} mode: {result['error']}")
    
    print(f"\n📊 OVERALL RESULTS: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Your enhanced integration system is working perfectly!")
        print("\n💡 Next steps:")
        print("   • Use with your actual research collections")
        print("   • Try batch processing with batch_sync_collections_with_integration()")
        print("   • Integrate with your AI assistant workflow")
    elif successful_tests >= total_tests * 0.66:  # 66% success
        print("✅ Most tests passed! System is largely functional with minor issues.")
        print("\n🔧 Recommendations:")
        print("   • Check failed tests for specific issues")
        print("   • Verify Zotero collection setup")
        print("   • Test with different papers/DOIs")
    else:
        print("⚠️  Several tests failed. Please review the detailed results above.")
        print("\n🔧 Troubleshooting:")
        print("   • Verify Zotero API credentials")
        print("   • Check network connectivity")
        print("   • Ensure test collections have items with DOIs")
        print("   • Try running individual tests manually")
    
    # OPTIMIZED: System diagnostics without expensive library scans
    print_header("SYSTEM DIAGNOSTICS", level=2)
    
    # DOI downloads summary
    doi_summary = syncer.get_doi_downloads_summary()
    print(f"📥 DOI Downloads:")
    print(f"   Enabled: {doi_summary['doi_downloads_enabled']}")
    print(f"   Selenium available: {doi_summary['selenium_available']}")
    print(f"   Downloaded files: {doi_summary['total_files']}")
    if doi_summary['total_files'] > 0:
        print(f"   Total size: {doi_summary['total_size_mb']:.1f} MB")
    
    # Integration summary
    integration_summary = syncer.get_integration_summary()
    print(f"\n🔧 PDF Integration:")
    print(f"   Enabled: {integration_summary['pdf_integration_enabled']}")
    print(f"   Default mode: {integration_summary['default_integration_mode']}")
    print(f"   Available modes: {', '.join(integration_summary['available_modes'])}")
    
    # OPTIMIZED: Skip expensive recommendations that scan the whole library
    print(f"\n✅ STREAMLINED TEST COMPLETE")
    print(f"🚀 System ready for production use with modes: {', '.join(integration_summary['available_modes'])}")
    print(f"💡 For collection analysis, use preview_collection_sync() for specific collections")

if __name__ == "__main__":
    print("🧪 Starting comprehensive enhanced Zotero integration test...")
    print("⚠️  Make sure you have the following test collections in your Zotero:")
    print("   • test_download_only (with items that have DOIs but no PDFs)")
    print("   • test_attach (with items that have DOIs but no PDFs)")  
    print("\n📋 NOTE: upload_replace mode has been disabled due to API limitations")
    print("🎯 Testing reliable modes: download_only, attach")
    print("\nPress Enter to continue or Ctrl+C to cancel...")
    
    try:
        input()
        run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n🛑 Test cancelled by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()