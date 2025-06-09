#!/usr/bin/env python3
"""
Knowledge Base Manager Script

This script provides utilities for managing multiple physics literature knowledge bases.
Allows listing, creating, deleting, and getting information about knowledge bases.

Location: scripts/manage_knowledge_bases.py
"""

import sys
import time
from pathlib import Path

# Set up imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import PipelineConfig
from src.core import (
    create_knowledge_base, 
    load_knowledge_base, 
    list_knowledge_bases, 
    delete_knowledge_base
)

def list_command(config):
    """List all available knowledge bases."""
    print("📚 KNOWLEDGE BASE LISTING")
    print("=" * 40)
    
    available_kbs = list_knowledge_bases(config.knowledge_bases_folder)
    
    if not available_kbs:
        print("No knowledge bases found.")
        print(f"Storage location: {config.knowledge_bases_folder}")
        print(f"Run 'python quick_start_rag.py' to create your first knowledge base.")
        return
    
    print(f"Found {len(available_kbs)} knowledge base(s) in {config.knowledge_bases_folder}:")
    print()
    
    for i, kb in enumerate(available_kbs, 1):
        default_marker = " (default)" if kb['name'] == config.default_kb_name else ""
        last_updated = time.strftime('%Y-%m-%d %H:%M', time.localtime(kb['last_updated'])) if kb['last_updated'] else 'Unknown'
        
        print(f"{i}. {kb['name']}{default_marker}")
        print(f"   Path: {kb['path']}")
        print(f"   Size: {kb['size_mb']:.1f} MB")
        print(f"   Last updated: {last_updated}")
        print(f"   Embedding model: {kb.get('embedding_model', 'unknown')}")
        print()

def info_command(config, kb_name):
    """Show detailed information about a specific knowledge base."""
    print(f"📋 KNOWLEDGE BASE INFO: {kb_name}")
    print("=" * 50)
    
    kb = load_knowledge_base(kb_name, config.knowledge_bases_folder)
    
    if not kb:
        print(f"❌ Knowledge base '{kb_name}' not found.")
        print(f"Available: {[kb['name'] for kb in list_knowledge_bases(config.knowledge_bases_folder)]}")
        return
    
    stats = kb.get_statistics()
    
    print(f"Name: {stats['name']}")
    print(f"Storage: {stats['storage_location']}")
    print(f"Created: {time.strftime('%Y-%m-%d %H:%M', time.localtime(stats.get('created_at', 0)))}")
    print(f"Last updated: {time.strftime('%Y-%m-%d %H:%M', time.localtime(stats.get('last_updated', 0)))}")
    print()
    
    print(f"📊 Content Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Successful processing: {stats['successful_documents']}")
    print(f"   Failed processing: {stats['failed_documents']}")
    print(f"   Success rate: {stats['success_rate']:.1f}%")
    print(f"   Total words: {stats['total_words']:,}")
    print(f"   Total size: {stats['total_size_mb']:.1f} MB")
    print(f"   Average words per doc: {stats['avg_words_per_doc']:.0f}")
    print()
    
    print(f"🔍 Embedding Information:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Average chunk length: {stats.get('avg_chunk_length', 0):.1f} words")
    print(f"   Embedding model: {stats['embedding_model']}")
    print()
    
    if stats.get('source_breakdown'):
        print(f"📁 Source Breakdown:")
        for source, data in stats['source_breakdown'].items():
            if isinstance(data, dict):
                print(f"   {source}: {data.get('successful', 0)} docs, {data.get('words', 0):,} words")
            else:
                print(f"   {source}: {data} items")
        print()
    
    # List documents
    documents = kb.list_documents()
    if documents:
        print(f"📄 Documents ({len(documents)} total):")
        for doc in documents[:10]:  # Show first 10
            print(f"   • {doc['file_name']} ({doc['source_type']}, {doc['word_count']} words)")
        
        if len(documents) > 10:
            print(f"   ... and {len(documents) - 10} more documents")

