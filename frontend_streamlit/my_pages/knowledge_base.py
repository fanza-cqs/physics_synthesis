#!/usr/bin/env python3
"""
Complete Integrated Knowledge Base Management Page.

Single file that contains all the unified KB creation functionality.
Ready to replace your existing frontend_streamlit/pages/knowledge_base.py

Location: frontend_streamlit/my_pages/knowledge_base.py
"""

import streamlit as st
from pathlib import Path
import time
from typing import Dict, List, Optional, Any
import sys

# ============================================================================
# Path Setup - CRITICAL: This must come before any src imports
# ============================================================================
current_dir = Path(__file__).parent
project_root = None

# Search upward for the config directory
for parent in [current_dir] + list(current_dir.parents):
    if (parent / "config").exists() and (parent / "src").exists():
        project_root = parent
        break

if project_root is None:
    st.error("❌ Could not find project root. Make sure you're running from within the physics_synthesis_pipeline directory.")
    st.stop()

# Add to Python path BEFORE importing src modules
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Core imports - NOW they should work
from config.settings import PipelineConfig
from src.core import (
    KnowledgeBaseOrchestrator,
    KBOperation,
    SourceSelection,
    list_knowledge_bases,
    load_knowledge_base,
    delete_knowledge_base
)
from src.utils.kb_validation import (
    validate_kb_name,
    validate_source_selection,
    check_zotero_availability,
    generate_summary_text
)
from src.utils.progress_tracker import (
    ProgressManager,
    create_operation_id
)
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# =============================================================================
# UNIFIED KB CREATION COMPONENT
# =============================================================================

