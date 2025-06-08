# Setup Script for Modular Zotero PDF Integrator
# File: setup_modular_integrator.py
# Run this script to create the modular file structure

import os
from pathlib import Path

def create_modular_structure():
    """Create the directory structure and files for modular assembly."""
    
    print("🏗️  Setting up modular Zotero PDF integrator structure...")
    
    # Define the base directory
    base_dir = Path("src/downloaders")
    parts_dir = base_dir / "zotero_pdf_integrator_parts"
    
    # Create directories
    parts_dir.mkdir(parents=True, exist_ok=True)
    
    # Create __init__.py files
    init_files = [
        base_dir / "__init__.py",
        parts_dir / "__init__.py"
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.write_text("# Auto-generated __init__.py\n")
            print(f"   ✅ Created: {init_file}")
    
    # Define all the files that need to be created
    files_to_create = [
        {
            'path': parts_dir / "part1_core_classes.py",
            'description': "Core classes and enums",
            'artifact': "part1_modular"
        },
        {
            'path': parts_dir / "part2_main_class.py", 
            'description': "Main integrator class",
            'artifact': "part2_modular"
        },
        {
            'path': parts_dir / "part3_mode_implementations.py",
            'description': "Mode implementation functions",
            'artifact': "part3_modular"
        },
        {
            'path': parts_dir / "part4_attachment_methods.py",
            'description': "Attachment methods",
            'artifact': "attachment_methods"  # From the original artifact
        },
        {
            'path': parts_dir / "part5_upload_replace_methods.py",
            'description': "Upload and replace methods", 
            'artifact': "upload_replace_methods"  # From the original artifact
        },
        {
            'path': parts_dir / "part6_main_function.py",
            'description': "Main integration function",
            'artifact': "main_integration_function"  # From the original artifact
        },
        {
            'path': base_dir / "zotero_pdf_integrator_fixed.py",
            'description': "Main assembly file",
            'artifact': "modular_assembly_main"
        }
    ]
    
    print(f"\n📁 Directory structure:")
    print(f"   {base_dir}/")
    print(f"   ├── zotero_pdf_integrator_fixed.py")
    print(f"   └── zotero_pdf_integrator_parts/")
    print(f"       ├── __init__.py")
    print(f"       ├── part1_core_classes.py")
    print(f"       ├── part2_main_class.py")
    print(f"       ├── part3_mode_implementations.py")
    print(f"       ├── part4_attachment_methods.py")
    print(f"       ├── part5_upload_replace_methods.py")
    print(f"       └── part6_main_function.py")
    
    print(f"\n📝 Files to create manually:")
    for file_info in files_to_create:
        status = "✅ Exists" if file_info['path'].exists() else "📝 Need to create"
        print(f"   {status} | {file_info['path'].name} - {file_info['description']}")
    
    return files_to_create

def create_test_script():
    """Create a test script for the modular assembly."""
    
    test_script_content = '''# Test Script for Modular Assembly
# File: test_modular_assembly.py

import sys
from pathlib import Path

# Add project root to path
project_root = Path.cwd()
if project_root.name != "physics_synthesis":
    project_root = project_root.parent
sys.path.insert(0, str(project_root))

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
        print("\\n🔧 Testing basic functionality...")
        
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
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("💡 Make sure all part files are created properly")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_individual_parts():
    """Test each part individually."""
    
    print("\\n🧪 TESTING INDIVIDUAL PARTS")
    print("=" * 50)
    
    parts_to_test = [
        ("Part 1", "src.downloaders.zotero_pdf_integrator_parts.part1_core_classes"),
        ("Part 2", "src.downloaders.zotero_pdf_integrator_parts.part2_main_class"),
        ("Part 3", "src.downloaders.zotero_pdf_integrator_parts.part3_mode_implementations"),
    ]
    
    results = {}
    
    for part_name, module_name in parts_to_test:
        try:
            import importlib
            module = importlib.import_module(module_name)
            
            # Run the test function if it exists
            if hasattr(module, f'test_{module_name.split(".")[-1].replace("part", "part")}'):
                test_func = getattr(module, f'test_{module_name.split(".")[-1]}')
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

if __name__ == "__main__":
    print("🚀 COMPREHENSIVE MODULAR ASSEMBLY TEST")
    print("=" * 60)
    
    # Test individual parts first
    part_results = test_individual_parts()
    
    # Test full assembly
    assembly_success = test_modular_import()
    
    # Summary
    print("\\n" + "="*60)
    print("📊 FINAL TEST SUMMARY")
    print("="*60)
    
    total_parts = len(part_results)
    passed_parts = sum(1 for result in part_results.values() if result)
    
    print(f"📋 Individual Parts: {passed_parts}/{total_parts} passed")
    for part, success in part_results.items():
        status = "✅" if success else "❌"
        print(f"   {status} {part}")
    
    print(f"\\n🔧 Full Assembly: {'✅ PASSED' if assembly_success else '❌ FAILED'}")
    
    if assembly_success and passed_parts == total_parts:
        print("\\n🎉 ALL TESTS PASSED - MODULAR ASSEMBLY READY!")
        print("🚀 You can now use the integrator in your pipeline")
    else:
        print("\\n🔧 Some issues found - check individual part errors above")
        print("💡 Fix failing parts and re-run this test")
'''
    
    test_file = Path("test_modular_assembly.py")
    test_file.write_text(test_script_content)
    print(f"✅ Created test script: {test_file}")
    
    return test_file

def print_next_steps():
    """Print the next steps for setting up the modular assembly."""
    
    print(f"\n🎯 NEXT STEPS TO COMPLETE MODULAR SETUP:")
    print("=" * 60)
    
    print(f"1. 📁 Create the files manually:")
    print(f"   Copy content from the artifacts I provided above:")
    print(f"   • part1_modular → part1_core_classes.py")
    print(f"   • part2_modular → part2_main_class.py") 
    print(f"   • part3_modular → part3_mode_implementations.py")
    print(f"   • attachment_methods → part4_attachment_methods.py")
    print(f"   • upload_replace_methods → part5_upload_replace_methods.py") 
    print(f"   • main_integration_function → part6_main_function.py")
    print(f"   • modular_assembly_main → zotero_pdf_integrator_fixed.py")
    
    print(f"\\n2. 🧪 Test the assembly:")
    print(f"   python test_modular_assembly.py")
    
    print(f"\\n3. 🔧 Debug any issues:")
    print(f"   The test script will show exactly which parts fail")
    
    print(f"\\n4. 🚀 Use in your pipeline:")
    print(f"   from src.downloaders.zotero_pdf_integrator_fixed import integrate_pdfs_with_zotero_fixed")
    
    print(f"\\n💡 Benefits of modular approach:")
    print(f"   ✅ Easy to test individual components")
    print(f"   ✅ Easy to debug specific issues") 
    print(f"   ✅ Easy to modify one part without affecting others")
    print(f"   ✅ Can combine into single file later if desired")

def main():
    """Main setup function."""
    
    print("🏗️  MODULAR ZOTERO PDF INTEGRATOR SETUP")
    print("=" * 60)
    
    # Create directory structure
    files_to_create = create_modular_structure()
    
    # Create test script
    test_file = create_test_script()
    
    # Print next steps
    print_next_steps()
    
    print(f"\\n✅ Setup complete! Directory structure created.")
    print(f"📝 Now copy the content from the artifacts to create the individual files.")

if __name__ == "__main__":
    main()