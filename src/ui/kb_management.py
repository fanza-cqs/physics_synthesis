# src/ui/kb_management.py
"""
Knowledge Base Management component for Physics Literature Synthesis Pipeline
Handles KB creation, management, and Zotero integration in overlay mode
"""

import streamlit as st
from typing import List, Dict, Optional
from pathlib import Path
import time

from ..sessions import SessionManager
from ..core import create_knowledge_base, load_knowledge_base, list_knowledge_bases
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class KBManagement:
    """
    Knowledge Base Management interface
    Renders as overlay when called from sidebar
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize KB management component
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
    
    def render_overlay(self):
        """Render KB management as overlay dialog"""
        st.markdown("## 📚 Knowledge Base Management")
        
        # Close button
        if st.button("✖️ Close", key="close_kb_management"):
            st.session_state.show_kb_management = False
            st.rerun()
        
        st.markdown("---")
        
        # Main KB management interface
        self._render_kb_interface()
    
    def _render_kb_interface(self):
        """Render main KB management interface"""
        config = st.session_state.get('config')
        if not config:
            st.error("Configuration not loaded")
            return
        
        # Get available knowledge bases
        available_kbs_info = list_knowledge_bases(config.knowledge_bases_folder)
        
        if available_kbs_info and isinstance(available_kbs_info[0], dict):
            available_kbs = [kb['name'] for kb in available_kbs_info]
        else:
            available_kbs = available_kbs_info or []
        
        # Current KB status
        current_session = self.session_manager.current_session
        current_kb = current_session.knowledge_base_name if current_session else None
        
        if current_kb:
            st.success(f"✅ **Current KB in session:** {current_kb}")
        else:
            st.info("💬 **Current session:** No knowledge base (pure chat mode)")
        
        # KB Selection Section
        if available_kbs:
            st.markdown("### 📖 Available Knowledge Bases")
            
            for kb_name in available_kbs:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                
                with col1:
                    is_current = kb_name == current_kb
                    status_icon = "✅" if is_current else "📚"
                    st.markdown(f"{status_icon} **{kb_name}**")
                
                with col2:
                    if st.button("📊 Stats", key=f"stats_{kb_name}"):
                        self._show_kb_stats(kb_name)
                
                with col3:
                    if not is_current:
                        if st.button("🔄 Use", key=f"use_{kb_name}"):
                            self._switch_to_kb(kb_name)
                    else:
                        st.markdown("*Active*")
                
                with col4:
                    if st.button("🗑️", key=f"delete_{kb_name}", help="Delete KB"):
                        st.session_state[f'confirm_delete_kb_{kb_name}'] = True
                        st.rerun()
                
                # Delete confirmation dialog
                if st.session_state.get(f'confirm_delete_kb_{kb_name}', False):
                    self._render_delete_kb_confirmation(kb_name)
        else:
            st.info("📭 No knowledge bases found. Create one below.")
        
        st.markdown("---")
        
        # KB Creation Section
        self._render_kb_creation_section()
    
    def _show_kb_stats(self, kb_name: str):
        """Show knowledge base statistics"""
        config = st.session_state.config
        
        try:
            kb = load_knowledge_base(kb_name, config.knowledge_bases_folder)
            
            if kb:
                stats = kb.get_statistics()
                
                st.markdown(f"#### 📊 Statistics for {kb_name}")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Documents", stats.get('total_documents', 0))
                with col2:
                    st.metric("Chunks", stats.get('total_chunks', 0))
                with col3:
                    st.metric("Words", f"{stats.get('total_words', 0):,}")
                with col4:
                    st.metric("Size (MB)", f"{stats.get('total_size_mb', 0):.1f}")
                
                # Additional stats if available
                if stats.get('documents_by_type'):
                    st.markdown("**Document Types:**")
                    for doc_type, count in stats['documents_by_type'].items():
                        st.markdown(f"• {doc_type}: {count}")
            else:
                st.error(f"Failed to load knowledge base: {kb_name}")
                
        except Exception as e:
            st.error(f"Error loading KB stats: {e}")
    
    def _switch_to_kb(self, kb_name: str):
        """Switch current session to use specified KB"""
        if self.session_manager.set_knowledge_base_for_current(kb_name):
            st.success(f"✅ Switched to knowledge base: {kb_name}")
            st.session_state.show_kb_management = False
            st.rerun()
        else:
            st.error("Failed to switch knowledge base")
    
    def _render_delete_kb_confirmation(self, kb_name: str):
        """Render KB deletion confirmation dialog"""
        st.warning(f"**Delete Knowledge Base: {kb_name}**")
        st.markdown("⚠️ This will permanently delete the knowledge base and all its data.")
        st.markdown("*This action cannot be undone.*")
        
        # Check for sessions using this KB
        affected_sessions = self.session_manager.get_sessions_for_knowledge_base(kb_name)
        if affected_sessions:
            st.markdown(f"**📝 {len(affected_sessions)} session(s) are using this KB:**")
            for session in affected_sessions[:3]:  # Show first 3
                st.markdown(f"• {session['name']}")
            if len(affected_sessions) > 3:
                st.markdown(f"• ... and {len(affected_sessions) - 3} more")
            st.markdown("*These sessions will continue without the KB.*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete", key=f"confirm_delete_kb_yes_{kb_name}"):
                self._delete_kb(kb_name)
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_delete_kb_{kb_name}"):
                st.session_state[f'confirm_delete_kb_{kb_name}'] = False
                st.rerun()
    
    def _delete_kb(self, kb_name: str):
        """Delete a knowledge base"""
        config = st.session_state.config
        
        try:
            # Handle affected sessions first
            affected_count, affected_names = self.session_manager.handle_knowledge_base_deleted(kb_name)
            
            # Delete KB directory
            kb_path = config.knowledge_bases_folder / kb_name
            if kb_path.exists():
                import shutil
                shutil.rmtree(kb_path)
                
                st.success(f"✅ Deleted knowledge base: {kb_name}")
                
                if affected_count > 0:
                    st.info(f"📝 Updated {affected_count} session(s) that were using this KB")
                
                # Clear deletion confirmation
                st.session_state[f'confirm_delete_kb_{kb_name}'] = False
                
                # If current session was using this KB, it's already handled by session manager
                st.rerun()
            else:
                st.error("Knowledge base folder not found")
                
        except Exception as e:
            logger.error(f"Failed to delete KB {kb_name}: {e}")
            st.error(f"Failed to delete knowledge base: {str(e)}")
    
    def _render_kb_creation_section(self):
        """Render knowledge base creation interface"""
        st.markdown("### 🆕 Create New Knowledge Base")
        
        # Choose creation method
        tab1, tab2 = st.tabs(["📁 From Local Folders", "🔗 From Zotero"])
        
        with tab1:
            self._render_folder_kb_creation()
        
        with tab2:
            self._render_zotero_kb_creation()
    
    def _render_folder_kb_creation(self):
        """Render KB creation from local folders"""
        st.markdown("**Create from Local Document Folders**")
        
        config = st.session_state.config
        
        # KB name input
        kb_name = st.text_input(
            "Knowledge Base Name:",
            placeholder="my_research_kb",
            key="folder_kb_name"
        )
        
        # Folder selection
        st.markdown("**Select source folders:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            include_literature = st.checkbox("📚 Literature folder", value=True, key="include_lit")
            include_your_work = st.checkbox("📝 Your work folder", value=True, key="include_work")
        
        with col2:
            include_drafts = st.checkbox("✏️ Current drafts", value=False, key="include_drafts")
            include_manual = st.checkbox("📂 Manual references", value=True, key="include_manual")
        
        # Show folder status
        self._show_folder_status(config, include_literature, include_your_work, include_drafts, include_manual)
        
        # Create button
        if st.button("🏗️ Create Knowledge Base", key="create_folder_kb", type="primary"):
            if kb_name.strip():
                self._create_kb_from_folders(
                    kb_name.strip(), 
                    include_literature, 
                    include_your_work, 
                    include_drafts, 
                    include_manual
                )
            else:
                st.error("Please enter a knowledge base name")
    
    def _render_zotero_kb_creation(self):
        """Render KB creation from Zotero collections"""
        if not st.session_state.get('zotero_available', False):
            st.warning("🔗 Zotero integration not available")
            st.markdown("Install dependencies: `pip install pyzotero selenium`")
            return
        
        zotero_status = st.session_state.get('zotero_status', 'unknown')
        
        if zotero_status != 'connected':
            st.warning("🔗 Zotero not connected")
            st.markdown("Configure Zotero in Settings first")
            return
        
        st.markdown("**Create from Zotero Collections**")
        
        # KB name input
        kb_name = st.text_input(
            "Knowledge Base Name:",
            placeholder="zotero_physics_kb",
            key="zotero_kb_name"
        )
        
        # Collection selection
        zotero_collections = st.session_state.get('zotero_collections', [])
        
        if not zotero_collections:
            st.info("📭 No Zotero collections found")
            if st.button("🔄 Reload Collections", key="reload_collections"):
                self._reload_zotero_collections()
            return
        
        collection_options = {}
        for coll in zotero_collections:
            name = coll['name']
            items = coll.get('num_items', 0)
            collection_options[f"{name} ({items} items)"] = coll['key']
        
        selected_collections = st.multiselect(
            "Select Zotero collections:",
            options=list(collection_options.keys()),
            key="selected_zotero_collections",
            help="Choose collections to include in the knowledge base"
        )
        
        # Options
        col1, col2 = st.columns(2)
        
        with col1:
            enable_doi = st.checkbox("📥 Download PDFs via DOI", value=True, key="enable_doi")
        
        with col2:
            if enable_doi:
                max_downloads = st.slider("Max downloads per collection", 1, 50, 10, key="max_doi")
            else:
                max_downloads = 0
        
        # Create button
        if st.button("🏗️ Create from Zotero", key="create_zotero_kb", type="primary"):
            if kb_name.strip() and selected_collections:
                collection_keys = [collection_options[name] for name in selected_collections]
                self._create_kb_from_zotero(kb_name.strip(), collection_keys, enable_doi, max_downloads)
            else:
                st.error("Please enter a KB name and select at least one collection")
    
    def _show_folder_status(self, config, lit, work, drafts, manual):
        """Show status of selected folders"""
        st.markdown("**Folder Status:**")
        
        folders = []
        if lit:
            folders.append(("Literature", config.literature_folder))
        if work:
            folders.append(("Your Work", config.your_work_folder))
        if drafts:
            folders.append(("Drafts", config.current_drafts_folder))
        if manual:
            folders.append(("Manual Refs", config.manual_references_folder))
        
        if not folders:
            st.warning("⚠️ No folders selected")
            return
        
        total_files = 0
        for name, path in folders:
            if path.exists():
                files = list(path.glob("**/*"))
                file_count = len([f for f in files if f.is_file()])
                total_files += file_count
                st.markdown(f"• **{name}**: ✅ {file_count} files")
            else:
                st.markdown(f"• **{name}**: ❌ Folder not found")
        
        if total_files > 0:
            st.info(f"📊 Total: {total_files} files will be processed")
        else:
            st.warning("⚠️ No files found in selected folders")
    
    def _create_kb_from_folders(self, name: str, lit: bool, work: bool, drafts: bool, manual: bool):
        """Create knowledge base from local folders"""
        config = st.session_state.config
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            status_text.text("🏗️ Creating knowledge base...")
            progress_bar.progress(20)
            
            # Create knowledge base
            kb = create_knowledge_base(name, config.knowledge_bases_folder)
            
            progress_bar.progress(40)
            status_text.text("📁 Scanning folders...")
            
            # Build from selected folders
            folders = {}
            if lit and config.literature_folder.exists():
                folders['literature_folder'] = config.literature_folder
            if work and config.your_work_folder.exists():
                folders['your_work_folder'] = config.your_work_folder
            if drafts and config.current_drafts_folder.exists():
                folders['current_drafts_folder'] = config.current_drafts_folder
            if manual and config.manual_references_folder.exists():
                folders['manual_references_folder'] = config.manual_references_folder
            
            if not folders:
                st.warning("⚠️ No valid source folders found")
                return
            
            progress_bar.progress(60)
            status_text.text("🧠 Processing documents...")
            
            # Build knowledge base
            stats = kb.build_from_directories(**folders, force_rebuild=True)
            
            progress_bar.progress(100)
            status_text.text("✅ Knowledge base created!")
            
            st.success(f"✅ Created '{name}' with {stats['total_documents']} documents")
            
            # Offer to use in current session
            if st.button("🔄 Use in Current Session", key="use_new_kb"):
                self._switch_to_kb(name)
            
            time.sleep(2)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            logger.error(f"Failed to create KB from folders: {e}")
            st.error(f"❌ Failed to create knowledge base: {str(e)}")
    
    def _create_kb_from_zotero(self, name: str, collection_keys: List[str], enable_doi: bool, max_downloads: int):
        """Create knowledge base from Zotero collections"""
        # This would use the existing Zotero integration code
        # For now, show a placeholder
        st.info("🚧 Zotero KB creation will be implemented in the next phase")
        
        # TODO: Implement Zotero KB creation
        # This should integrate with the existing Zotero code from the original app
    
    def _reload_zotero_collections(self):
        """Reload Zotero collections"""
        try:
            zotero_manager = st.session_state.get('zotero_manager')
            if zotero_manager:
                collections = zotero_manager.get_collections()
                st.session_state.zotero_collections = collections
                st.success("✅ Reloaded Zotero collections")
                st.rerun()
            else:
                st.error("❌ Zotero manager not available")
        except Exception as e:
            logger.error(f"Failed to reload Zotero collections: {e}")
            st.error(f"❌ Failed to reload collections: {str(e)}")


def render_kb_management_css():
    """Render CSS for KB management styling"""
    st.markdown("""
    <style>
    /* KB management overlay styling */
    .kb-management-overlay {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 20px 40px rgba(0,0,0,0.1);
        max-width: 800px;
        margin: 2rem auto;
    }
    
    /* KB item styling */
    .kb-item {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    
    .kb-item:hover {
        background: #f1f5f9;
        border-color: #667eea;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.1);
    }
    
    /* Active KB highlighting */
    .kb-item.active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
    }
    
    /* Button styling in KB management */
    .stButton > button {
        border-radius: 6px;
        transition: all 0.3s ease;
    }
    
    /* Stats display */
    .kb-stats {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #f8fafc;
        border-radius: 8px;
        padding: 0.25rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 6px;
        background: transparent;
        border: none;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #e2e8f0;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Folder status styling */
    .folder-status {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    
    /* Warning/error styling */
    .stWarning {
        background: #fef3cd;
        border: 1px solid #f59e0b;
        color: #92400e;
        border-radius: 8px;
        padding: 1rem;
    }
    
    .stError {
        background: #fef2f2;
        border: 1px solid #ef4444;
        color: #991b1b;
        border-radius: 8px;
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)