def create_command(config, kb_name):
    """Create a new knowledge base."""
    print(f"🆕 CREATING KNOWLEDGE BASE: {kb_name}")
    print("=" * 50)
    
    # Check if it already exists
    existing_kbs = list_knowledge_bases(config.knowledge_bases_folder)
    if any(kb['name'] == kb_name for kb in existing_kbs):
        print(f"❌ Knowledge base '{kb_name}' already exists.")
        return False
    
    try:
        # Get configuration
        kb_config = config.get_knowledge_base_config(kb_name)
        
        # Create knowledge base
        kb = create_knowledge_base(
            name=kb_name,
            base_storage_dir=config.knowledge_bases_folder,
            embedding_model=kb_config.embedding_model,
            chunk_size=kb_config.chunk_size,
            chunk_overlap=kb_config.chunk_overlap
        )
        
        print(f"✅ Knowledge base '{kb_name}' created successfully")
        print(f"   Storage: {kb.kb_dir}")
        print(f"   Configuration: {kb_config.embedding_model}, {kb_config.chunk_size} words/chunk")
        print()
        print(f"💡 Next steps:")
        print(f"   1. Add documents to your document folders")
        print(f"   2. Run: python quick_start_rag.py")
        print(f"   3. Select '{kb_name}' to build the knowledge base")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create knowledge base: {e}")
        return False

def delete_command(config, kb_name):
    """Delete a knowledge base."""
    print(f"🗑️  DELETING KNOWLEDGE BASE: {kb_name}")
    print("=" * 50)
    
    # Check if it exists
    kb = load_knowledge_base(kb_name, config.knowledge_bases_folder)
    if not kb:
        print(f"❌ Knowledge base '{kb_name}' not found.")
        return False
    
    # Show info before deletion
    stats = kb.get_statistics()
    print(f"Knowledge base to delete:")
    print(f"   Name: {stats['name']}")
    print(f"   Documents: {stats['total_documents']}")
    print(f"   Chunks: {stats['total_chunks']}")
    print(f"   Size: {stats['total_size_mb']:.1f} MB")
    print()
    
    # Confirmation
    confirm = input(f"⚠️  Are you sure you want to delete '{kb_name}'? (type 'DELETE' to confirm): ").strip()
    
    if confirm != "DELETE":
        print("❌ Deletion cancelled.")
        return False
    
    try:
        success = delete_knowledge_base(kb_name, config.knowledge_bases_folder)
        if success:
            print(f"✅ Knowledge base '{kb_name}' deleted successfully")
            return True
        else:
            print(f"❌ Failed to delete knowledge base '{kb_name}'")
            return False
            
    except Exception as e:
        print(f"❌ Error during deletion: {e}")
        return False

def rename_command(config, old_name, new_name):
    """Rename a knowledge base."""
    print(f"📝 RENAMING KNOWLEDGE BASE: {old_name} → {new_name}")
    print("=" * 60)
    
    # Check if source exists
    old_kb = load_knowledge_base(old_name, config.knowledge_bases_folder)
    if not old_kb:
        print(f"❌ Knowledge base '{old_name}' not found.")
        return False
    
    # Check if target already exists
    existing_kbs = list_knowledge_bases(config.knowledge_bases_folder)
    if any(kb['name'] == new_name for kb in existing_kbs):
        print(f"❌ Knowledge base '{new_name}' already exists.")
        return False
    
    try:
        # Get old statistics
        old_stats = old_kb.get_statistics()
        
        # Create new knowledge base with same configuration
        new_kb = create_knowledge_base(
            name=new_name,
            base_storage_dir=config.knowledge_bases_folder,
            embedding_model=old_stats['embedding_model'],
            chunk_size=old_kb.config['chunk_size'],
            chunk_overlap=old_kb.config['chunk_overlap']
        )
        
        # Copy data (this is a simplified approach)
        print(f"🔄 Copying data from '{old_name}' to '{new_name}'...")
        
        # Copy embeddings and metadata
        import shutil
        shutil.copy2(old_kb.embeddings_file, new_kb.embeddings_file)
        shutil.copy2(old_kb.metadata_file, new_kb.metadata_file)
        
        # Update config with new name
        new_kb.config['name'] = new_name
        new_kb.config['last_updated'] = time.time()
        
        # Save new knowledge base
        new_kb.save_to_storage()
        
        # Delete old knowledge base
        old_kb.delete()
        
        print(f"✅ Knowledge base renamed successfully")
        print(f"   Old: {old_name}")
        print(f"   New: {new_name}")
        print(f"   Documents: {old_stats['total_documents']}")
        print(f"   Chunks: {old_stats['total_chunks']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during rename: {e}")
        return False

