#!/usr/bin/env python3
"""
Physics Synthesis Pipeline - System Diagnostic Script
Run this to identify and fix common issues before starting the app
"""

import sys
import os
from pathlib import Path
import importlib.util

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def check_directory_structure():
    """Check if required directories exist"""
    print_section("Directory Structure Check")
    
    current_dir = Path.cwd()
    print(f"Current directory: {current_dir}")
    
    required_dirs = ['config', 'src', 'frontend_streamlit']
    optional_dirs = ['sessions', 'knowledge_bases', 'zotero_data']
    
    all_good = True
    
    for dir_name in required_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ - EXISTS")
        else:
            print(f"❌ {dir_name}/ - MISSING")
            all_good = False
    
    for dir_name in optional_dirs:
        dir_path = current_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name}/ - EXISTS")
        else:
            print(f"⚠️  {dir_name}/ - MISSING (will be created)")
            try:
                dir_path.mkdir(exist_ok=True)
                print(f"   Created {dir_name}/")
            except Exception as e:
                print(f"   Failed to create {dir_name}/: {e}")
    
    return all_good

def test_python_path():
    """Test if project root is in Python path"""
    print_section("Python Path Configuration")
    
    current_dir = Path.cwd()
    
    # Find project root (directory with config/ and src/)
    project_root = None
    for parent in [current_dir] + list(current_dir.parents):
        if (parent / "config").exists() and (parent / "src").exists():
            project_root = parent
            break
    
    if project_root:
        print(f"✅ Project root found: {project_root}")
        
        # Add to Python path if not already there
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))
            print(f"✅ Added {project_root} to Python path")
        else:
            print(f"✅ Project root already in Python path")
        
        return project_root
    else:
        print(f"❌ Project root not found. Make sure you're in the physics_synthesis_pipeline directory")
        return None

def test_imports():
    """Test critical module imports"""
    print_section("Import Tests")
    
    imports_to_test = [
        ('config', 'PipelineConfig'),
        ('src.sessions', 'SessionManager'),
        ('src.ui', 'Sidebar'),
        ('src.ui', 'ChatInterface'),
        ('src.chat', 'LiteratureAssistant'),
        ('src.core', 'list_knowledge_bases'),
        ('src.downloaders', 'create_zotero_manager'),
    ]
    
    enhanced_imports = [
        ('src.ui.enhanced_sidebar', 'EnhancedSidebar'),
        ('src.ui.enhanced_chat_interface', 'EnhancedChatInterface'),
        ('src.sessions.session_integration', 'get_session_integration'),
    ]
    
    results = {}
    
    # Test basic imports
    for module_name, class_name in imports_to_test:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name} - OK")
                results[f"{module_name}.{class_name}"] = True
            else:
                print(f"⚠️  {module_name}.{class_name} - MODULE OK, CLASS MISSING")
                results[f"{module_name}.{class_name}"] = False
        except ImportError as e:
            print(f"❌ {module_name}.{class_name} - IMPORT FAILED: {e}")
            results[f"{module_name}.{class_name}"] = False
        except Exception as e:
            print(f"❌ {module_name}.{class_name} - ERROR: {e}")
            results[f"{module_name}.{class_name}"] = False
    
    # Test enhanced imports (optional)
    print(f"\n📊 Enhanced Components (Optional):")
    for module_name, class_name in enhanced_imports:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, class_name):
                print(f"✅ {module_name}.{class_name} - OK")
                results[f"enhanced.{module_name}.{class_name}"] = True
            else:
                print(f"⚠️  {module_name}.{class_name} - MODULE OK, CLASS MISSING")
                results[f"enhanced.{module_name}.{class_name}"] = False
        except ImportError as e:
            print(f"⚠️  {module_name}.{class_name} - NOT AVAILABLE: {e}")
            results[f"enhanced.{module_name}.{class_name}"] = False
        except Exception as e:
            print(f"❌ {module_name}.{class_name} - ERROR: {e}")
            results[f"enhanced.{module_name}.{class_name}"] = False
    
    return results

