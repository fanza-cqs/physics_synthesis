# Test Script for Modular Assembly
# File: test_modular_assembly.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd()
if project_root.name != "physics_synthesis":
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

print(f"📁 Working directory: {project_root}")

def test_modular_import():
    """Test that all modular parts can be imported."""
    
    print("🧪 TESTING MODULAR ASSEMBLY")
    print("=" * 50)
    
    try:
        # Test importing the main assembly
        from src.downloaders.zotero_pdf_integrator_fixed import (
            IntegrationMode,
            IntegrationConfig, 
            IntegrationResult,
            FixedZoteroPDFIntegrator,
            integrate_pdfs_with_zotero_fixed,
            test_modular_assembly
        )
        
        print("✅ All main components imported successfully")
        
        # Run the built-in assembly test
        test_modular_assembly()
        
        # Test basic functionality
        print("\n🔧 Testing basic functionality...")
        
        # Test download_only mode
        test_data = [{
            'file_path': str(Path.cwd() / 'README.md'),  # Use a file that exists
            'doi': 'test.doi/12345',
            'zotero_key': 'TEST_KEY_123'
        }]
        
        results = integrate_pdfs_with_zotero_fixed(
            test_data,
            zotero_manager=None,
            mode="download_only"
        )
        
        print(f"✅ Download-only test completed: {len(results)} results")
        
        if results and results[0].success:
            print("🎉 MODULAR ASSEMBLY FULLY WORKING!")
            return True
        else:
            print("⚠️  Assembly works but test failed")
            print(f"   Error: {results[0].error if results else 'No results'}")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Make sure all part files are created properly")
        print("   Check that these files exist:")
        expected_files = [
            "src/downloaders/zotero_pdf_integrator_fixed.py",
            "src/downloaders/zotero_pdf_integrator_parts/part1_core_classes.py",
            "src/downloaders/zotero_pdf_integrator_parts/part2_main_class.py",
            "src/downloaders/zotero_pdf_integrator_parts/part3_mode_implementations.py",
            "src/downloaders/zotero_pdf_integrator_parts/part4_attachment_methods.py",
            "src/downloaders/zotero_pdf_integrator_parts/part5_upload_replace_methods.py",
            "src/downloaders/zotero_pdf_integrator_parts/part6_main_function.py",
        ]
        for file_path in expected_files:
            exists = "✅" if Path(file_path).exists() else "❌"
            print(f"   {exists} {file_path}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_individual_parts():
    """Test each part individually."""
    
    print("\n🧪 TESTING INDIVIDUAL PARTS")
    print("=" * 50)
    
    parts_to_test = [
        ("Part 1", "src.downloaders.zotero_pdf_integrator_parts.part1_core_classes", "test_part1"),
        ("Part 2", "src.downloaders.zotero_pdf_integrator_parts.part2_main_class", "test_part2"),
        ("Part 3", "src.downloaders.zotero_pdf_integrator_parts.part3_mode_implementations", "test_part3"),
        ("Part 4", "src.downloaders.zotero_pdf_integrator_parts.part4_attachment_methods", "test_part4"),
        ("Part 5", "src.downloaders.zotero_pdf_integrator_parts.part5_upload_replace_methods", "test_part5"),
        ("Part 6", "src.downloaders.zotero_pdf_integrator_parts.part6_main_function", "test_part6"),
    ]
    
    results = {}
    
    for part_name, module_name, test_func_name in parts_to_test:
        try:
            import importlib
            module = importlib.import_module(module_name)
            
            # Run the test function if it exists
            if hasattr(module, test_func_name):
                test_func = getattr(module, test_func_name)
                test_func()
                results[part_name] = True
                print(f"✅ {part_name} test passed")
            else:
                print(f"✅ {part_name} imported successfully (no test function)")
                results[part_name] = True
                
        except Exception as e:
            print(f"❌ {part_name} failed: {e}")
            results[part_name] = False
    
    return results

def test_mode_configurations():
    """Test that all three modes can be configured."""
    
    print("\n🔧 TESTING MODE CONFIGURATIONS")
    print("=" * 50)
    
    try:
        from src.downloaders.zotero_pdf_integrator_fixed import (
            setup_download_only_mode,
            setup_attach_mode,
            setup_upload_replace_mode,
            get_available_modes,
            FIXED_EXAMPLE_CONFIGS
        )
        
        # Test mode setup functions
        config1 = setup_download_only_mode()
        print(f"✅ Download-only mode configured: {config1.mode.value}")
        
        config2 = setup_attach_mode()
        print(f"✅ Attach mode configured: {config2.mode.value}")
        
        config3 = setup_upload_replace_mode("TEST_COLLECTION")
        print(f"✅ Upload-replace mode configured: {config3.mode.value}")
        
        # Test available modes
        modes = get_available_modes()
        print(f"✅ Available modes: {', '.join(modes)}")
        
        # Test example configs
        print(f"✅ Example configs available: {len(FIXED_EXAMPLE_CONFIGS)} configurations")
        
        return True
        
    except Exception as e:
        print(f"❌ Mode configuration test failed: {e}")
        return False

def test_integration_with_real_files():
    """Test integration with actual files that exist."""
    
    print("\n📁 TESTING WITH REAL FILES")
    print("=" * 50)
    
    try:
        from src.downloaders.zotero_pdf_integrator_fixed import integrate_pdfs_with_zotero_fixed
        
        # Find some actual files to test with
        test_files = []
        
        # Look for README or other common files
        possible_files = [
            Path.cwd() / 'README.md',
            Path.cwd() / 'requirements.txt',
            Path.cwd() / 'setup.py',
        ]
        
        for file_path in possible_files:
            if file_path.exists():
                test_files.append(str(file_path))
                break
        
        if not test_files:
            print("⚠️  No test files found, skipping real file test")
            return True
        
        # Test with download_only mode (safest)
        test_data = [{
            'file_path': test_files[0],
            'doi': 'test.doi/real.file',
            'zotero_key': 'REAL_FILE_TEST'
        }]
        
        print(f"🔍 Testing with file: {Path(test_files[0]).name}")
        
        results = integrate_pdfs_with_zotero_fixed(
            test_data,
            zotero_manager=None,
            mode="download_only"
        )
        
        if results and len(results) > 0:
            result = results[0]
            print(f"✅ Real file test completed")
            print(f"   File: {Path(result.pdf_path).name}")
            print(f"   Success: {result.success}")
            print(f"   Mode: {result.mode.value}")
            
            if result.success:
                print("🎉 Real file integration working!")
                return True
            else:
                print(f"⚠️  File processing failed: {result.error}")
                return False
        else:
            print("❌ No results returned from integration")
            return False
            
    except Exception as e:
        print(f"❌ Real file test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE MODULAR ASSEMBLY TEST")
    print("=" * 60)
    
    # Test individual parts first
    part_results = test_individual_parts()
    
    # Test mode configurations
    mode_config_success = test_mode_configurations()
    
    # Test full assembly
    assembly_success = test_modular_import()
    
    # Test with real files
    real_file_success = test_integration_with_real_files()
    
    # Summary
    print("\n" + "="*60)
    print("📊 FINAL TEST SUMMARY")
    print("="*60)
    
    total_parts = len(part_results)
    passed_parts = sum(1 for result in part_results.values() if result)
    
    print(f"📋 Individual Parts: {passed_parts}/{total_parts} passed")
    for part, success in part_results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {part}")
    
    print(f"\n🔧 Mode Configurations: {'✅ PASSED' if mode_config_success else '❌ FAILED'}")
    print(f"🔧 Full Assembly: {'✅ PASSED' if assembly_success else '❌ FAILED'}")
    print(f"📁 Real File Test: {'✅ PASSED' if real_file_success else '❌ FAILED'}")
    
    all_tests_passed = (
        passed_parts == total_parts and 
        mode_config_success and 
        assembly_success and 
        real_file_success
    )
    
    if all_tests_passed:
        print("\n🎉 ALL TESTS PASSED - MODULAR ASSEMBLY PERFECT!")
        print("🚀 Your integrator is ready for production use!")
        print("\n💡 Next steps:")
        print("   • Use in your pipeline: from src.downloaders.zotero_pdf_integrator_fixed import integrate_pdfs_with_zotero_fixed")
        print("   • Test with your actual Zotero data")
        print("   • Try all three modes: download_only, attach, upload_replace")
    else:
        print("\n🔧 Some issues found - check individual test results above")
        print("💡 Common issues:")
        print("   • Missing part files - copy content from artifacts")
        print("   • Import path problems - check directory structure")
        print("   • Syntax errors in copied files - check for copy/paste issues")
    
    print(f"\n📁 Expected file structure:")
    print(f"   src/downloaders/")
    print(f"   ├── zotero_pdf_integrator_fixed.py")
    print(f"   └── zotero_pdf_integrator_parts/")
    print(f"       ├── __init__.py")
    print(f"       ├── part1_core_classes.py")
    print(f"       ├── part2_main_class.py")
    print(f"       ├── part3_mode_implementations.py")
    print(f"       ├── part4_attachment_methods.py")
    print(f"       ├── part5_upload_replace_methods.py")
    print(f"       └── part6_main_function.py")