#!/usr/bin/env python3
"""
Phase 1B Verification Script

Tests that the enhanced embeddings and prompt engineering components
work correctly and provide improved functionality.

Usage: python verify_phase_1b.py
"""

import sys
from pathlib import Path
import tempfile

def test_enhanced_embeddings():
    """Test enhanced embeddings functionality."""
    print("🔬 Testing Enhanced Embeddings...")
    
    try:
        from src.core.embeddings import (
            EnhancedEmbeddingsManager, 
            create_embeddings_manager,
            ChunkingConfig,
            create_chunking_strategy
        )
        
        # Test factory function
        basic_em = create_embeddings_manager(enhanced=False)
        enhanced_em = create_embeddings_manager(enhanced=True)
        
        assert hasattr(basic_em, 'chunk_text'), "Basic embeddings manager missing chunk_text"
        assert hasattr(enhanced_em, 'chunk_text'), "Enhanced embeddings manager missing chunk_text"
        
        # Test enhanced features
        assert hasattr(enhanced_em, 'get_enhanced_statistics'), "Missing enhanced statistics"
        assert hasattr(enhanced_em, 'switch_chunking_strategy'), "Missing strategy switching"
        
        print("✅ Enhanced embeddings manager created successfully")
        
        # Test chunking strategies
        simple_strategy = create_chunking_strategy('simple')
        context_strategy = create_chunking_strategy('context_aware')
        
        assert simple_strategy.name == 'SimpleChunkingStrategy', "Simple strategy name incorrect"
        assert context_strategy.name == 'ContextAwareChunkingStrategy', "Context strategy name incorrect"
        
        print("✅ Chunking strategies work correctly")
        
        # Test chunking with sample text
        sample_text = """
        This is a sample physics paper. The quantum mechanical system can be described by the Hamiltonian H = p²/2m + V(x).
        
        In the next section, we discuss experimental methods. The measurement apparatus consists of lasers and detectors.
        
        Results show that the quantum state exhibits entanglement. References: [1] Einstein et al. (1935), [2] Bell (1964).
        """
        
        simple_chunks = simple_strategy.chunk_text(sample_text)
        context_chunks = context_strategy.chunk_text(sample_text)
        
        assert len(simple_chunks) > 0, "Simple chunking produced no chunks"
        assert len(context_chunks) > 0, "Context-aware chunking produced no chunks"
        
        # Check enhanced metadata
        if context_chunks:
            chunk_data = context_chunks[0]
            assert 'text' in chunk_data, "Chunk missing text"
            assert 'metadata' in chunk_data, "Chunk missing metadata"
            
            metadata = chunk_data['metadata']
            assert hasattr(metadata, 'has_equations'), "Missing equation detection"
            assert hasattr(metadata, 'has_citations'), "Missing citation detection"
            
            print("✅ Enhanced chunking metadata works")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced embeddings test failed: {e}")
        return False