def check_dependencies():
    """Check if required dependencies are installed"""
    print_section("Dependency Check")
    
    required_packages = [
        'streamlit',
        'anthropic',
        'chromadb',
        'sentence_transformers',
        'torch',
        'transformers',
        'pyzotero',
        'pathlib',
        'json',
        'datetime'
    ]
    
    optional_packages = [
        'selenium',
        'beautifulsoup4',
        'requests',
        'numpy',
        'pandas'
    ]
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - INSTALLED")
        except ImportError:
            print(f"❌ {package} - MISSING (required)")
    
    print(f"\n📦 Optional packages:")
    for package in optional_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - INSTALLED")
        except ImportError:
            print(f"⚠️  {package} - NOT INSTALLED (optional)")

def check_config_files():
    """Check if configuration files exist and are valid"""
    print_section("Configuration Files")
    
    try:
        from config import PipelineConfig
        config = PipelineConfig()
        print(f"✅ Configuration loaded successfully")
        
        # Check for API keys (without revealing them)
        if hasattr(config, 'anthropic_api_key') and config.anthropic_api_key:
            print(f"✅ Anthropic API key configured")
        else:
            print(f"⚠️  Anthropic API key not configured")
        
        if hasattr(config, 'zotero_api_key') and config.zotero_api_key:
            print(f"✅ Zotero API key configured")
        else:
            print(f"⚠️  Zotero API key not configured")
            
    except Exception as e:
        print(f"❌ Configuration error: {e}")

def test_session_system():
    """Test basic session system functionality"""
    print_section("Session System Test")
    
    try:
        from src.sessions import SessionManager
        
        # Test session manager creation
        session_manager = SessionManager(Path.cwd())
        print(f"✅ SessionManager created successfully")
        
        # Test session creation
        session = session_manager.create_session("Test Session")
        print(f"✅ Test session created: {session.id}")
        
        # Test session persistence
        if session_manager.storage.save_session(session):
            print(f"✅ Session saved successfully")
        else:
            print(f"❌ Session save failed")
        
        # Clean up test session
        session_manager.delete_session(session.id)
        print(f"✅ Test session cleaned up")
        
    except Exception as e:
        print(f"❌ Session system test failed: {e}")

def generate_recommendations():
    """Generate recommendations based on test results"""
    print_section("Recommendations")
    
    print("Based on the diagnostic results:")
    print()
    
    print("🚀 To start the application:")
    print("1. Navigate to frontend_streamlit/")
    print("2. Run: streamlit run app_sessions.py")
    print()
    
    print("🔧 If you see import errors:")
    print("1. Make sure you're in the physics_synthesis_pipeline root directory")
    print("2. Check that all required directories exist")
    print("3. Install missing dependencies with pip")
    print()
    
    print("⚡ For enhanced features:")
    print("1. If enhanced components work, try: streamlit run app_sessions_final.py")
    print("2. If not, stick with app_sessions.py")
    print()
    
    print("🧪 For testing:")
    print("1. Start with basic functionality (session creation)")
    print("2. Test knowledge base features")
    print("3. Test document upload")
    print("4. Configure API keys for chat features")

def main():
    """Run complete system diagnostic"""
    print("🔬 Physics Synthesis Pipeline - System Diagnostic")
    print(f"Python version: {sys.version}")
    print(f"Current working directory: {Path.cwd()}")
    
    # Run all checks
    dir_ok = check_directory_structure()
    project_root = test_python_path()
    
    if not project_root:
        print("\n❌ Cannot continue without finding project root")
        return
    
    import_results = test_imports()
    check_dependencies()
    check_config_files()
    test_session_system()
    generate_recommendations()
    
    # Summary
    print_section("Summary")
    basic_imports_ok = all(v for k, v in import_results.items() if not k.startswith('enhanced.'))
    enhanced_imports_ok = all(v for k, v in import_results.items() if k.startswith('enhanced.'))
    
    if dir_ok and basic_imports_ok:
        print("🎉 BASIC SYSTEM: READY TO GO!")
        print("   You can start with: streamlit run app_sessions.py")
    else:
        print("⚠️  BASIC SYSTEM: NEEDS ATTENTION")
        print("   Fix import errors before starting")
    
    if enhanced_imports_ok:
        print("🚀 ENHANCED SYSTEM: AVAILABLE!")
        print("   You can use: streamlit run app_sessions_final.py")
    else:
        print("📋 ENHANCED SYSTEM: NOT AVAILABLE")
        print("   Use basic app for now")

if __name__ == "__main__":
    main()