class UnifiedKBCreation:
    """Unified Knowledge Base Creation interface - all in one component."""
    
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
        st.markdown("## 🏗️ Create or Update Knowledge Base")
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
        st.markdown("### 1. ⚙️ Operation Type")
        
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
        st.markdown("### 2. 📝 Knowledge Base Details")
        
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
        elif operation == KBOperation.REPLACE_EXISTING:
            default_name = existing_kb_name if existing_kb_name else ""
            label = "Keep same name or enter new name:"
        else:  # ADD_TO_EXISTING
            default_name = f"{existing_kb_name}_extended" if existing_kb_name else ""
            label = "Name for the combined knowledge base:"
        
        kb_name = st.text_input(
            label,
            value=default_name,
            key="kb_name_input",
            placeholder="my_research_kb"
        )
        
        # Validate KB name
        if kb_name:
            validation = validate_kb_name(kb_name)
            if not validation.is_valid:
                for error in validation.error_messages:
                    st.error(f"❌ {error}")
                return None, existing_kb_name
            
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
        st.markdown("### 3. 📂 Source Selection")
        
        # Initialize source selection
        source_selection = SourceSelection()
        
        # Local Folders Section
        with st.expander("📁 **Predefined Local Folders**", expanded=True):
            source_selection.use_local_folders = st.checkbox(
                "Include local folders",
                value=False,
                key="use_local_folders"
            )
            
            if source_selection.use_local_folders:
                col1, col2 = st.columns(2)
                
                with col1:
                    source_selection.literature_folder = st.checkbox(
                        "📚 Literature folder", value=True, key="include_literature"
                    )
                    source_selection.your_work_folder = st.checkbox(
                        "📝 Your work folder", value=True, key="include_your_work"
                    )
                
                with col2:
                    source_selection.current_drafts_folder = st.checkbox(
                        "✏️ Current drafts", value=False, key="include_drafts"
                    )
                    source_selection.manual_references_folder = st.checkbox(
                        "📂 Manual references", value=True, key="include_manual"
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
                    key="use_zotero"
                )
                
                if source_selection.use_zotero:
                    collections = self._get_zotero_collections()
                    if collections:
                        selected_collections = st.multiselect(
                            "Select collections:",
                            [coll['name'] for coll in collections],
                            key="zotero_collections"
                        )
                        source_selection.zotero_collections = selected_collections
                        
                        if selected_collections:
                            total_items = sum(
                                coll['num_items'] for coll in collections 
                                if coll['name'] in selected_collections
                            )
                            st.success(f"✅ Selected {len(selected_collections)} collections with {total_items} total items")
            else:
                st.error(f"❌ Zotero not available: {zotero_error}")
        
        # Custom Folder Section
        with st.expander("📂 **Custom Folder**", expanded=True):
            source_selection.use_custom_folder = st.checkbox(
                "Include custom folder",
                value=False,
                key="use_custom_folder"
            )
            
            if source_selection.use_custom_folder:
                custom_path = st.text_input(
                    "Folder path:",
                    key="custom_folder_path",
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
        st.markdown("### 4. 🚀 Create Knowledge Base")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🔍 Preview Sources", key="preview_sources", type="secondary"):
                self._run_preprocessing_preview(source_selection)
        
        with col2:
            if st.button("🏗️ Create Knowledge Base", key="create_kb", type="primary"):
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
    
    def _run_preprocessing_preview(self, source_selection: SourceSelection):
        """Run preprocessing and show preview of sources."""
        with st.spinner("🔍 Scanning sources..."):
            try:
                preprocessing = self.orchestrator.preprocess_sources(source_selection)
                
                st.markdown("#### 📊 Source Preview")
                
                if preprocessing.has_valid_sources:
                    summary_text = generate_summary_text(preprocessing)
                    st.markdown(summary_text)
                    st.session_state.preprocessing_results = preprocessing
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
        status_placeholder = st.empty()
        
        def progress_callback(message: str, percentage: float):
            progress_placeholder.progress(
                percentage / 100.0,
                text=f"{percentage:.1f}% - {message}"
            )
            
            with status_placeholder.container():
                st.info(f"🔄 {message}")
        
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
            status_placeholder.empty()
            
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
                if result.kb_path:
                    st.info(f"**Location:** `{result.kb_path}`")
                
                if result.sources_processed:
                    st.success(f"**Sources processed:** {', '.join(result.sources_processed)}")
                
                if result.sources_failed:
                    st.warning(f"**Sources failed:** {', '.join(result.sources_failed)}")
                
                if result.is_partial:
                    st.warning("⚠️ **Partial creation:** Some sources failed, but KB was created with available data")
                
                # Option to use this KB in current session
                if st.button("🔄 Use this KB in current session", key="use_new_kb"):
                    st.session_state.current_kb = result.kb_name
                    st.success(f"✅ Now using KB: {result.kb_name}")
                    st.rerun()
            
            else:
                st.error("❌ **Knowledge Base Creation Failed**")
                for error in result.error_messages:
                    st.error(f"• {error}")
        
        except Exception as e:
            progress_placeholder.empty()
            status_placeholder.empty()
            st.error(f"❌ **Unexpected error:** {e}")

# =============================================================================
# MAIN PAGE FUNCTIONS
# =============================================================================

def render_knowledge_base_page():
    """Render the unified knowledge base management page."""
    # Only set page config if running standalone (not within main app)
    if 'system_initialized' not in st.session_state:
        st.set_page_config(
            page_title="Knowledge Base Management",
            page_icon="📚",
            layout="wide"
        )
    
    # Load CSS
    render_css()
    
    # Page header
    st.markdown("# 📚 Knowledge Base Management")
    st.markdown("Create, manage, and explore your physics literature knowledge bases")
    
    # Check configuration
    if 'config' not in st.session_state:
        try:
            st.session_state.config = PipelineConfig()
        except Exception as e:
            st.error(f"❌ Configuration error: {e}")
            st.stop()
    
    config = st.session_state.config
    
    # Main interface tabs
    tab1, tab2, tab3 = st.tabs(["🏗️ Create/Update", "📖 Browse & Manage", "⚙️ Settings"])
    
    with tab1:
        render_creation_tab(config)
    
    with tab2:
        render_management_tab(config)
    
    with tab3:
        render_settings_tab(config)

def render_creation_tab(config):
    """Render the KB creation/update tab with unified interface."""
    try:
        creator = UnifiedKBCreation()
        creator.render()
    except Exception as e:
        st.error(f"❌ Error loading KB creation interface: {e}")
        logger.error(f"KB creation interface error: {e}")

def render_management_tab(config):
    """Render the KB management and browsing tab."""
    st.markdown("## Browse and Manage Knowledge Bases")
    
    # Get available knowledge bases
    available_kbs = list_knowledge_bases(config.knowledge_bases_folder)
    
    if not available_kbs:
        st.info("📝 No knowledge bases found. Create your first one in the **Create/Update** tab!")
        return
    
    # KB selection and info
    st.markdown("### 📖 Available Knowledge Bases")
    
    # KB selector
    kb_options = [kb['name'] for kb in available_kbs]
    selected_kb_name = st.selectbox(
        "Select knowledge base to manage:",
        kb_options,
        key="manage_kb_selector"
    )
    
    if selected_kb_name:
        render_kb_details(config, selected_kb_name, available_kbs)

def render_kb_details(config, kb_name: str, available_kbs: list):
    """Render detailed information and actions for a specific KB."""
    # Find KB info
    kb_info = next((kb for kb in available_kbs if kb['name'] == kb_name), None)
    if not kb_info:
        st.error(f"Knowledge base '{kb_name}' not found")
        return
    
    # KB Header
    st.markdown(f"### 📚 {kb_name}")
    
    # Basic info metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💾 Size", f"{kb_info['size_mb']:.1f} MB")
    
    with col2:
        if kb_info.get('last_updated'):
            last_updated = time.strftime('%Y-%m-%d', time.localtime(kb_info['last_updated']))
            st.metric("📅 Updated", last_updated)
    
    with col3:
        st.metric("🤖 Model", kb_info.get('embedding_model', 'Unknown'))
    
    with col4:
        if kb_info.get('created_at'):
            created = time.strftime('%Y-%m-%d', time.localtime(kb_info['created_at']))
            st.metric("🎂 Created", created)
    
    st.markdown("---")
    
    # Actions section
    st.markdown("### ⚡ Actions")
    
    action_col1, action_col2, action_col3, action_col4 = st.columns(4)
    
    with action_col1:
        if st.button("🔄 Use in Session", key=f"use_{kb_name}"):
            st.session_state.current_kb = kb_name
            st.success(f"✅ Now using KB: {kb_name}")
            st.rerun()
    
    with action_col2:
        if st.button("📊 View Statistics", key=f"stats_{kb_name}"):
            st.session_state.show_stats = kb_name
            st.rerun()
    
    with action_col3:
        if st.button("📝 Add Documents", key=f"add_{kb_name}"):
            st.info("💡 Use the **Create/Update** tab with 'Add to existing KB' option")
    
    with action_col4:
        if st.button("🗑️ Delete", key=f"delete_{kb_name}", type="secondary"):
            st.session_state.confirm_delete = kb_name
    
    # Handle delete confirmation
    if st.session_state.get('confirm_delete') == kb_name:
        st.markdown("---")
        st.error(f"⚠️ **Confirm Deletion of '{kb_name}'**")
        
        confirm_col1, confirm_col2 = st.columns([1, 1])
        
        with confirm_col1:
            if st.button("✅ Yes, Delete", key=f"confirm_yes_{kb_name}", type="primary"):
                try:
                    success = delete_knowledge_base(kb_name, config.knowledge_bases_folder)
                    if success:
                        st.success(f"✅ Knowledge base '{kb_name}' deleted successfully")
                        st.session_state.pop('confirm_delete', None)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to delete knowledge base '{kb_name}'")
                except Exception as e:
                    st.error(f"❌ Error deleting KB: {e}")
        
        with confirm_col2:
            if st.button("❌ Cancel", key=f"confirm_no_{kb_name}"):
                st.session_state.pop('confirm_delete', None)
                st.rerun()
    
    # Show detailed statistics if requested
    if st.session_state.get('show_stats') == kb_name:
        st.markdown("---")
        render_detailed_statistics(config, kb_name)

def render_detailed_statistics(config, kb_name: str):
    """Render detailed statistics for a knowledge base."""
    st.markdown(f"### 📊 Detailed Statistics for '{kb_name}'")
    
    try:
        kb = load_knowledge_base(kb_name, config.knowledge_bases_folder)
        if not kb:
            st.error("Failed to load knowledge base")
            return
        
        stats = kb.get_statistics()
        
        # Overview metrics
        st.markdown("#### 📈 Overview")
        overview_cols = st.columns(5)
        
        metrics_data = [
            ("Documents", stats.get('total_documents', 0), "📄"),
            ("Chunks", stats.get('total_chunks', 0), "🧩"),
            ("Words", f"{stats.get('total_words', 0):,}", "📝"),
            ("Size", f"{stats.get('total_size_mb', 0):.1f} MB", "💾"),
            ("Success Rate", f"{stats.get('success_rate', 0):.1f}%", "✅")
        ]
        
        for i, (label, value, icon) in enumerate(metrics_data):
            with overview_cols[i]:
                st.metric(f"{icon} {label}", value)
        
        # Close button
        if st.button("❌ Close Statistics", key=f"close_stats_{kb_name}"):
            st.session_state.pop('show_stats', None)
            st.rerun()
            
    except Exception as e:
        st.error(f"Error loading statistics: {e}")

def render_settings_tab(config):
    """Render the settings and configuration tab."""
    st.markdown("## ⚙️ Knowledge Base Settings")
    
    # API Configuration Status
    st.markdown("### 🔑 API Configuration")
    
    api_status = config.check_env_file()
    
    status_col1, status_col2 = st.columns(2)
    
    with status_col1:
        st.markdown("**Anthropic API:**")
        if api_status.get('anthropic_api_key'):
            st.success("✅ Configured")
        else:
            st.error("❌ Not configured")
            st.info("Set `ANTHROPIC_API_KEY` in your `.env` file")
    
    with status_col2:
        st.markdown("**Zotero API:**")
        if api_status.get('zotero_configured'):
            st.success("✅ Configured")
        else:
            st.warning("⚠️ Not configured (optional)")
            st.info("Set `ZOTERO_API_KEY` and `ZOTERO_LIBRARY_ID` in your `.env` file")
    
    # Storage Configuration
    st.markdown("### 💾 Storage Configuration")
    
    storage_info = [
        ("Knowledge Bases", config.knowledge_bases_folder),
        ("Literature Folder", config.literature_folder),
        ("Your Work Folder", config.your_work_folder),
        ("Current Drafts", config.current_drafts_folder),
        ("Manual References", config.manual_references_folder),
        ("Zotero Sync", config.zotero_sync_folder)
    ]
    
    for name, path in storage_info:
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            st.text(name)
        
        with col2:
            st.code(str(path) if path else "Not configured")
        
        with col3:
            if path and path.exists():
                st.success("✅")
            else:
                st.error("❌")

def render_css():
    """Render CSS for the entire page."""
    st.markdown("""
    <style>
    /* General styling */
    .stExpander {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .stExpander > div:first-child {
        background-color: #f8fafc;
    }
    
    /* Progress bar styling */
    .stProgress {
        margin: 1rem 0;
    }
    
    /* Metrics styling */
    .metric-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        border: 1px solid #e2e8f0;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Success/Error messages */
    .stSuccess {
        border-radius: 8px;
    }
    
    .stError {
        border-radius: 8px;
    }
    
    .stWarning {
        border-radius: 8px;
    }
    
    .stInfo {
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_knowledge_base_page()