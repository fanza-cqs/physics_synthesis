#!/usr/bin/env python3
"""
Setup Check Script for Physics Literature RAG System

This script verifies that your environment is properly configured
and provides guidance for any missing components.

Location: scripts/check_setup.py
"""

import sys
import os
from pathlib import Path

# Set up imports - FIXED for scripts/ directory  
project_root = Path(__file__).parent.parent  # Go up from scripts/ to project root
sys.path.insert(0, str(project_root))

def check_dependencies():
    """Check if required Python packages are installed."""
    print("🔍 CHECKING DEPENDENCIES")
    print("-" * 40)
    
    required_packages = {
        'anthropic': 'Claude AI integration',
        'sentence_transformers': 'Text embeddings',
        'numpy': 'Numerical computing',
        'sklearn': 'Machine learning utilities',  # Fixed: sklearn not scikit-learn
        'pyzotero': 'Zotero integration (optional)',
        'selenium': 'PDF downloads (optional)',
        'PyPDF2': 'PDF processing',
        'fitz': 'Advanced PDF processing (PyMuPDF)',
        'bibtexparser': 'BibTeX parsing'
    }
    
    missing_required = []
    missing_optional = []
    
    for package, description in required_packages.items():
        try:
            if package == 'fitz':
                import fitz
            elif package == 'sklearn':
                import sklearn  # This imports scikit-learn
            else:
                __import__(package)
            print(f"✅ {package:20s} - {description}")
        except ImportError:
            if package in ['pyzotero', 'selenium']:
                missing_optional.append((package, description))
                print(f"⚠️  {package:20s} - {description} (optional)")
            else:
                missing_required.append((package, description))
                print(f"❌ {package:20s} - {description} (REQUIRED)")
    
    return missing_required, missing_optional

def check_configuration():
    """Check configuration and API keys."""
    print(f"\n🔧 CHECKING CONFIGURATION")
    print("-" * 40)
    
    try:
        from config import PipelineConfig
        config = PipelineConfig()
        print(f"✅ Configuration loaded successfully")
        
        # Check directories
        print(f"\n📁 Directory Structure:")
        folders = config.get_document_folders()
        for name, path in folders.items():
            exists = path.exists()
            print(f"   {name:20s}: {'✅' if exists else '❌'} {path}")
            if not exists:
                try:
                    path.mkdir(parents=True, exist_ok=True)
                    print(f"   → Created {path}")
                except Exception as e:
                    print(f"   → Failed to create: {e}")
        
        # Check API keys
        print(f"\n🔑 API Keys:")
        api_status = config.check_env_file()
        
        print(f"   Anthropic API: {'✅' if api_status['anthropic_api_key'] else '❌'}")
        if not api_status['anthropic_api_key']:
            print(f"      → Required for AI assistant")
            print(f"      → Get key at: https://console.anthropic.com/")
            print(f"      → Add to .env: ANTHROPIC_API_KEY=your-key-here")
        
        print(f"   Zotero API: {'✅' if api_status['zotero_configured'] else '⚠️'}")
        if not api_status['zotero_configured']:
            print(f"      → Optional for automatic PDF management")
            print(f"      → Get key at: https://www.zotero.org/settings/keys")
            print(f"      → Add to .env: ZOTERO_API_KEY=your-key")
            print(f"      → Add to .env: ZOTERO_LIBRARY_ID=your-id")
        
        return True, config
        
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False, None

def check_sample_documents(config):
    """Check for sample documents and suggest next steps."""
    print(f"\n📚 CHECKING DOCUMENTS")
    print("-" * 40)
    
    if not config:
        print(f"❌ Cannot check documents (configuration failed)")
        return
    
    # Count documents in each folder
    folders = config.get_document_folders()
    total_docs = 0
    
    for name, path in folders.items():
        if path.exists():
            pdf_files = list(path.glob("*.pdf"))
            txt_files = list(path.glob("*.txt"))
            tex_files = list(path.glob("*.tex"))
            
            folder_total = len(pdf_files) + len(txt_files) + len(tex_files)
            total_docs += folder_total
            
            if folder_total > 0:
                print(f"   {name:20s}: {folder_total} files (PDF: {len(pdf_files)}, TXT: {len(txt_files)}, TEX: {len(tex_files)})")
            else:
                print(f"   {name:20s}: No files")
    
    print(f"\n📊 Total documents found: {total_docs}")
    
    if total_docs == 0:
        print(f"\n💡 GETTING STARTED WITH DOCUMENTS:")
        print(f"   1. Add PDF papers to: {config.literature_folder}")
        print(f"   2. Add your work to: {config.your_work_folder}")
        print(f"   3. Or run quick_start_rag.py to create sample documents")
        print(f"   4. Set up Zotero integration for automatic PDF management")
    else:
        print(f"✅ Ready to build knowledge base!")

def test_basic_functionality():
    """Test basic system functionality."""
    print(f"\n🧪 TESTING BASIC FUNCTIONALITY")
    print("-" * 40)
    
    try:
        from src.core import KnowledgeBase
        
        # Test knowledge base creation
        print(f"📚 Testing knowledge base creation...")
        kb = KnowledgeBase(
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=500,
            chunk_overlap=100
        )
        print(f"✅ Knowledge base created successfully")
        
        # Test embeddings
        print(f"🔍 Testing embeddings...")
        stats = kb.get_statistics()
        print(f"✅ Embeddings system working (model: {stats['embedding_model']})")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

