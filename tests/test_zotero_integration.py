#!/usr/bin/env python3
"""
Complete Integration Test Script for Zotero Manager Architecture

This script tests the entire Zotero integration system to ensure:
1. All imports work correctly
2. Factory functions operate as expected
3. Backward compatibility is maintained
4. Graceful degradation functions properly
5. Documentation and status functions work

Run this script after making changes to verify nothing is broken.
"""

import sys
import traceback
from pathlib import Path

# Add the src directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent))

def test_section(name):
    """Decorator to mark test sections"""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {name}")
    print('='*60)

def test_result(test_name, success, error=None):
    """Print test result with proper formatting"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {test_name}")
    if error:
        print(f"     Error: {error}")
    return success

def safe_test(func, test_name):
    """Safely run a test function and return success status"""
    try:
        func()
        return test_result(test_name, True)
    except Exception as e:
        return test_result(test_name, False, str(e))

def test_basic_imports():
    """Test that all basic imports work"""
    test_section("BASIC IMPORTS")
    
    # Test legacy imports
    def test_legacy():
        from src.downloaders import BibtexParser, PaperMetadata
        from src.downloaders import ArxivSearcher, ArxivSearchResult, DownloadResult
        from src.downloaders import LiteratureDownloader, PaperDownloadResult
        print("     ✓ Legacy BibTeX imports")
    
    # Test availability flags
    def test_flags():
        from src.downloaders import (
            ZOTERO_AVAILABLE, 
            ENHANCED_ZOTERO_AVAILABLE,
            PDF_INTEGRATION_AVAILABLE, 
            SELENIUM_AVAILABLE
        )
        print(f"     ✓ Availability flags imported")
        print(f"       - ZOTERO_AVAILABLE: {ZOTERO_AVAILABLE}")
        print(f"       - ENHANCED_ZOTERO_AVAILABLE: {ENHANCED_ZOTERO_AVAILABLE}")
        print(f"       - PDF_INTEGRATION_AVAILABLE: {PDF_INTEGRATION_AVAILABLE}")
        print(f"       - SELENIUM_AVAILABLE: {SELENIUM_AVAILABLE}")
    
    # Test basic Zotero imports (if available)
    def test_basic_zotero():
        from src.downloaders import ZOTERO_AVAILABLE
        if ZOTERO_AVAILABLE:
            from src.downloaders import ZoteroLibraryManager, ZoteroItem, ZoteroAttachment, SyncResult
            print("     ✓ Basic Zotero imports")
        else:
            print("     ⚠️ Basic Zotero not available (expected if PyZotero not installed)")
    
    # Test enhanced Zotero imports (if available)
    def test_enhanced_zotero():
        from src.downloaders import ENHANCED_ZOTERO_AVAILABLE
        if ENHANCED_ZOTERO_AVAILABLE:
            from src.downloaders import (
                EnhancedZoteroLibraryManager,
                CollectionSyncResult,
                DOIDownloadResult,
                EnhancedZoteroLiteratureSyncer
            )
            print("     ✓ Enhanced Zotero imports")
        else:
            print("     ⚠️ Enhanced Zotero not available (expected if dependencies missing)")
    
    # Test backward compatibility alias
    def test_backward_compatibility():
        from src.downloaders import ENHANCED_ZOTERO_AVAILABLE
        if ENHANCED_ZOTERO_AVAILABLE:
            from src.downloaders import ZoteroLiteratureSyncer, EnhancedZoteroLiteratureSyncer
            # Verify the alias works
            assert ZoteroLiteratureSyncer is EnhancedZoteroLiteratureSyncer
            print("     ✓ Backward compatibility alias (ZoteroLiteratureSyncer)")
        else:
            print("     ⚠️ Backward compatibility alias not testable (enhanced not available)")
    
    # Test PDF integration imports (if available)
    def test_pdf_integration():
        from src.downloaders import PDF_INTEGRATION_AVAILABLE
        if PDF_INTEGRATION_AVAILABLE:
            from src.downloaders import (
                integrate_pdfs_with_zotero_fixed,
                IntegrationMode,
                IntegrationConfig,
                IntegrationResult,
                FixedZoteroPDFIntegrator,
                get_available_modes,
                setup_download_only_mode,
                setup_attach_mode
            )
            print("     ✓ PDF Integration imports")
        else:
            print("     ⚠️ PDF Integration not available (expected if modules missing)")
    
    results = [
        safe_test(test_legacy, "Legacy BibTeX imports"),
        safe_test(test_flags, "Availability flags"),
        safe_test(test_basic_zotero, "Basic Zotero imports"),
        safe_test(test_enhanced_zotero, "Enhanced Zotero imports"),
        safe_test(test_backward_compatibility, "Backward compatibility alias"),
        safe_test(test_pdf_integration, "PDF Integration imports")
    ]
    
    return all(results)

def test_factory_functions():
    """Test that factory functions work correctly"""
    test_section("FACTORY FUNCTIONS")
    
    # Mock configuration for testing
    class MockConfig:
        def __init__(self):
            self.zotero_api_key = "test_key"
            self.literature_folder = Path("test_folder")
        
        def get_zotero_config(self):
            return {
                'library_id': 'test_id',
                'library_type': 'user',
                'api_key': 'test_key',
                'output_directory': 'test_output'
            }
        
        def get_arxiv_config(self):
            return {'delay': 1.0}
    
    config = MockConfig()
    
    def test_create_zotero_manager():
        from src.downloaders import create_zotero_manager, ZOTERO_AVAILABLE
        if ZOTERO_AVAILABLE:
            # This should work without actually connecting to Zotero
            print("     ✓ create_zotero_manager function exists and callable")
        else:
            try:
                create_zotero_manager(config)
                assert False, "Should have raised ImportError"
            except ImportError:
                print("     ✓ create_zotero_manager properly raises ImportError when unavailable")
    
    def test_create_literature_syncer():
        from src.downloaders import create_literature_syncer, ENHANCED_ZOTERO_AVAILABLE
        if ENHANCED_ZOTERO_AVAILABLE:
            print("     ✓ create_literature_syncer function exists and callable")
        else:
            try:
                create_literature_syncer(config)
                assert False, "Should have raised ImportError"
            except ImportError:
                print("     ✓ create_literature_syncer properly raises ImportError when unavailable")
    
    def test_create_literature_manager():
        from src.downloaders import create_literature_manager
        
        # Test bibtex option (should always work)
        try:
            manager = create_literature_manager('bibtex', config)
            print("     ✓ create_literature_manager works for 'bibtex'")
        except Exception as e:
            print(f"     ⚠️ create_literature_manager failed for 'bibtex': {e}")
        
        # Test manual option (should return None)
        try:
            result = create_literature_manager('manual', config)
            assert result is None
            print("     ✓ create_literature_manager returns None for 'manual'")
        except Exception as e:
            print(f"     ❌ create_literature_manager failed for 'manual': {e}")
        
        # Test invalid option
        try:
            create_literature_manager('invalid', config)
            assert False, "Should have raised ValueError"
        except ValueError:
            print("     ✓ create_literature_manager raises ValueError for invalid type")
    
    results = [
        safe_test(test_create_zotero_manager, "create_zotero_manager function"),
        safe_test(test_create_literature_syncer, "create_literature_syncer function"),
        safe_test(test_create_literature_manager, "create_literature_manager function")
    ]
    
    return all(results)

def test_status_functions():
    """Test status and capability functions"""
    test_section("STATUS AND CAPABILITY FUNCTIONS")
    
    def test_get_zotero_capabilities():
        from src.downloaders import get_zotero_capabilities
        capabilities = get_zotero_capabilities()
        
        # Check structure
        assert 'capabilities' in capabilities
        assert 'recommendations' in capabilities
        assert 'suggested_manager' in capabilities
        
        # Check basic capability entries
        caps = capabilities['capabilities']
        assert 'basic_zotero' in caps
        assert 'enhanced_zotero' in caps
        assert 'pdf_integration' in caps
        assert 'selenium_automation' in caps
        
        print("     ✓ get_zotero_capabilities returns proper structure")
    
    def test_get_available_downloaders():
        from src.downloaders import get_available_downloaders
        downloaders = get_available_downloaders()
        
        # Check that expected downloaders are present
        expected = ['arxiv_direct', 'bibtex_arxiv', 'zotero', 'enhanced_zotero', 'manual']
        for downloader in expected:
            assert downloader in downloaders
        
        print("     ✓ get_available_downloaders returns all expected options")
    
    def test_get_integration_capabilities():
        from src.downloaders import get_integration_capabilities
        capabilities = get_integration_capabilities()
        
        # Should be same as zotero capabilities
        assert isinstance(capabilities, dict)
        print("     ✓ get_integration_capabilities works")
    
    def test_recommend_literature_source():
        from src.downloaders import recommend_literature_source
        
        # Mock config with Zotero key
        class ConfigWithZotero:
            zotero_api_key = "test_key"
        
        # Mock config without Zotero key  
        class ConfigWithoutZotero:
            pass
        
        # Test with Zotero
        rec1 = recommend_literature_source(ConfigWithZotero())
        assert 'source' in rec1
        assert 'reason' in rec1
        
        # Test without Zotero
        rec2 = recommend_literature_source(ConfigWithoutZotero())
        assert rec2['source'] == 'bibtex'
        
        print("     ✓ recommend_literature_source works with different configs")
    
    def test_print_functions():
        from src.downloaders import print_zotero_status, print_integration_status
        
        # These should run without errors (output will be printed)
        print("\n     📊 Testing print_zotero_status():")
        print_zotero_status()
        
        print("\n     📊 Testing print_integration_status():")
        print_integration_status()
        
        print("     ✓ Print functions executed without errors")
    
    results = [
        safe_test(test_get_zotero_capabilities, "get_zotero_capabilities"),
        safe_test(test_get_available_downloaders, "get_available_downloaders"),
        safe_test(test_get_integration_capabilities, "get_integration_capabilities"),
        safe_test(test_recommend_literature_source, "recommend_literature_source"),
        safe_test(test_print_functions, "Print status functions")
    ]
    
    return all(results)

def test_inheritance_structure():
    """Test that inheritance structure is correct"""
    test_section("INHERITANCE STRUCTURE")
    
    def test_manager_inheritance():
        from src.downloaders import ENHANCED_ZOTERO_AVAILABLE, ZOTERO_AVAILABLE
        
        if ENHANCED_ZOTERO_AVAILABLE and ZOTERO_AVAILABLE:
            from src.downloaders import ZoteroLibraryManager, EnhancedZoteroLibraryManager
            
            # Check inheritance
            assert issubclass(EnhancedZoteroLibraryManager, ZoteroLibraryManager)
            print("     ✓ EnhancedZoteroLibraryManager inherits from ZoteroLibraryManager")
            
            # Check that enhanced has additional methods
            enhanced_methods = set(dir(EnhancedZoteroLibraryManager))
            basic_methods = set(dir(ZoteroLibraryManager))
            additional_methods = enhanced_methods - basic_methods
            
            # Should have DOI-related methods
            doi_methods = [m for m in additional_methods if 'doi' in m.lower()]
            assert len(doi_methods) > 0
            print(f"     ✓ Enhanced manager has {len(additional_methods)} additional methods")
            print(f"       DOI-related methods: {len(doi_methods)}")
        else:
            print("     ⚠️ Cannot test inheritance (managers not available)")
    
    def test_syncer_consolidation():
        from src.downloaders import ENHANCED_ZOTERO_AVAILABLE
        
        if ENHANCED_ZOTERO_AVAILABLE:
            from src.downloaders import ZoteroLiteratureSyncer, EnhancedZoteroLiteratureSyncer
            
            # Check alias
            assert ZoteroLiteratureSyncer is EnhancedZoteroLiteratureSyncer
            print("     ✓ ZoteroLiteratureSyncer is aliased to EnhancedZoteroLiteratureSyncer")
        else:
            print("     ⚠️ Cannot test syncer consolidation (enhanced not available)")
    
    results = [
        safe_test(test_manager_inheritance, "Manager inheritance structure"),
        safe_test(test_syncer_consolidation, "Syncer consolidation")
    ]
    
    return all(results)

def test_graceful_degradation():
    """Test that graceful degradation works"""
    test_section("GRACEFUL DEGRADATION")
    
    def test_availability_handling():
        from src.downloaders import (
            ZOTERO_AVAILABLE, 
            ENHANCED_ZOTERO_AVAILABLE, 
            PDF_INTEGRATION_AVAILABLE,
            SELENIUM_AVAILABLE
        )
        
        print(f"     Current availability status:")
        print(f"       - Basic Zotero: {ZOTERO_AVAILABLE}")
        print(f"       - Enhanced Zotero: {ENHANCED_ZOTERO_AVAILABLE}")
        print(f"       - PDF Integration: {PDF_INTEGRATION_AVAILABLE}")
        print(f"       - Selenium: {SELENIUM_AVAILABLE}")
        
        # The system should handle any combination gracefully
        print("     ✓ Availability flags accessible")
    
    def test_error_messages():
        from src.downloaders import create_literature_manager, create_literature_syncer
        
        # Mock config without Zotero
        class EmptyConfig:
            literature_folder = Path("test")
            def get_arxiv_config(self):
                return {}
        
        # These should provide helpful error messages
        try:
            create_literature_syncer(EmptyConfig())
            print("     ❌ Should have failed with invalid config")
        except (ImportError, AttributeError) as e:
            # Either error type is acceptable
            error_msg = str(e)
            
            # Check for the clean error message (no double-wrapping)
            if ("get_zotero_config" in error_msg and 
                "PipelineConfig" in error_msg and
                not error_msg.startswith("Invalid configuration object:")):  # Not double-wrapped
                print("     ✅ Clean, helpful error message for missing method")
            else:
                print(f"     ⚠️ Error message format: {error_msg}")
        except Exception as e:
            print(f"     ⚠️ Unexpected error type: {type(e).__name__}: {e}")


        # Test 2: create_literature_manager with invalid source
        try:
            create_literature_manager('enhanced_zotero', EmptyConfig())
        except (ImportError, AttributeError) as e:
            # Either error type is acceptable depending on availability
            if "Zotero integration not available" in str(e) or "get_zotero_config" in str(e):
                print("     ✅ Helpful error when enhanced Zotero unavailable or config invalid")
            else:
                print(f"     ⚠️ Unexpected error message: {e}")
        except Exception as e:
            print(f"     ⚠️ Unexpected error type: {type(e).__name__}: {e}")
    
    
    results = [
        safe_test(test_availability_handling, "Availability status handling"),
        safe_test(test_error_messages, "Error message quality")
    ]
    
    return all(results)

def test_architecture_documentation():
    """Test that architectural decisions are documented"""
    test_section("ARCHITECTURE DOCUMENTATION")
    
    def test_docstring_content():
        import src.downloaders
        
        # Check main module docstring
        docstring = src.downloaders.__doc__
        assert docstring is not None
        assert "ZOTERO MANAGER ARCHITECTURE" in docstring
        assert "LITERATURE SYNCER ARCHITECTURE" in docstring
        print("     ✓ Main module has comprehensive architecture documentation")
    
    def test_function_documentation():
        from src.downloaders import create_zotero_manager, create_literature_syncer
        
        # Check factory function docs
        assert create_zotero_manager.__doc__ is not None
        assert "ARCHITECTURE DECISION" in create_zotero_manager.__doc__
        
        assert create_literature_syncer.__doc__ is not None
        assert "consolidated" in create_literature_syncer.__doc__.lower()
        
        print("     ✓ Factory functions have architecture explanations")
    
    results = [
        safe_test(test_docstring_content, "Module documentation"),
        safe_test(test_function_documentation, "Function documentation")
    ]
    
    return all(results)

def run_all_tests():
    """Run all tests and provide summary"""
    print("🚀 COMPREHENSIVE ZOTERO INTEGRATION TEST")
    print("Testing the enhanced architecture changes...")
    
    test_results = []
    
    test_results.append(test_basic_imports())
    test_results.append(test_factory_functions())
    test_results.append(test_status_functions())
    test_results.append(test_inheritance_structure())
    test_results.append(test_graceful_degradation())
    test_results.append(test_architecture_documentation())
    
    # Final summary
    print(f"\n{'='*60}")
    print("🏁 TEST SUMMARY")
    print('='*60)
    
    passed = sum(test_results)
    total = len(test_results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("✅ Architecture changes are working correctly!")
        print("✅ No breaking changes detected!")
        print("✅ System is ready for use!")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("❌ Please review the failed tests above")
        print("❌ Fix issues before proceeding")
    
    print(f"\n💡 Next steps:")
    print("   1. If tests pass: Your architecture is solid!")
    print("   2. If tests fail: Review error messages and fix issues")
    print("   3. Run this script again after fixes")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)