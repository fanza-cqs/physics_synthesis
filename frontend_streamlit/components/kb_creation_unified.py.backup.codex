#!/usr/bin/env python3
"""
Unified Knowledge Base Creation Component for Physics Literature Synthesis Pipeline.

Single-page interface that replaces the tab-based system with unified source selection.

Location: frontend_streamlit/components/kb_creation_unified.py
"""

import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

from config.settings import PipelineConfig
from src.core import (
    KnowledgeBaseOrchestrator,
    KBOperation,
    SourceSelection,
    list_knowledge_bases
)
from src.utils.kb_validation import (
    validate_kb_name,
    validate_source_selection,
    validate_existing_kb,
    check_zotero_availability,
    generate_summary_text
)
from src.utils.progress_tracker import ProgressManager, create_operation_id

class UnifiedKBCreation:
    """
    Unified Knowledge Base Creation interface.
    
    Single page that handles all KB creation scenarios:
    - Create new KB
    - Replace existing KB 
    - Add to existing KB
    """
    
    def __init__(self):
        """Initialize the unified KB creation component."""
        self.config = st.session_state.get('config')
        if not self.config:
            st.error("Configuration not loaded")
            return
        
        self.orchestrator = KnowledgeBaseOrchestrator(self.config)
        self.progress_manager = ProgressManager.get_instance()
    
    def render(self):
        """Render the complete unified KB creation interface."""
        st.markdown("# 🏗️ Create Knowledge Base")
        st.markdown("Unified interface for creating knowledge bases from multiple sources")
        
        # Step 1: Operation Type Selection
        operation_type = self._render_operation_selection()
        
        if not operation_type:
            return
        
        st.markdown("---")
        
        # Step 2: KB Name and Target Selection
        kb_name, existing_kb_name = self._render_kb_naming(operation_type)
        
        if not kb_name:
            return
        
        st.markdown("---")
        
        # Step 3: Source Selection
        source_selection = self._render_source_selection()
        
        if not source_selection:
            return
        
        st.markdown("---")
        
        # Step 4: Pre-processing and Creation
        self._render_creation_section(operation_type, kb_name, existing_kb_name, source_selection)
    
    def _render_operation_selection(self) -> Optional[KBOperation]:
        """Render operation type selection section."""
        st.markdown("## 1. ⚙️ Operation Type")
        st.markdown("Choose what you want to do:")
        
        operation_options = {
            "Create new KB": KBOperation.CREATE_NEW,
            "Replace existing KB with updates": KBOperation.REPLACE_EXISTING,
            "Add to existing KB": KBOperation.ADD_TO_EXISTING
        }
        
        selected_operation = st.radio(
            "Select operation:",
            list(operation_options.keys()),
            key="operation_type",
            help="Choose whether to create a new knowledge base, replace an existing one, or add to an existing one"
        )
        
        operation = operation_options[selected_operation]
        
        # Show operation explanation
        explanations = {
            KBOperation.CREATE_NEW: "🆕 Create a brand new knowledge base from selected sources",
            KBOperation.REPLACE_EXISTING: "🔄 Replace all content in an existing knowledge base",
            KBOperation.ADD_TO_EXISTING: "➕ Add new sources to an existing knowledge base"
        }
        
        st.info(explanations[operation])
        
        return operation
    
    def _render_kb_naming(self, operation: KBOperation) -> tuple[Optional[str], Optional[str]]:
        """Render KB naming and existing KB selection."""
        st.markdown("## 2. 📝 Knowledge Base Details")
        
        existing_kb_name = None
        
        # For operations that need existing KB, show dropdown first
        if operation in [KBOperation.REPLACE_EXISTING, KBOperation.ADD_TO_EXISTING]:
            available_kbs = list_knowledge_bases(self.config.knowledge_bases_folder)
            
            if not available_kbs:
                st.error("❌ No existing knowledge bases found. Create a new one first.")
                return None, None
            
            kb_options = [kb['name'] for kb in available_kbs]
            
            existing_kb_name = st.selectbox(
                "Select existing knowledge base:",
                kb_options,
                key="existing_kb_selection",
                help="Choose the knowledge base to replace or extend"
            )
            
            if existing_kb_name:
                # Show existing KB info
                kb_info = next((kb for kb in available_kbs if kb['name'] == existing_kb_name), None)
                if kb_info:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Size", f"{kb_info['size_mb']:.1f} MB")
                    with col2:
                        if kb_info.get('last_updated'):
                            last_updated = time.strftime('%Y-%m-%d', time.localtime(kb_info['last_updated']))
                            st.metric("Last Updated", last_updated)
                    with col3:
                        st.metric("Model", kb_info.get('embedding_model', 'Unknown'))
        
        # KB name input
        if operation == KBOperation.CREATE_NEW:
            default_name = ""
            label = "New knowledge base name:"
            help_text = "Enter a unique name for your new knowledge base"
        elif operation == KBOperation.REPLACE_EXISTING:
            default_name = existing_kb_name if existing_kb_name else ""
            label = "Keep same name or enter new name:"
            help_text = "You can keep the same name or give it a new name"
        else:  # ADD_TO_EXISTING
            default_name = f"{existing_kb_name}_extended" if existing_kb_name else ""
            label = "Name for the combined knowledge base:"
            help_text = "Name for the new KB that combines existing + new sources"
        
        kb_name = st.text_input(
            label,
            value=default_name,
            key="kb_name_input",
            help=help_text,
            placeholder="my_research_kb"
        )
        
        # Validate KB name
        if kb_name:
            validation = validate_kb_name(kb_name)
            if not validation.is_valid:
                for error in validation.error_messages:
                    st.error(f"❌ {error}")
                return None, existing_kb_name
            
            for warning in validation.warning_messages:
                st.warning(f"⚠️ {warning}")
            
            # Check if KB already exists (for CREATE_NEW)
            if operation == KBOperation.CREATE_NEW:
                available_kbs = list_knowledge_bases(self.config.knowledge_bases_folder)
                existing_names = [kb['name'] for kb in available_kbs]
                if kb_name in existing_names:
                    st.error(f"❌ Knowledge base '{kb_name}' already exists. Choose a different name.")
                    return None, existing_kb_name
        
        return kb_name, existing_kb_name
    
    def _render_source_selection(self) -> Optional[SourceSelection]:
        """Render unified source selection interface."""
        st.markdown("## 3. 📂 Source Selection")
        st.markdown("Select sources to include in your knowledge base:")
        
        # Initialize source selection
        source_selection = SourceSelection()
        
        # Local Folders Section
        with st.expander("📁 **Predefined Local Folders**", expanded=True):
            source_selection.use_local_folders = st.checkbox(
                "Include local folders",
                value=False,
                key="use_local_folders",
                help="Include documents from your predefined local folders"
            )
            
            if source_selection.use_local_folders:
                st.markdown("**Select folders to include:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    source_selection.literature_folder = st.checkbox(
                        "📚 Literature folder",
                        value=True,
                        key="include_literature",
                        help="Papers and articles from literature"
                    )
                    source_selection.your_work_folder = st.checkbox(
                        "📝 Your work folder", 
                        value=True,
                        key="include_your_work",
                        help="Your own papers and documents"
                    )
                
                with col2:
                    source_selection.current_drafts_folder = st.checkbox(
                        "✏️ Current drafts",
                        value=False,
                        key="include_drafts",
                        help="Work-in-progress documents"
                    )
                    source_selection.manual_references_folder = st.checkbox(
                        "📂 Manual references",
                        value=True,
                        key="include_manual",
                        help="Manually added reference documents"
                    )
                
                # Show folder status
                self._show_local_folder_status(source_selection)
        
        # Zotero Section
        with st.expander("🔗 **Zotero Collections**", expanded=True):
            zotero_available, zotero_error = check_zotero_availability(self.config)
            
            if zotero_available:
                source_selection.use_zotero = st.checkbox(
                    "Include Zotero collections",
                    value=False,
                    key="use_zotero",
                    help="Include documents from your Zotero collections"
                )
                
                if source_selection.use_zotero:
                    collections = self._get_zotero_collections()
                    if collections:
                        selected_collections = st.multiselect(
                            "Select collections:",
                            [coll['name'] for coll in collections],
                            key="zotero_collections",
                            help="Choose which Zotero collections to include"
                        )
                        source_selection.zotero_collections = selected_collections
                        
                        # Show collection info
                        if selected_collections:
                            total_items = sum(
                                coll['num_items'] for coll in collections 
                                if coll['name'] in selected_collections
                            )
                            st.success(f"✅ Selected {len(selected_collections)} collections with {total_items} total items")
                    else:
                        st.warning("⚠️ No Zotero collections found")
            else:
                st.error(f"❌ Zotero not available: {zotero_error}")
                st.markdown("💡 **To enable Zotero:** Set `ZOTERO_API_KEY` and `ZOTERO_LIBRARY_ID` in your `.env` file")
        
        # Custom Folder Section
        with st.expander("📂 **Custom Folder**", expanded=True):
            source_selection.use_custom_folder = st.checkbox(
                "Include custom folder",
                value=False,
                key="use_custom_folder",
                help="Include documents from a folder you choose"
            )
            
            if source_selection.use_custom_folder:
                custom_path = st.text_input(
                    "Folder path:",
                    key="custom_folder_path",
                    help="Enter the full path to your custom folder",
                    placeholder="/path/to/your/documents"
                )
                
                if custom_path:
                    custom_folder = Path(custom_path)
                    if custom_folder.exists() and custom_folder.is_dir():
                        source_selection.custom_folder_path = custom_folder
                        doc_count = self._count_documents_in_folder(custom_folder)
                        st.success(f"✅ Found {doc_count} documents in {custom_folder.name}")
                    else:
                        st.error("❌ Folder does not exist or is not accessible")
                        source_selection.custom_folder_path = None
        
        # Validate source selection
        if source_selection.use_local_folders or source_selection.use_zotero or source_selection.use_custom_folder:
            validation = validate_source_selection(source_selection)
            if not validation.is_valid:
                for error in validation.error_messages:
                    st.error(f"❌ {error}")
                return None
            
            return source_selection
        else:
            st.info("👆 Please select at least one source above")
            return None
    
    def _render_creation_section(self, 
                                operation: KBOperation,
                                kb_name: str,
                                existing_kb_name: Optional[str],
                                source_selection: SourceSelection):
        """Render the pre-processing and creation section."""
        st.markdown("## 4. 🚀 Create Knowledge Base")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔍 Preview Sources", key="preview_sources", type="secondary"):
                self._run_preprocessing_preview(source_selection)
        
        with col2:
            create_disabled = not self._is_ready_for_creation()
            if st.button(
                "🏗️ Create Knowledge Base",
                key="create_kb",
                type="primary",
                disabled=create_disabled,
                help="Create the knowledge base with selected sources"
            ):
                self._run_kb_creation(operation, kb_name, existing_kb_name, source_selection)
    
    def _show_local_folder_status(self, source_selection: SourceSelection):
        """Show status of local folders."""
        if not source_selection.use_local_folders:
            return
        
        st.markdown("**📊 Folder Status:**")
        
        folders_to_check = []
        if source_selection.literature_folder:
            folders_to_check.append(("Literature", self.config.literature_folder))
        if source_selection.your_work_folder:
            folders_to_check.append(("Your Work", self.config.your_work_folder))
        if source_selection.current_drafts_folder:
            folders_to_check.append(("Current Drafts", self.config.current_drafts_folder))
        if source_selection.manual_references_folder:
            folders_to_check.append(("Manual References", self.config.manual_references_folder))
        
        for folder_name, folder_path in folders_to_check:
            if folder_path and folder_path.exists():
                doc_count = self._count_documents_in_folder(folder_path)
                st.success(f"• {folder_name}: ✅ {doc_count} files")
            else:
                st.error(f"• {folder_name}: ❌ Not found")
    
    def _get_zotero_collections(self) -> List[Dict]:
        """Get available Zotero collections."""
        try:
            from src.downloaders import create_literature_syncer
            syncer = create_literature_syncer(self.config)
            collections = syncer.zotero_manager.get_collections()
            return collections
        except Exception as e:
            st.error(f"Error fetching Zotero collections: {e}")
            return []
    
    def _count_documents_in_folder(self, folder: Path) -> int:
        """Count supported documents in a folder."""
        if not folder or not folder.exists():
            return 0
        
        extensions = {'.pdf', '.tex', '.txt'}
        count = 0
        
        try:
            for file_path in folder.rglob("*"):
                if file_path.is_file() and file_path.suffix.lower() in extensions:
                    count += 1
        except Exception:
            pass
        
        return count
    
    def _is_ready_for_creation(self) -> bool:
        """Check if all requirements are met for KB creation."""
        # This would check session state for valid inputs
        return (
            st.session_state.get('kb_name_input') and
            (st.session_state.get('use_local_folders') or 
             st.session_state.get('use_zotero') or 
             st.session_state.get('use_custom_folder'))
        )
    
    def _run_preprocessing_preview(self, source_selection: SourceSelection):
        """Run preprocessing and show preview of sources."""
        with st.spinner("🔍 Scanning sources..."):
            try:
                preprocessing = self.orchestrator.preprocess_sources(source_selection)
                
                st.markdown("### 📊 Source Preview")
                
                if preprocessing.has_valid_sources:
                    summary_text = generate_summary_text(preprocessing)
                    st.markdown(summary_text)
                    
                    # Store preprocessing results for creation
                    st.session_state.preprocessing_results = preprocessing
                    st.session_state.preprocessing_done = True
                else:
                    st.error("❌ No valid documents found in selected sources")
                    for error in preprocessing.error_messages:
                        st.error(f"• {error}")
                
            except Exception as e:
                st.error(f"❌ Error during preprocessing: {e}")
    
    def _run_kb_creation(self,
                        operation: KBOperation,
                        kb_name: str,
                        existing_kb_name: Optional[str],
                        source_selection: SourceSelection):
        """Run the actual KB creation process."""
        # Create operation ID for progress tracking
        operation_id = create_operation_id(kb_name, operation.value)
        
        # Progress tracking setup
        progress_placeholder = st.empty()
        
        def progress_callback(message: str, percentage: float):
            progress_placeholder.progress(
                percentage / 100.0,
                text=f"{percentage:.1f}% - {message}"
            )
        
        self.orchestrator.set_progress_callback(progress_callback)
        
        try:
            with st.spinner("🏗️ Creating knowledge base..."):
                result = self.orchestrator.create_knowledge_base(
                    kb_name=kb_name,
                    source_selection=source_selection,
                    operation=operation,
                    existing_kb_name=existing_kb_name
                )
            
            # Clear progress
            progress_placeholder.empty()
            
            # Show results
            if result.success:
                st.success("🎉 **Knowledge Base Created Successfully!**")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Documents", result.total_documents)
                with col2:
                    st.metric("🧩 Chunks", result.total_chunks)
                with col3:
                    st.metric("⏱️ Time", f"{result.processing_time:.1f}s")
                
                st.info(f"**Knowledge Base:** `{result.kb_name}`")
                st.info(f"**Location:** `{result.kb_path}`")
                
                if result.sources_processed:
                    st.success(f"**Sources processed:** {', '.join(result.sources_processed)}")
                
                if result.sources_failed:
                    st.warning(f"**Sources failed:** {', '.join(result.sources_failed)}")
                
                if result.is_partial:
                    st.warning("⚠️ **Partial creation:** Some sources failed, but KB was created with available data")
                
                # Option to use this KB in current session
                if st.button("🔄 Use this KB in current session", key="use_new_kb"):
                    # This would integrate with session management
                    st.session_state.current_kb = result.kb_name
                    st.success(f"✅ Now using KB: {result.kb_name}")
                    st.rerun()
            
            else:
                st.error("❌ **Knowledge Base Creation Failed**")
                for error in result.error_messages:
                    st.error(f"• {error}")
        
        except Exception as e:
            progress_placeholder.empty()
            st.error(f"❌ **Unexpected error:** {e}")

def render_unified_kb_creation():
    """Render the unified KB creation interface."""
    creator = UnifiedKBCreation()
    creator.render()

# CSS for styling
def render_kb_creation_css():
    """Render CSS for KB creation interface."""
    st.markdown("""
    <style>
    /* KB Creation specific styles */
    .stExpander {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .stExpander > div:first-child {
        background-color: #f8fafc;
    }
    
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Progress bar styling */
    .stProgress {
        margin: 1rem 0;
    }
    
    /* Source status styling */
    .source-status {
        padding: 0.5rem;
        margin: 0.25rem 0;
        border-radius: 4px;
        border-left: 4px solid;
    }
    
    .source-status.success {
        background-color: #f0f9ff;
        border-left-color: #10b981;
    }
    
    .source-status.error {
        background-color: #fef2f2;
        border-left-color: #ef4444;
    }
    </style>
    """, unsafe_allow_html=True)