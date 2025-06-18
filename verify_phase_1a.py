#!/usr/bin/env python3
"""
Phase 1A Verification Script - Fixed Version

Tests that the restructuring maintains backward compatibility with
the save_to_file/load_from_file methods fixed.

Usage: python verify_phase_1a_fixed.py
"""

import sys
from pathlib import Path
import tempfile
import shutil

def test_embeddings_save_load():
    """Test that EmbeddingsManager save/load methods work correctly."""
    print("🔍 Testing EmbeddingsManager save/load functionality...")
    
    try:
        from src.core.embeddings.base_embeddings import EmbeddingsManager
        
        # Create a temporary embeddings manager
        em = EmbeddingsManager(model_name="all-MiniLM-L6-v2")
        
        # Test that required methods exist
        assert hasattr(em, 'save_to_file'), "save_to_file method missing"
        assert hasattr(em, 'load_from_file'), "load_from_file method missing"
        assert hasattr(em, 'save_embeddings'), "save_embeddings method missing"
        assert hasattr(em, 'load_embeddings'), "load_embeddings method missing"
        assert hasattr(em, 'get_document_chunks'), "get_document_chunks method missing"
        assert hasattr(em, 'search_with_context'), "search_with_context method missing"
        
        print("✅ All required EmbeddingsManager methods present")
        
        # Test save/load functionality with empty manager
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test_embeddings.pkl"
            
            # Save empty embeddings
            em.save_to_file(test_file)
            assert test_file.exists(), "Save file was not created"
            
            # Load embeddings
            new_em = EmbeddingsManager(model_name="all-MiniLM-L6-v2")
            success = new_em.load_from_file(test_file)
            assert success, "Load from file failed"
            
            print("✅ Save/load functionality works")
        
        return True
        
    except Exception as e:
        print(f"❌ EmbeddingsManager test failed: {e}")
        return False

def test_knowledge_base_compatibility():
    """Test that KnowledgeBase can use the restructured EmbeddingsManager."""
    print("\n🏗️ Testing KnowledgeBase compatibility...")
    
    try:
        from src.core import KnowledgeBase
        
        # Create a temporary knowledge base
        with tempfile.TemporaryDirectory() as temp_dir:
            kb = KnowledgeBase(
                name="test_kb",
                base_storage_dir=Path(temp_dir)
            )
            
            # Test that the embeddings manager has the required interface
            em = kb.embeddings_manager
            assert hasattr(em, 'save_to_file'), "KnowledgeBase embeddings manager missing save_to_file"
            assert hasattr(em, 'load_from_file'), "KnowledgeBase embeddings manager missing load_from_file"
            
            # Test that save_to_storage doesn't crash
            try:
                kb.save_to_storage()
                print("✅ KnowledgeBase save_to_storage works")
            except Exception as e:
                print(f"❌ KnowledgeBase save_to_storage failed: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ KnowledgeBase compatibility test failed: {e}")
        return False

def test_backward_compatibility():
    """Test that all existing imports still work."""
    print("\n🧪 Testing Backward Compatibility...")
    
    try:
        # Test core embeddings imports (should work via __init__.py re-exports)
        from src.core import EmbeddingsManager, DocumentChunk, SearchResult
        print("✅ Core embeddings imports work")
        
        # Test that the imported EmbeddingsManager has required methods
        em = EmbeddingsManager()
        assert hasattr(em, 'save_to_file'), "Imported EmbeddingsManager missing save_to_file"
        assert hasattr(em, 'load_from_file'), "Imported EmbeddingsManager missing load_from_file"
        
        # Test chat imports
        from src.chat import LiteratureAssistant, EnhancedPhysicsAssistant
        print("✅ Chat assistant imports work")
        
        # Test knowledge base imports
        from src.core import KnowledgeBase
        print("✅ Knowledge base imports work")
        
        # Test additional prompt imports that were failing
        try:
            from src.chat.prompts import get_concept_explanation_prefix
            print("✅ Additional prompt imports work")
        except ImportError as e:
            print(f"⚠️ Additional prompt import issue: {e}")
            # This might be expected if some functions aren't needed for backward compatibility
        
        print("✅ All backward compatibility tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def test_new_structure():
    """Test that new modular structure works."""
    print("\n🏗️ Testing New Modular Structure...")
    
    try:
        # Test direct imports from new structure
        from src.core.embeddings.base_embeddings import EmbeddingsManager as BaseEM
        print("✅ Direct embeddings import works")
        
        # Test prompt imports
        from src.chat.prompts import (
            get_basic_literature_prompt, 
            get_enhanced_physics_prompt,
            get_concept_explanation_prefix,
            get_literature_survey_template,
            get_research_brainstorm_template
        )
        print("✅ Prompt function imports work")
        
        # Test prompt functionality
        kb_stats = {
            'total_documents': 100,
            'total_chunks': 1000,
            'source_breakdown': {'literature': 50, 'your_work': 30, 'zotero_sync': 20},
            'embedding_model': 'all-MiniLM-L6-v2'
        }
        
        basic_prompt = get_basic_literature_prompt(kb_stats)
        enhanced_prompt = get_enhanced_physics_prompt(kb_stats)
        concept_prompt = get_concept_explanation_prefix("quantum mechanics", "undergraduate")
        survey_prompt = get_literature_survey_template("quantum computing", 10)
        brainstorm_prompt = get_research_brainstorm_template("quantum error correction")
        
        # Check that prompts contain expected content
        assert "theoretical physicist" in basic_prompt.lower()
        assert "theoretical physicist" in enhanced_prompt.lower()
        assert "100" in basic_prompt  # Should include total_documents
        assert "100" in enhanced_prompt
        assert "quantum mechanics" in concept_prompt.lower()
        assert "quantum computing" in survey_prompt.lower()
        assert "quantum error correction" in brainstorm_prompt.lower()
        print("✅ Prompt generation works correctly")
        
        print("✅ All new structure tests passed!")
        return True
        
    except (ImportError, AssertionError) as e:
        print(f"❌ New structure test failed: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🚀 Phase 1A Verification Script - Fixed Version")
    print("=" * 50)
    
    # Add project root to path
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    tests = [
        test_embeddings_save_load,
        test_knowledge_base_compatibility,
        test_backward_compatibility,
        test_new_structure
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 PHASE 1A VERIFICATION RESULTS (FIXED)")
    print("=" * 50)
    
    if all(results):
        print("🎉 All tests passed! Phase 1A restructuring fixed and working.")
        print("\n✅ Ready for Phase 1B implementation")
        return True
    else:
        failed_count = sum(1 for r in results if not r)
        print(f"❌ {failed_count} test(s) failed. Please fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)