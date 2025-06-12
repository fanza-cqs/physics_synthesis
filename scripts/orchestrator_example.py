#!/usr/bin/env python3
"""
Example usage of the Knowledge Base Orchestrator.

This script demonstrates how to use the new unified KB creation system.

Location: examples/orchestrator_example.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import PipelineConfig
from src.core import (
    KnowledgeBaseOrchestrator,
    KBOperation,
    SourceSelection
)
from src.utils.progress_tracker import ProgressManager, create_operation_id

def progress_callback(progress_state):
    """Callback function for progress updates."""
    print(f"Progress: {progress_state.progress_percentage:.1f}% - {progress_state.current_step}")

def example_create_new_kb():
    """Example: Create new knowledge base from multiple sources."""
    print("🚀 Example: Creating new knowledge base from multiple sources")
    print("=" * 60)
    
    # Load configuration
    config = PipelineConfig()
    
    # Initialize orchestrator
    orchestrator = KnowledgeBaseOrchestrator(config)
    orchestrator.set_progress_callback(progress_callback)
    
    # Configure source selection
    source_selection = SourceSelection(
        # Local folders
        use_local_folders=True,
        literature_folder=True,
        your_work_folder=True,
        current_drafts_folder=False,
        manual_references_folder=True,
        
        # Zotero (if available)
        use_zotero=True,
        zotero_collections=["Quantum Computing", "Machine Learning"],  # Example collections
        
        # Custom folder (example)
        use_custom_folder=True,
        custom_folder_path=Path("/path/to/custom/papers")  # Update this path
    )
    
    # Pre-process sources to get summary
    print("\n1. Pre-processing sources...")
    preprocessing = orchestrator.preprocess_sources(source_selection)
    
    print(f"📊 Found {preprocessing.total_documents} total documents:")
    if preprocessing.local_folders_summary:
        print("   Local folders:", preprocessing.local_folders_summary)
    if preprocessing.zotero_summary:
        print("   Zotero collections:", preprocessing.zotero_summary)
    if preprocessing.custom_folder_summary:
        print("   Custom folder:", preprocessing.custom_folder_summary)
    
    if preprocessing.error_messages:
        print("   Errors:", preprocessing.error_messages)
    
    if not preprocessing.has_valid_sources:
        print("❌ No valid sources found. Exiting.")
        return
    
    # Create knowledge base
    print("\n2. Creating knowledge base...")
    result = orchestrator.create_knowledge_base(
        kb_name="unified_physics_kb",
        source_selection=source_selection,
        operation=KBOperation.CREATE_NEW
    )
    
    # Display results
    print("\n3. Results:")
    if result.success:
        print(f"✅ Knowledge base created successfully!")
        print(f"   Name: {result.kb_name}")
        print(f"   Path: {result.kb_path}")
        print(f"   Documents: {result.total_documents}")
        print(f"   Chunks: {result.total_chunks}")
        print(f"   Sources processed: {result.sources_processed}")
        if result.sources_failed:
            print(f"   Sources failed: {result.sources_failed}")
        if result.is_partial:
            print(f"   ⚠️ KB marked as partial due to failed sources")
        print(f"   Processing time: {result.processing_time:.1f}s")
    else:
        print(f"❌ Knowledge base creation failed!")
        print(f"   Errors: {result.error_messages}")

def example_add_to_existing_kb():
    """Example: Add sources to existing knowledge base."""
    print("🔄 Example: Adding sources to existing knowledge base")
    print("=" * 60)
    
    config = PipelineConfig()
    orchestrator = KnowledgeBaseOrchestrator(config)
    orchestrator.set_progress_callback(progress_callback)
    
    # Configure source selection (only new sources to add)
    source_selection = SourceSelection(
        use_custom_folder=True,
        custom_folder_path=Path("/path/to/new/papers")  # Update this path
    )
    
    # Add to existing KB
    result = orchestrator.create_knowledge_base(
        kb_name="extended_kb",  # Name for the new combined KB
        source_selection=source_selection,
        operation=KBOperation.ADD_TO_EXISTING,
        existing_kb_name="unified_physics_kb"  # Existing KB to extend
    )
    
    if result.success:
        print(f"✅ Successfully extended knowledge base!")
        print(f"   New KB name: {result.kb_name}")
        print(f"   Total documents: {result.total_documents}")
    else:
        print(f"❌ Failed to extend knowledge base: {result.error_messages}")

def example_with_progress_tracking():
    """Example: KB creation with full progress tracking."""
    print("📈 Example: Knowledge base creation with progress tracking")
    print("=" * 60)
    
    config = PipelineConfig()
    
    # Initialize progress manager
    progress_manager = ProgressManager.get_instance()
    
    # Create operation ID
    operation_id = create_operation_id("tracked_kb", "create")
    
    # Start tracking
    progress_state = progress_manager.start_operation(
        operation_id=operation_id,
        kb_name="tracked_kb",
        operation_type="create_new",
        sources_total=2  # Example: local folders + custom folder
    )
    
    print(f"Started operation: {operation_id}")
    
    try:
        # Initialize orchestrator with progress callback
        orchestrator = KnowledgeBaseOrchestrator(config)
        
        def progress_callback_with_manager(message, percentage):
            progress_manager.update_progress(
                step=message,
                progress_percentage=percentage
            )
            print(f"Progress: {percentage:.1f}% - {message}")
        
        orchestrator.set_progress_callback(progress_callback_with_manager)
        
        # Configure minimal source selection for demo
        source_selection = SourceSelection(
            use_local_folders=True,
            literature_folder=True,
            your_work_folder=False,
            current_drafts_folder=False,
            manual_references_folder=False
        )
        
        # Create KB
        result = orchestrator.create_knowledge_base(
            kb_name="tracked_kb",
            source_selection=source_selection,
            operation=KBOperation.CREATE_NEW
        )
        
        # Complete tracking
        if result.success:
            progress_manager.complete_operation(success=True)
            print("✅ Operation completed successfully!")
        else:
            progress_manager.complete_operation(
                success=False, 
                error_message="; ".join(result.error_messages)
            )
            print("❌ Operation failed!")
    
    except Exception as e:
        progress_manager.complete_operation(success=False, error_message=str(e))
        print(f"❌ Operation failed with exception: {e}")
    
    # Show final progress
    final_state = progress_manager.get_current_progress()
    if final_state:
        print(f"Final status: {final_state.status.value}")

def main():
    """Run examples."""
    print("Knowledge Base Orchestrator Examples")
    print("=" * 40)
    
    # Note: These examples assume you have:
    # 1. Proper API keys configured
    # 2. Document folders with some content
    # 3. Zotero collections (for Zotero examples)
    # 4. Custom folder paths updated
    
    try:
        # Example 1: Create new KB (basic)
        example_create_new_kb()
        
        print("\n" + "=" * 60 + "\n")
        
        # Example 2: Add to existing KB
        # example_add_to_existing_kb()
        
        # Example 3: With progress tracking
        # example_with_progress_tracking()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure you have:")
        print("1. API keys configured in .env")
        print("2. Document folders with content")
        print("3. Updated custom folder paths in examples")

if __name__ == "__main__":
    main()