def migrate_legacy_command(config, target_name=None):
    """Migrate legacy cache file to new knowledge base system."""
    print(f"🔄 MIGRATING LEGACY CACHE")
    print("=" * 40)
    
    legacy_cache = config.get_legacy_cache_file()
    
    if not legacy_cache.exists():
        print(f"❌ No legacy cache file found at: {legacy_cache}")
        return False
    
    target_kb_name = target_name or config.default_kb_name
    
    # Check if target already exists
    existing_kbs = list_knowledge_bases(config.knowledge_bases_folder)
    if any(kb['name'] == target_kb_name for kb in existing_kbs):
        print(f"❌ Knowledge base '{target_kb_name}' already exists.")
        print(f"Use a different name or delete the existing knowledge base first.")
        return False
    
    print(f"Migrating: {legacy_cache}")
    print(f"Target: {target_kb_name}")
    print()
    
    success = config.migrate_legacy_cache(target_kb_name)
    
    if success:
        print(f"✅ Migration completed successfully!")
        print(f"   New knowledge base: '{target_kb_name}'")
        print(f"   Legacy file backed up as: {legacy_cache}.backup")
        print()
        print(f"💡 Run 'python manage_knowledge_bases.py info {target_kb_name}' to see details")
    else:
        print(f"❌ Migration failed")
    
    return success

def main():
    """Main command-line interface."""
    if len(sys.argv) < 2:
        print("📚 KNOWLEDGE BASE MANAGER")
        print("=" * 40)
        print()
        print("Usage:")
        print("  python manage_knowledge_bases.py list")
        print("  python manage_knowledge_bases.py info <name>")
        print("  python manage_knowledge_bases.py create <name>")
        print("  python manage_knowledge_bases.py delete <name>")
        print("  python manage_knowledge_bases.py rename <old_name> <new_name>")
        print("  python manage_knowledge_bases.py migrate [target_name]")
        print()
        print("Examples:")
        print("  python manage_knowledge_bases.py list")
        print("  python manage_knowledge_bases.py info physics_main")
        print("  python manage_knowledge_bases.py create quantum_computing")
        print("  python manage_knowledge_bases.py delete old_project")
        print("  python manage_knowledge_bases.py migrate physics_legacy")
        return
    
    try:
        config = PipelineConfig()
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    command = sys.argv[1].lower()
    
    if command == "list":
        list_command(config)
        
    elif command == "info":
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_knowledge_bases.py info <name>")
            return
        info_command(config, sys.argv[2])
        
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_knowledge_bases.py create <name>")
            return
        create_command(config, sys.argv[2])
        
    elif command == "delete":
        if len(sys.argv) < 3:
            print("❌ Usage: python manage_knowledge_bases.py delete <name>")
            return
        delete_command(config, sys.argv[2])
        
    elif command == "rename":
        if len(sys.argv) < 4:
            print("❌ Usage: python manage_knowledge_bases.py rename <old_name> <new_name>")
            return
        rename_command(config, sys.argv[2], sys.argv[3])
        
    elif command == "migrate":
        target_name = sys.argv[2] if len(sys.argv) > 2 else None
        migrate_legacy_command(config, target_name)
        
    else:
        print(f"❌ Unknown command: {command}")
        print("Available commands: list, info, create, delete, rename, migrate")

if __name__ == "__main__":
    main()