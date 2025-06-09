#!/usr/bin/env python3
"""
Enhanced Quick Start Script for Physics Literature RAG System

This script provides an easy way to get started with the literature-aware assistant
using the new named knowledge base system with organized storage.

Location: scripts/quick_start_rag.py
"""

import sys
from pathlib import Path
import time

# Set up imports - FIXED for scripts/ directory
project_root = Path(__file__).parent.parent  # Go up from scripts/ to project root
sys.path.insert(0, str(project_root))

from config.settings import PipelineConfig
from src.core import create_knowledge_base, load_knowledge_base, list_knowledge_bases
from src.chat import LiteratureAssistant
from src.downloaders import create_literature_syncer, print_zotero_status

class EnhancedQuickStartRAG:
    """Enhanced quick start helper for the RAG system with named knowledge bases."""
    
    def __init__(self):
        """Initialize the enhanced quick start system."""
        self.config = None
        self.knowledge_base = None
        self.assistant = None
        self.kb_name = None
        
    def setup(self):
        """Set up the RAG system with guided configuration."""
        print("🚀 PHYSICS LITERATURE RAG - ENHANCED QUICK START")
        print("=" * 55)
        
        # Load configuration
        try:
            self.config = PipelineConfig()
            print(f"✅ Configuration loaded")
        except Exception as e:
            print(f"❌ Configuration failed: {e}")
            return False
        
        # Check for legacy migration
        self._check_legacy_migration()
        
        # Check API keys
        api_status = self.config.check_env_file()
        
        print(f"\n📋 API Status:")
        print(f"   Anthropic (required): {'✅' if api_status['anthropic_api_key'] else '❌'}")
        print(f"   Zotero (optional): {'✅' if api_status['zotero_configured'] else '❌'}")
        
        if not api_status['anthropic_api_key']:
            print(f"\n⚠️  ANTHROPIC_API_KEY required for AI assistant")
            print(f"   Add to .env file: ANTHROPIC_API_KEY=your-key-here")
            return False
        
        return True
    
    def _check_legacy_migration(self):
        """Check for and offer to migrate legacy cache file."""
        legacy_cache = self.config.get_legacy_cache_file()
        
        if legacy_cache.exists():
            print(f"\n🔄 Legacy cache file detected: {legacy_cache.name}")
            response = input("   Migrate to new knowledge base system? (y/n): ").strip().lower()
            
            if response in ['y', 'yes']:
                kb_name = input(f"   Knowledge base name [default: {self.config.default_kb_name}]: ").strip()
                if not kb_name:
                    kb_name = self.config.default_kb_name
                
                print(f"   Migrating to knowledge base '{kb_name}'...")
                if self.config.migrate_legacy_cache(kb_name):
                    print(f"   ✅ Migration successful!")
                    self.kb_name = kb_name
                else:
                    print(f"   ❌ Migration failed")
            else:
                print(f"   Keeping legacy cache file")
    
    def select_knowledge_base(self):
        """Select or create a knowledge base."""
        print(f"\n📚 Knowledge Base Selection")
        print("-" * 40)
        
        # List available knowledge bases
        available_kbs = list_knowledge_bases(self.config.knowledge_bases_folder)
        
        if available_kbs:
            print(f"📋 Available knowledge bases:")
            for i, kb_info in enumerate(available_kbs, 1):
                kb = kb_info
                last_updated = time.strftime('%Y-%m-%d %H:%M', time.localtime(kb['last_updated'])) if kb['last_updated'] else 'Unknown'
                print(f"   {i}. {kb['name']} (Updated: {last_updated}, Size: {kb['size_mb']:.1f} MB)")
        
        print(f"\n💡 Options:")
        print(f"   1. Create new knowledge base")
        print(f"   2. Load existing knowledge base")
        print(f"   3. Use default: '{self.config.default_kb_name}'")
        
        while True:
            try:
                choice = input(f"\nChoice [3]: ").strip()
                
                if not choice or choice == "3":
                    # Use default
                    self.kb_name = self.config.default_kb_name
                    break
                elif choice == "1":
                    # Create new
                    kb_name = input(f"Knowledge base name: ").strip()
                    if not kb_name:
                        print("❌ Name cannot be empty")
                        continue
                    
                    if any(kb['name'] == kb_name for kb in available_kbs):
                        print(f"❌ Knowledge base '{kb_name}' already exists")
                        continue
                    
                    self.kb_name = kb_name
                    break
                elif choice == "2":
                    # Load existing
                    if not available_kbs:
                        print("❌ No existing knowledge bases found")
                        continue
                    
                    kb_choice = input(f"Enter knowledge base name or number: ").strip()
                    
                    # Try by number first
                    try:
                        kb_index = int(kb_choice) - 1
                        if 0 <= kb_index < len(available_kbs):
                            self.kb_name = available_kbs[kb_index]['name']
                            break
                    except ValueError:
                        pass
                    
                    # Try by name
                    if any(kb['name'] == kb_choice for kb in available_kbs):
                        self.kb_name = kb_choice
                        break
                    
                    print(f"❌ Invalid selection: {kb_choice}")
                else:
                    print(f"❌ Invalid choice: {choice}")
                    
            except KeyboardInterrupt:
                print(f"\n👋 Goodbye!")
                return False
        
        print(f"✅ Selected knowledge base: '{self.kb_name}'")
        return True
    
    def build_or_load_knowledge_base(self):
        """Build or load the selected knowledge base."""
        print(f"\n📚 Knowledge Base: '{self.kb_name}'")
        print("-" * 50)
        
        # Try to load existing knowledge base
        self.knowledge_base = load_knowledge_base(self.kb_name, self.config.knowledge_bases_folder)
        
        if self.knowledge_base:
            stats = self.knowledge_base.get_statistics()
            print(f"✅ Loaded existing knowledge base")
            print(f"   Documents: {stats['total_documents']}")
            print(f"   Chunks: {stats['total_chunks']}")
            if stats.get('last_updated'):
                print(f"   Last updated: {time.strftime('%Y-%m-%d %H:%M', time.localtime(stats['last_updated']))}")
            
            # Ask if user wants to rebuild
            if stats['total_documents'] > 0:
                rebuild = input(f"\n🔄 Rebuild knowledge base? (y/n) [n]: ").strip().lower()
                if rebuild in ['y', 'yes']:
                    return self._build_knowledge_base(force_rebuild=True)
                else:
                    return True
            else:
                print(f"🔍 Knowledge base is empty, scanning for documents...")
                return self._build_knowledge_base()
        else:
            # Create new knowledge base
            print(f"🆕 Creating new knowledge base...")
            kb_config = self.config.get_knowledge_base_config(self.kb_name)
            
            self.knowledge_base = create_knowledge_base(
                name=self.kb_name,
                base_storage_dir=self.config.knowledge_bases_folder,
                embedding_model=kb_config.embedding_model,
                chunk_size=kb_config.chunk_size,
                chunk_overlap=kb_config.chunk_overlap
            )
            
            return self._build_knowledge_base()
    
    def _build_knowledge_base(self, force_rebuild: bool = False):
        """Build the knowledge base from documents."""
        print(f"🔍 Scanning for documents...")
        
        # Get available folders
        folders = self.config.get_document_folders()
        docs_found = 0
        
        for folder_name, folder_path in folders.items():
            if folder_path.exists():
                files = list(folder_path.glob("*.pdf")) + list(folder_path.glob("*.txt")) + list(folder_path.glob("*.tex"))
                if files:
                    print(f"   {folder_name}: {len(files)} files")
                    docs_found += len(files)
        
        if docs_found == 0:
            print(f"⚠️  No documents found. Creating sample document...")
            self._create_sample_document()
            docs_found = 1
        
        # Build knowledge base
        try:
            print(f"🔨 Building knowledge base from {docs_found} documents...")
            
            stats = self.knowledge_base.build_from_directories(
                literature_folder=self.config.literature_folder,
                your_work_folder=self.config.your_work_folder,
                current_drafts_folder=self.config.current_drafts_folder,
                manual_references_folder=self.config.manual_references_folder,
                zotero_folder=self.config.zotero_sync_folder,
                force_rebuild=force_rebuild
            )
            
            print(f"✅ Knowledge base built:")
            print(f"   Documents: {stats['total_documents']}")
            print(f"   Chunks: {stats['total_chunks']}")
            print(f"   Success rate: {stats['success_rate']:.1f}%")
            print(f"   Storage: {stats['storage_location']}")
            
            return True
            
        except Exception as e:
            print(f"❌ Knowledge base build failed: {e}")
            return False
    
    def _create_sample_document(self):
        """Create a sample physics document for testing."""
        sample_content = """
        Quantum Computing with Superconducting Qubits

        Abstract: We demonstrate quantum computation using superconducting transmon qubits
        in a dilution refrigerator operating at 10 mK. The system achieves single-qubit
        gate fidelities of 99.8% and two-qubit gate fidelities of 99.2% using cross-resonance
        gates. We implement quantum error correction protocols and demonstrate logical
        qubit lifetimes exceeding physical qubit coherence times.

        1. Introduction
        Superconducting quantum processors have emerged as a leading platform for 
        quantum computation. The transmon qubit design provides strong anharmonicity
        while maintaining long coherence times through charge noise insensitivity.

        2. Experimental Setup
        Our processor consists of 53 superconducting transmon qubits arranged in a
        two-dimensional grid. Each qubit has a frequency around 5 GHz and anharmonicity
        of -300 MHz. The chip is fabricated using electron beam lithography on silicon.

        3. Quantum Gates
        Single-qubit gates are implemented using microwave pulses with Gaussian envelopes.
        Two-qubit gates use the cross-resonance interaction between neighboring qubits.
        Gate times are 50 ns for single-qubit gates and 300 ns for two-qubit gates.

        4. Error Correction
        We implement surface code error correction with distance-3 logical qubits.
        Syndrome detection is performed every 1 μs using ancilla qubits. Real-time
        decoding enables active error correction during computation.

        5. Results
        Quantum volume benchmarks demonstrate computational capabilities exceeding
        classical simulation limits. We successfully execute quantum algorithms
        including Shor's algorithm for 15-bit factorization and quantum chemistry
        simulations for small molecules.

        6. Conclusion
        Our results demonstrate the viability of superconducting quantum processors
        for practical quantum computation. Future work will focus on scaling to
        larger qubit arrays and improved error correction codes.
        """
        
        sample_path = self.config.literature_folder / "sample_quantum_computing.txt"
        self.config.literature_folder.mkdir(parents=True, exist_ok=True)
        sample_path.write_text(sample_content)
        print(f"   Created: {sample_path.name}")
    
    def create_assistant(self):
        """Create the literature assistant."""
        print(f"\n🤖 Creating Literature Assistant...")
        
        try:
            self.assistant = LiteratureAssistant(
                knowledge_base=self.knowledge_base,
                anthropic_api_key=self.config.anthropic_api_key,
                chat_config=self.config.get_chat_config()
            )
            print(f"✅ Assistant ready for knowledge base '{self.kb_name}'")
            return True
        except Exception as e:
            print(f"❌ Assistant creation failed: {e}")
            return False
    
    def interactive_chat(self):
        """Start interactive chat with the assistant."""
        stats = self.knowledge_base.get_statistics()
        
        print(f"\n💬 INTERACTIVE LITERATURE CHAT")
        print(f"=" * 45)
        print(f"Knowledge Base: '{self.kb_name}'")
        print(f"Documents: {stats['total_documents']} | Chunks: {stats['total_chunks']}")
        print(f"Type 'quit' to exit, 'help' for commands")
        print()
        
        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() in ['help', 'h']:
                    self._show_help()
                    continue
                
                if user_input.lower() == 'stats':
                    self._show_stats()
                    continue
                
                if user_input.lower() == 'kb':
                    self._show_kb_info()
                    continue
                
                if user_input.lower() == 'switch':
                    self._switch_knowledge_base()
                    continue
                
                if user_input.lower() == 'clear':
                    self.assistant.clear_conversation()
                    print("🧹 Conversation cleared")
                    continue
                
                # Ask the assistant
                print("🤖 Assistant: ", end="", flush=True)
                start_time = time.time()
                
                response = self.assistant.ask(
                    user_input,
                    temperature=0.3,
                    max_context_chunks=5
                )
                
                print(f"{response.content}")
                
                # Show metadata
                if response.sources_used:
                    print(f"📚 Sources: {', '.join(response.sources_used)}")
                
                print(f"⏱️  ({response.processing_time:.1f}s, {response.context_chunks_used} chunks)")
                print()
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                print()
    
    def _show_help(self):
        """Show help commands."""
        print(f"📋 Available commands:")
        print(f"   help, h     - Show this help")
        print(f"   stats       - Show knowledge base statistics")
        print(f"   kb          - Show knowledge base info")
        print(f"   switch      - Switch to different knowledge base")
        print(f"   clear       - Clear conversation history")
        print(f"   quit, q     - Exit")
        print(f"\n💡 Example questions:")
        print(f"   - What is quantum error correction?")
        print(f"   - How do superconducting qubits work?")
        print(f"   - Explain quantum volume benchmarks")
        print()
    
    def _show_stats(self):
        """Show knowledge base statistics."""
        stats = self.knowledge_base.get_statistics()
        print(f"📊 Knowledge Base Statistics:")
        print(f"   Name: {stats['name']}")
        print(f"   Documents: {stats['total_documents']}")
        print(f"   Chunks: {stats['total_chunks']}")
        print(f"   Avg chunk length: {stats.get('avg_chunk_length', 0):.1f} words")
        print(f"   Embedding model: {stats['embedding_model']}")
        print(f"   Storage: {stats['storage_location']}")
        
        if stats.get('last_updated'):
            print(f"   Last updated: {time.strftime('%Y-%m-%d %H:%M', time.localtime(stats['last_updated']))}")
        
        if 'source_breakdown' in stats:
            print(f"   Sources:")
            for source, data in stats['source_breakdown'].items():
                if isinstance(data, dict):
                    print(f"     {source}: {data.get('documents', 0)} docs")
                else:
                    print(f"     {source}: {data} items")
        print()
    
    def _show_kb_info(self):
        """Show knowledge base information."""
        available_kbs = list_knowledge_bases(self.config.knowledge_bases_folder)
        
        print(f"📚 Knowledge Base Information:")
        print(f"   Current: {self.kb_name}")
        print(f"   Storage folder: {self.config.knowledge_bases_folder}")
        
        if available_kbs:
            print(f"   Available knowledge bases:")
            for kb in available_kbs:
                current_marker = "→ " if kb['name'] == self.kb_name else "  "
                last_updated = time.strftime('%Y-%m-%d', time.localtime(kb['last_updated'])) if kb['last_updated'] else 'Unknown'
                print(f"     {current_marker}{kb['name']} ({kb['size_mb']:.1f} MB, {last_updated})")
        else:
            print(f"   No other knowledge bases found")
        print()
    
    def _switch_knowledge_base(self):
        """Switch to a different knowledge base."""
        available_kbs = list_knowledge_bases(self.config.knowledge_bases_folder)
        
        if not available_kbs:
            print("❌ No other knowledge bases found")
            return
        
        print(f"📚 Available knowledge bases:")
        for i, kb in enumerate(available_kbs, 1):
            current_marker = "(current)" if kb['name'] == self.kb_name else ""
            last_updated = time.strftime('%Y-%m-%d', time.localtime(kb['last_updated'])) if kb['last_updated'] else 'Unknown'
            print(f"   {i}. {kb['name']} {current_marker} ({kb['size_mb']:.1f} MB, {last_updated})")
        
        try:
            choice = input(f"\nSelect knowledge base (1-{len(available_kbs)}) or 'cancel': ").strip()
            
            if choice.lower() == 'cancel':
                return
            
            kb_index = int(choice) - 1
            if 0 <= kb_index < len(available_kbs):
                new_kb_name = available_kbs[kb_index]['name']
                
                if new_kb_name == self.kb_name:
                    print(f"Already using '{new_kb_name}'")
                    return
                
                print(f"🔄 Switching to '{new_kb_name}'...")
                
                # Load new knowledge base
                new_kb = load_knowledge_base(new_kb_name, self.config.knowledge_bases_folder)
                if new_kb:
                    self.knowledge_base = new_kb
                    self.kb_name = new_kb_name
                    
                    # Create new assistant
                    self.assistant = LiteratureAssistant(
                        knowledge_base=self.knowledge_base,
                        anthropic_api_key=self.config.anthropic_api_key,
                        chat_config=self.config.get_chat_config()
                    )
                    
                    stats = self.knowledge_base.get_statistics()
                    print(f"✅ Switched to '{new_kb_name}' ({stats['total_documents']} docs, {stats['total_chunks']} chunks)")
                else:
                    print(f"❌ Failed to load knowledge base '{new_kb_name}'")
            else:
                print(f"❌ Invalid selection: {choice}")
                
        except (ValueError, KeyboardInterrupt):
            print(f"❌ Invalid input or cancelled")
        
        print()
    
    def check_zotero_integration(self):
        """Check and optionally set up Zotero integration."""
        print(f"\n📖 Checking Zotero Integration...")
        
        api_status = self.config.check_env_file()
        
        if api_status['zotero_configured']:
            print(f"✅ Zotero configured")
            try:
                # Test Zotero connection
                syncer = create_literature_syncer(self.config)
                collections = syncer.zotero_manager.get_collections()
                print(f"   Found {len(collections)} collections")
                
                if collections:
                    print(f"   Example collections:")
                    for coll in collections[:3]:
                        print(f"     - {coll['name']} ({coll['num_items']} items)")
                
                return True
            except Exception as e:
                print(f"⚠️  Zotero connection failed: {e}")
                return False
        else:
            print(f"⚠️  Zotero not configured (optional)")
            print(f"   To enable: Set ZOTERO_API_KEY and ZOTERO_LIBRARY_ID in .env")
            return False
    
    def run(self):
        """Run the complete enhanced quick start process."""
        # Setup
        if not self.setup():
            return False
        
        # Select knowledge base
        if not self.select_knowledge_base():
            return False
        
        # Optional Zotero check
        self.check_zotero_integration()
        
        # Build or load knowledge base
        if not self.build_or_load_knowledge_base():
            return False
        
        # Create assistant
        if not self.create_assistant():
            return False
        
        # Start interactive chat
        self.interactive_chat()
        
        return True