def provide_next_steps(missing_required, missing_optional, config_ok, has_api_key):
    """Provide clear next steps based on current setup status."""
    print(f"\n🎯 NEXT STEPS")
    print("=" * 50)
    
    if missing_required:
        print(f"❌ CRITICAL: Install required packages first")
        print(f"   pip install " + " ".join([pkg for pkg, _ in missing_required]))
        return
    
    if not config_ok:
        print(f"❌ CRITICAL: Fix configuration issues first")
        return
    
    if not has_api_key:
        print(f"❌ CRITICAL: Set up Anthropic API key")
        print(f"   1. Get API key: https://console.anthropic.com/")
        print(f"   2. Create .env file in project root:")
        print(f"      ANTHROPIC_API_KEY=your-anthropic-api-key-here")
        return
    
    # System is ready!
    print(f"✅ SYSTEM READY! Choose your path:")
    print(f"\n🚀 Option 1: Quick Start (Recommended)")
    print(f"   python quick_start_rag.py")
    print(f"   → Interactive setup with sample documents")
    print(f"   → Immediate chat interface")
    
    print(f"\n🧪 Option 2: Run Tests First")
    print(f"   python test_basic_rag_system.py")
    print(f"   → Verify all components work")
    print(f"   → Detailed system testing")
    
    print(f"\n📖 Option 3: Add Your Documents")
    if config_ok:
        try:
            from config import PipelineConfig
            config = PipelineConfig()
            print(f"   1. Add PDFs to: {config.literature_folder}")
            print(f"   2. Run: python quick_start_rag.py")
        except:
            print(f"   1. Add PDFs to documents/literature/")
            print(f"   2. Run: python quick_start_rag.py")
    
    if missing_optional:
        print(f"\n⚠️  OPTIONAL ENHANCEMENTS:")
        for pkg, desc in missing_optional:
            if pkg == 'pyzotero':
                print(f"   Install Zotero integration: pip install pyzotero")
                print(f"   → Automatic PDF management from Zotero library")
            elif pkg == 'selenium':
                print(f"   Install advanced PDF downloads: pip install selenium")
                print(f"   → DOI-based PDF acquisition")

def create_sample_env_file():
    """Create a sample .env file if it doesn't exist."""
    env_file = Path(".env")
    
    if not env_file.exists():
        print(f"\n📝 Creating sample .env file...")
        
        sample_content = """# Physics Literature Synthesis Pipeline Configuration
# Copy this file and add your actual API keys

# REQUIRED: Anthropic API key for Claude AI
# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# OPTIONAL: Zotero integration for automatic PDF management
# Get from: https://www.zotero.org/settings/keys
ZOTERO_API_KEY=your-zotero-api-key-here
ZOTERO_LIBRARY_ID=your-zotero-library-id-here
ZOTERO_LIBRARY_TYPE=user

# OPTIONAL: Google Custom Search for enhanced arXiv search
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id-here

# OPTIONAL: System settings (defaults are usually fine)
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
EMBEDDING_MODEL=all-MiniLM-L6-v2
CLAUDE_MODEL=claude-3-5-sonnet-20241022
DEFAULT_TEMPERATURE=0.3
MAX_CONTEXT_CHUNKS=8
"""
        
        try:
            env_file.write_text(sample_content)
            print(f"✅ Created .env template")
            print(f"   → Edit .env file and add your API keys")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")

def main():
    """Run complete setup check."""
    print("🔧 PHYSICS LITERATURE RAG - SETUP CHECK")
    print("=" * 60)
    
    # Check dependencies
    missing_required, missing_optional = check_dependencies()
    
    # Check configuration
    config_ok, config = check_configuration()
    
    # Check API key specifically
    has_api_key = False
    if config:
        api_status = config.check_env_file()
        has_api_key = api_status['anthropic_api_key']
    
    # Check documents
    if config_ok:
        check_sample_documents(config)
    
    # Test basic functionality
    if not missing_required and config_ok:
        functionality_ok = test_basic_functionality()
    else:
        functionality_ok = False
    
    # Create sample .env if needed
    if not has_api_key:
        create_sample_env_file()
    
    # Provide next steps
    provide_next_steps(missing_required, missing_optional, config_ok, has_api_key)
    
    # Final status
    print(f"\n📊 SETUP STATUS SUMMARY")
    print("-" * 30)
    print(f"Dependencies: {'✅' if not missing_required else '❌'}")
    print(f"Configuration: {'✅' if config_ok else '❌'}")
    print(f"Anthropic API: {'✅' if has_api_key else '❌'}")
    print(f"Basic Functions: {'✅' if functionality_ok else '❌'}")
    print(f"Zotero (optional): {'✅' if not missing_optional else '⚠️'}")
    
    if not missing_required and config_ok and has_api_key and functionality_ok:
        print(f"\n🎉 READY TO GO! Run: python quick_start_rag.py")
    else:
        print(f"\n⚠️  Complete setup steps above before proceeding")

if __name__ == "__main__":
    main()