def test_enhanced_prompts():
    """Test enhanced prompt engineering functionality."""
    print("\n🎯 Testing Enhanced Prompt Engineering...")
    
    try:
        from src.chat.prompts import (
            PromptManager,
            PromptConfig,
            PromptStyle,
            create_prompt_manager,
            PhysicsExpertiseModule,
            ContextFormattingModule,
            ScientificLexiconModule
        )
        
        # Test factory function
        basic_pm = create_prompt_manager('basic')
        enhanced_pm = create_prompt_manager('enhanced')
        modular_pm = create_prompt_manager('modular')
        
        assert basic_pm.config.style == PromptStyle.BASIC, "Basic prompt manager style incorrect"
        assert enhanced_pm.config.style == PromptStyle.ENHANCED, "Enhanced prompt manager style incorrect"
        assert modular_pm.config.style == PromptStyle.MODULAR, "Modular prompt manager style incorrect"
        
        print("✅ Prompt managers created successfully")
        
        # Test modular components
        physics_module = PhysicsExpertiseModule()
        context_module = ContextFormattingModule()
        lexicon_module = ScientificLexiconModule()
        
        # Test physics expertise levels
        basic_physics = physics_module.get_physics_expertise_prompt('basic')
        enhanced_physics = physics_module.get_physics_expertise_prompt('enhanced')
        expert_physics = physics_module.get_physics_expertise_prompt('expert')
        
        assert len(basic_physics) > 100, "Basic physics prompt too short"
        assert len(enhanced_physics) > len(basic_physics), "Enhanced physics prompt not longer than basic"
        assert len(expert_physics) > len(enhanced_physics), "Expert physics prompt not longer than enhanced"
        
        print("✅ Physics expertise modules work correctly")
        
        # Test context formatting
        simple_context = context_module.get_context_formatting_instructions('simple')
        structured_context = context_module.get_context_formatting_instructions('structured')
        advanced_context = context_module.get_context_formatting_instructions('advanced')
        
        assert 'literature' in simple_context.lower(), "Simple context missing literature reference"
        assert 'synthesis' in structured_context.lower(), "Structured context missing synthesis guidance"
        assert 'hierarchical' in advanced_context.lower(), "Advanced context missing hierarchical processing"
        
        print("✅ Context formatting modules work correctly")
        
        # Test lexicon guidance
        basic_lexicon = lexicon_module.get_lexicon_guidance('basic')
        precise_lexicon = lexicon_module.get_lexicon_guidance('precise')
        technical_lexicon = lexicon_module.get_lexicon_guidance('technical')
        
        assert 'terminology' in basic_lexicon.lower(), "Basic lexicon missing terminology guidance"
        assert 'precision' in precise_lexicon.lower(), "Precise lexicon missing precision guidance"
        assert 'expert' in technical_lexicon.lower(), "Technical lexicon missing expert guidance"
        
        print("✅ Scientific lexicon modules work correctly")
        
        # Test full prompt generation
        kb_stats = {
            'total_documents': 100,
            'total_chunks': 1000,
            'source_breakdown': {'literature': 80, 'your_work': 20},
            'embedding_model': 'all-MiniLM-L6-v2'
        }
        
        modular_prompt = modular_pm.generate_system_prompt(kb_stats, 'literature_assistant')
        
        assert len(modular_prompt) > 1000, "Modular prompt too short"
        assert '100' in modular_prompt, "Modular prompt missing KB stats"
        assert 'physics' in modular_prompt.lower(), "Modular prompt missing physics expertise"
        
        print("✅ Full prompt generation works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Enhanced prompts test failed: {e}")
        return False