def show_knowledge_base_manager():
    """Show knowledge base management interface."""
    print("📚 KNOWLEDGE BASE MANAGER")
    print("=" * 40)
    
    try:
        config = PipelineConfig()
        available_kbs = list_knowledge_bases(config.knowledge_bases_folder)
        
        if available_kbs:
            print(f"Available knowledge bases:")
            for i, kb in enumerate(available_kbs, 1):
                last_updated = time.strftime('%Y-%m-%d %H:%M', time.localtime(kb['last_updated'])) if kb['last_updated'] else 'Unknown'
                print(f"   {i}. {kb['name']}")
                print(f"      Size: {kb['size_mb']:.1f} MB")
                print(f"      Updated: {last_updated}")
                print(f"      Model: {kb.get('embedding_model', 'unknown')}")
                print()
        else:
            print("No knowledge bases found.")
            print(f"Storage location: {config.knowledge_bases_folder}")
        
        print(f"💡 Use 'python quick_start_rag.py' to create or work with knowledge bases")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main entry point with argument handling."""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ['--list', '-l', 'list']:
            show_knowledge_base_manager()
            return
        elif sys.argv[1] in ['--help', '-h', 'help']:
            print("🚀 PHYSICS LITERATURE RAG - ENHANCED QUICK START")
            print("=" * 55)
            print()
            print("Usage:")
            print("  python quick_start_rag.py         - Interactive setup and chat")
            print("  python quick_start_rag.py list    - Show knowledge base manager")
            print("  python quick_start_rag.py help    - Show this help")
            print()
            print("Features:")
            print("  • Named knowledge bases with organized storage")
            print("  • Load existing or create new knowledge bases")
            print("  • Switch between knowledge bases during chat")
            print("  • Legacy cache migration support")
            print("  • Enhanced document management")
            return
    
    # Run interactive mode
    quick_start = EnhancedQuickStartRAG()
    quick_start.run()


if __name__ == "__main__":
    main()