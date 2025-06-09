#!/usr/bin/env python3
"""
Test script for basic RAG system functionality.
This will help us verify and improve the literature-aware assistant.
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config import PipelineConfig
from src.core import KnowledgeBase
from src.chat import LiteratureAssistant

def test_1_configuration():
    """Test 1: Verify configuration is working."""
    print("🧪 TEST 1: Configuration System")
    print("-" * 50)
    
    try:
        config = PipelineConfig()
        print(f"✅ Configuration loaded successfully")
        print(f"   Project root: {config.project_root}")
        print(f"   Literature folder: {config.literature_folder}")
        print(f"   Zotero sync folder: {config.zotero_sync_folder}")
        
        # Check API keys
        api_status = config.check_env_file()
        print(f"   Anthropic API: {'✅' if api_status['anthropic_api_key'] else '❌'}")
        print(f"   Zotero API: {'✅' if api_status['zotero_configured'] else '❌'}")
        
        return True, config
    except Exception as e:
        print(f"❌ Configuration failed: {e}")
        return False, None

def test_2_knowledge_base_empty():
    """Test 2: Create empty knowledge base."""
    print("\n🧪 TEST 2: Knowledge Base Creation")
    print("-" * 50)
    
    try:
        # Test with basic parameters
        kb = KnowledgeBase(
            embedding_model="all-MiniLM-L6-v2",
            chunk_size=500,  # Smaller for testing
            chunk_overlap=100
        )
        
        stats = kb.get_statistics()
        print(f"✅ Empty knowledge base created")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Total chunks: {stats['total_chunks']}")
        print(f"   Embedding model: {stats['embedding_model']}")
        
        return True, kb
    except Exception as e:
        print(f"❌ Knowledge base creation failed: {e}")
        return False, None

def test_3_add_sample_document(kb, config):
    """Test 3: Add a sample document to test processing."""
    print("\n🧪 TEST 3: Document Processing")
    print("-" * 50)
    
    # Create a sample physics document
    sample_doc_path = config.literature_folder / "sample_physics_paper.txt"
    sample_content = """
    Quantum Entanglement in Two-Photon Systems
    
    Abstract: This paper investigates quantum entanglement phenomena in two-photon systems.
    We demonstrate that entangled photon pairs exhibit non-local correlations that violate
    Bell's inequalities. The experimental setup consists of a parametric down-conversion
    source producing entangled photon pairs at 810nm wavelength.
    
    Introduction: Quantum entanglement is a fundamental phenomenon in quantum mechanics
    where particles become correlated in such a way that the quantum state of each particle
    cannot be described independently. This property forms the basis for quantum information
    processing and quantum cryptography applications.
    
    Methods: We use a beta-barium borate (BBO) crystal for spontaneous parametric 
    down-conversion. The pump laser operates at 405nm with 100mW power. Photon pairs
    are detected using avalanche photodiodes with coincidence timing resolution of 1ns.
    
    Results: We observed violation of Bell's inequality with S = 2.7 ± 0.1, significantly
    exceeding the classical limit of 2.0. The entanglement fidelity was measured to be
    95.2% ± 1.5%, demonstrating high-quality entangled states.
    
    Conclusion: Our results confirm the non-local nature of quantum entanglement and
    demonstrate the feasibility of high-fidelity entangled photon generation for
    quantum information applications.
    """
    
    try:
        # Ensure directory exists
        config.literature_folder.mkdir(parents=True, exist_ok=True)
        
        # Write sample document
        sample_doc_path.write_text(sample_content, encoding='utf-8')
        print(f"✅ Created sample document: {sample_doc_path.name}")
        
        # Add to knowledge base
        success = kb.add_document(sample_doc_path, source_type="test_literature")
        
        if success:
            stats = kb.get_statistics()
            print(f"✅ Document processed successfully")
            print(f"   Total documents: {stats['total_documents']}")
            print(f"   Total chunks: {stats['total_chunks']}")
            print(f"   Average chunk length: {stats.get('avg_chunk_length', 0):.1f} words")
            return True
        else:
            print(f"❌ Failed to process document")
            return False
            
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        return False

def test_4_basic_search(kb):
    """Test 4: Test semantic search functionality."""
    print("\n🧪 TEST 4: Semantic Search")
    print("-" * 50)
    
    try:
        test_queries = [
            "quantum entanglement",
            "Bell's inequality violation", 
            "photon detection methods",
            "experimental setup for quantum optics"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: '{query}'")
            results = kb.search(query, top_k=2)
            
            if results:
                print(f"   Found {len(results)} results")
                for i, result in enumerate(results, 1):
                    print(f"   {i}. Similarity: {result.similarity_score:.3f}")
                    print(f"      Text: {result.chunk.text[:100]}...")
            else:
                print(f"   No results found")
        
        return True
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False

def test_5_literature_assistant(kb, config):
    """Test 5: Test the literature assistant."""
    print("\n🧪 TEST 5: Literature Assistant")
    print("-" * 50)
    
    try:
        if not config.anthropic_api_key:
            print("❌ Anthropic API key required for assistant testing")
            print("   Set ANTHROPIC_API_KEY in your .env file to test the assistant")
            return False
        
        # Create assistant
        assistant = LiteratureAssistant(
            knowledge_base=kb,
            anthropic_api_key=config.anthropic_api_key,
            chat_config=config.get_chat_config()
        )
        
        print(f"✅ Literature assistant created")
        
        # Test questions
        test_questions = [
            "What is quantum entanglement?",
            "How do you measure Bell's inequality violations?",
            "What experimental setup is used for entangled photons?"
        ]
        
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            try:
                response = assistant.ask(
                    question, 
                    temperature=0.3,
                    max_context_chunks=3
                )
                
                print(f"✅ Response generated ({response.processing_time:.2f}s)")
                print(f"   Sources used: {len(response.sources_used)}")
                print(f"   Context chunks: {response.context_chunks_used}")
                print(f"   Response preview: {response.content[:150]}...")
                
                if response.sources_used:
                    print(f"   Source files: {', '.join(response.sources_used)}")
                
            except Exception as e:
                print(f"❌ Question failed: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Assistant creation failed: {e}")
        return False

def test_6_conversation_memory(assistant):
    """Test 6: Test conversation memory and context."""
    print("\n🧪 TEST 6: Conversation Memory")
    print("-" * 50)
    
    try:
        # First question
        print("🗣️  First question...")
        response1 = assistant.ask("What is the wavelength mentioned in the quantum entanglement experiment?")
        print(f"✅ Response 1: {response1.content[:100]}...")
        
        # Follow-up question (should use conversation context)
        print("\n🗣️  Follow-up question...")
        response2 = assistant.ask("What was the power of the laser used?")
        print(f"✅ Response 2: {response2.content[:100]}...")
        
        # Check conversation summary
        summary = assistant.get_conversation_summary()
        print(f"\n📊 Conversation summary: {summary}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        return False

def main():
    """Run all tests to verify basic RAG functionality."""
    print("🚀 BASIC RAG SYSTEM TEST SUITE")
    print("=" * 60)
    
    # Track test results
    results = {}
    
    # Test 1: Configuration
    success, config = test_1_configuration()
    results['configuration'] = success
    if not success:
        return
    
    # Test 2: Knowledge Base
    success, kb = test_2_knowledge_base_empty()
    results['knowledge_base'] = success
    if not success:
        return
    
    # Test 3: Document Processing
    success = test_3_add_sample_document(kb, config)
    results['document_processing'] = success
    if not success:
        return
    
    # Test 4: Search
    success = test_4_basic_search(kb)
    results['search'] = success
    
    # Test 5: Assistant (requires API key)
    assistant = None
    if config.anthropic_api_key:
        success = test_5_literature_assistant(kb, config)
        results['assistant'] = success
        
        if success:
            # Get assistant for memory test
            assistant = LiteratureAssistant(kb, config.anthropic_api_key, config.get_chat_config())
            
            # Test 6: Conversation Memory
            success = test_6_conversation_memory(assistant)
            results['conversation'] = success
    else:
        print("\n⚠️  Skipping assistant tests (no Anthropic API key)")
        results['assistant'] = 'skipped'
        results['conversation'] = 'skipped'
    
    # Print final summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result == True:
            status = "✅ PASS"
        elif result == False:
            status = "❌ FAIL"
        else:
            status = "⏭️  SKIP"
        print(f"{test_name:20s}: {status}")
    
    # Success indicators
    passed = sum(1 for r in results.values() if r == True)
    total = len([r for r in results.values() if r != 'skipped'])
    
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("\n🎉 All tests passed! Your basic RAG system is working.")
        print("\n💡 Next steps:")
        print("   1. Add real papers to your literature folder")
        print("   2. Set up Zotero integration for automatic PDF downloads")
        print("   3. Try the system with actual physics questions")
    else:
        print(f"\n⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()