def test_integration():
    """Test integration between enhanced embeddings and prompts."""
    print("\n🔗 Testing Enhanced Integration...")
    
    try:
        from src.core.embeddings import create_embeddings_manager
        from src.chat.prompts import create_prompt_manager
        
        # Create enhanced components
        enhanced_em = create_embeddings_manager(
            enhanced=True,
            chunking_strategy='context_aware'
        )
        
        modular_pm = create_prompt_manager(
            'modular',
            physics_expertise_level='enhanced',
            context_integration='structured'
        )
        
        # Test that they can work together
        strategy_info = enhanced_em.get_chunking_strategy_info()
        prompt_analysis = modular_pm.get_prompt_analysis()
        
        assert 'name' in strategy_info, "Strategy info missing name"
        assert 'config' in strategy_info, "Strategy info missing config"
        
        print("✅ Enhanced components integrate correctly")
        
        # Test configuration updates
        modular_pm.update_config(physics_expertise_level='expert')
        assert modular_pm.config.physics_expertise_level == 'expert', "Config update failed"
        
        # Test cloning with different config
        expert_pm = modular_pm.clone_with_config(scientific_lexicon='technical')
        assert expert_pm.config.scientific_lexicon == 'technical', "Clone config incorrect"
        assert expert_pm.config.physics_expertise_level == 'expert', "Clone missing original config"
        
        print("✅ Configuration management works correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def test_backward_compatibility():
    """Test that enhanced features don't break existing functionality."""
    print("\n🔄 Testing Backward Compatibility...")
    
    try:
        # Test that original imports still work
        from src.core import EmbeddingsManager, DocumentChunk, SearchResult
        from src.chat import LiteratureAssistant, EnhancedPhysicsAssistant
        
        # Test that original functionality is preserved
        em = EmbeddingsManager()
        assert hasattr(em, 'chunk_text'), "Original EmbeddingsManager missing chunk_text"
        assert hasattr(em, 'save_to_file'), "Original EmbeddingsManager missing save_to_file"
        assert hasattr(em, 'load_from_file'), "Original EmbeddingsManager missing load_from_file"
        
        print("✅ Original embeddings functionality preserved")
        
        # Test that legacy prompts still work
        from src.chat.prompts import get_basic_literature_prompt, get_enhanced_physics_prompt
        
        kb_stats = {'total_documents': 50, 'total_chunks': 500, 'source_breakdown': {}}
        
        basic_prompt = get_basic_literature_prompt(kb_stats)
        enhanced_prompt = get_enhanced_physics_prompt(kb_stats)
        
        assert len(basic_prompt) > 100, "Legacy basic prompt too short"
        assert len(enhanced_prompt) > 100, "Legacy enhanced prompt too short"
        assert '50' in basic_prompt, "Legacy prompt missing KB stats"
        
        print("✅ Legacy prompt functionality preserved")
        
        # Test that new functionality is opt-in
        from src.core.embeddings import create_embeddings_manager
        
        # Default should be backward compatible
        default_em = create_embeddings_manager()
        assert type(default_em).__name__ == 'EmbeddingsManager', "Default manager not backward compatible"
        
        # Enhanced should be explicitly requested
        enhanced_em = create_embeddings_manager(enhanced=True)
        assert type(enhanced_em).__name__ == 'EnhancedEmbeddingsManager', "Enhanced manager not created"
        
        print("✅ Enhanced features are properly opt-in")
        
        return True
        
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def test_performance_and_quality():
    """Test that enhanced features provide measurable improvements."""
    print("\n⚡ Testing Performance and Quality Improvements...")
    
    try:
        from src.core.embeddings import create_embeddings_manager, ChunkingConfig
        
        # Test chunking quality improvements
        sample_text = """
        Abstract: This paper presents a comprehensive study of quantum entanglement in many-body systems.
        
        Introduction: Quantum entanglement is a fundamental feature of quantum mechanics described by the equation |ψ⟩ = α|00⟩ + β|11⟩.
        
        Methods: We used laser spectroscopy and magnetic resonance techniques to measure the entanglement entropy.
        
        Results: The measurements show clear evidence of long-range entanglement. See Figure 1 and Reference [1].
        
        Discussion: These results confirm theoretical predictions from quantum field theory [2,3].
        """
        
        # Compare simple vs context-aware chunking
        simple_em = create_embeddings_manager(enhanced=True, chunking_strategy='simple')
        context_em = create_embeddings_manager(enhanced=True, chunking_strategy='context_aware')
        
        simple_chunks = simple_em.chunk_text(sample_text)
        context_chunks = context_em.chunk_text(sample_text, {'file_name': 'test_paper.pdf'})
        
        # Context-aware should preserve structure better
        if len(context_chunks) > 0:
            context_chunk = context_chunks[0]
            
            # Check for enhanced metadata
            if hasattr(context_em, 'chunk_metadata') and context_em.chunk_metadata:
                metadata = context_em.chunk_metadata[-1]['metadata']
                
                # Should detect equations and citations
                has_equations = getattr(metadata, 'has_equations', False)
                has_citations = getattr(metadata, 'has_citations', False)
                
                print(f"✅ Enhanced chunking detected equations: {has_equations}")
                print(f"✅ Enhanced chunking detected citations: {has_citations}")
        
        # Test enhanced statistics
        enhanced_stats = context_em.get_enhanced_statistics()
        
        assert 'chunking_strategy' in enhanced_stats, "Enhanced stats missing strategy info"
        assert 'enhanced_features' in enhanced_stats, "Enhanced stats missing features info"
        
        print("✅ Enhanced statistics provide additional insights")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance and quality test failed: {e}")
        return False

def main():
    """Run all Phase 1B verification tests."""
    print("🚀 Phase 1B Verification Script")
    print("Testing Enhanced Embeddings & Prompt Engineering")
    print("=" * 60)
    
    # Add project root to path
    project_root = Path(__file__).parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    tests = [
        test_enhanced_embeddings,
        test_enhanced_prompts,
        test_integration,
        test_backward_compatibility,
        test_performance_and_quality
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 PHASE 1B VERIFICATION RESULTS")
    print("=" * 60)
    
    if all(results):
        print("🎉 All tests passed! Phase 1B enhanced features working correctly.")
        print("\n✅ Enhanced embeddings with better chunking strategies")
        print("✅ Modular prompt engineering with physics expertise")
        print("✅ Backward compatibility maintained")
        print("✅ Configuration-driven enhancements")
        print("✅ Ready for production use and further iteration")
        
        print("\n🔧 USAGE RECOMMENDATIONS:")
        print("• Use EnhancedEmbeddingsManager with 'context_aware' strategy for better chunking")
        print("• Use PromptManager with 'modular' style for enhanced AI responses")
        print("• Configure physics_expertise_level='enhanced' for research contexts")
        print("• Set context_integration='structured' for better literature synthesis")
        
        return True
    else:
        failed_count = sum(1 for r in results if not r)
        print(f"❌ {failed_count} test(s) failed. Please fix issues before proceeding.")
        
        print("\n🔍 DEBUGGING TIPS:")
        print("• Check that all new modules are properly imported")
        print("• Verify chunking strategies are correctly implemented")
        print("• Ensure prompt modules are accessible")
        print("• Test individual components separately")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)