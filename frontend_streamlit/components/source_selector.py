#!/usr/bin/env python3
"""
Multi-Source Selector Component for Unified KB Creation.

Handles selection and validation of local folders, Zotero collections, and custom folders.

Location: frontend_streamlit/components/source_selector.py
"""

import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import time

from src.core import SourceSelection
from src.utils.kb_validation import check_zotero_availability

class SourceSelector:
    """
    Multi-source selector component for unified KB creation.
    
    Provides a clean interface for selecting and validating:
    - Local predefined folders
    - Zotero collections  
    - Custom user-selected folders
    """
    
    def __init__(self, config):
        """
        Initialize source selector.
        
        Args:
            config: PipelineConfig instance
        """
        self.config = config
        self.zotero_available = None
        self.zotero_collections = None
    
    def render(self, container=None) -> Optional[SourceSelection]:
        """
        Render the source selection interface.
        
        Args:
            container: Streamlit container to render in (optional)
            
        Returns:
            SourceSelection object if valid selection made, None otherwise
        """
        if container:
            with container:
                return self._render_selection_interface()
        else:
            return self._render_selection_interface()
    
    def _render_selection_interface(self) -> Optional[SourceSelection]:
        """Render the complete source selection interface."""
        st.markdown("### 📂 Select Knowledge Base Sources")
        st.markdown("Choose which sources to include in your knowledge base:")
        
        # Initialize source selection
        source_selection = SourceSelection()
        has_valid_selection = False
        
        # Local Folders Section
        local_valid = self._render_local_folders_section(source_selection)
        has_valid_selection = has_valid_selection or local_valid
        
        # Zotero Section
        zotero_valid = self._render_zotero_section(source_selection)
        has_valid_selection = has_valid_selection or zotero_valid
        
        # Custom Folder Section
        custom_valid = self._render_custom_folder_section(source_selection)
        has_valid_selection = has_valid_selection or custom_valid
        
        # Validation summary
        if has_valid_selection:
            self._render_selection_summary(source_selection)
            return source_selection
        else:
            st.info("👆 Please select at least one source above to continue")
            return None
    
    def _render_local_folders_section(self, source_selection: SourceSelection) -> bool:
        """Render local folders selection section."""
        with st.expander("📁 **Predefined Local Folders**", expanded=True):
            st.markdown("Include documents from your configured local folders:")
            
            # Main toggle
            source_selection.use_local_folders = st.checkbox(
                "Include local folders",
                value=False,
                key="use_local_folders",
                help="Include documents from your predefined document folders"
            )
            
            if not source_selection.use_local_folders:
                return False
            
            # Folder selection checkboxes
            st.markdown("**Select which folders to include:**")
            
            # Get folder info
            folder_info = self._get_local_folder_info()
            
            # Two-column layout for folder selection
            col1, col2 = st.columns(2)
            
            with col1:
                # Literature folder
                if folder_info['literature']['exists']:
                    label = f"📚 Literature folder ({folder_info['literature']['count']} files)"
                    source_selection.literature_folder = st.checkbox(
                        label, value=True, key="include_literature"
                    )
                else:
                    st.error("📚 Literature folder: ❌ Not found")
                    source_selection.literature_folder = False
                
                # Your work folder
                if folder_info['your_work']['exists']:
                    label = f"📝 Your work folder ({folder_info['your_work']['count']} files)"
                    source_selection.your_work_folder = st.checkbox(
                        label, value=True, key="include_your_work"
                    )
                else:
                    st.error("📝 Your work folder: ❌ Not found")
                    source_selection.your_work_folder = False
            
            with col2:
                # Current drafts folder
                if folder_info['current_drafts']['exists']:
                    label = f"✏️ Current drafts ({folder_info['current_drafts']['count']} files)"
                    source_selection.current_drafts_folder = st.checkbox(
                        label, value=False, key="include_drafts"
                    )
                else:
                    st.warning("✏️ Current drafts: ⚠️ Not found")
                    source_selection.current_drafts_folder = False
                
                # Manual references folder
                if folder_info['manual_references']['exists']:
                    label = f"📂 Manual references ({folder_info['manual_references']['count']} files)"
                    source_selection.manual_references_folder = st.checkbox(
                        label, value=True, key="include_manual"
                    )
                else:
                    st.warning("📂 Manual references: ⚠️ Not found")
                    source_selection.manual_references_folder = False
            
            # Check if any folders are selected
            folders_selected = (
                source_selection.literature_folder or
                source_selection.your_work_folder or 
                source_selection.current_drafts_folder or
                source_selection.manual_references_folder
            )
            
            if not folders_selected:
                st.error("❌ Please select at least one local folder")
                return False
            
            # Show selection summary
            total_files = sum(
                folder_info[key]['count'] for key in folder_info
                if getattr(source_selection, f"{key}_folder", False) and folder_info[key]['exists']
            )
            
            if total_files > 0:
                st.success(f"✅ Selected local folders with {total_files} total documents")
                return True
            else:
                st.error("❌ Selected folders contain no documents")
                return False
    
    def _render_zotero_section(self, source_selection: SourceSelection) -> bool:
        """Render Zotero collections selection section."""
        with st.expander("🔗 **Zotero Collections**", expanded=True):
            # Check Zotero availability
            if self.zotero_available is None:
                self.zotero_available, zotero_error = check_zotero_availability(self.config)
            
            if not self.zotero_available:
                st.error(f"❌ Zotero not available: {zotero_error}")
                st.markdown("💡 **To enable Zotero:** Set `ZOTERO_API_KEY` and `ZOTERO_LIBRARY_ID` in your `.env` file")
                source_selection.use_zotero = False
                return False
            
            # Zotero available - show selection interface
            st.markdown("Include documents from your Zotero collections:")
            
            source_selection.use_zotero = st.checkbox(
                "Include Zotero collections",
                value=False,
                key="use_zotero",
                help="Sync and include documents from selected Zotero collections"
            )
            
            if not source_selection.use_zotero:
                return False
            
            # Load collections if needed
            if self.zotero_collections is None:
                with st.spinner("Loading Zotero collections..."):
                    self.zotero_collections = self._load_zotero_collections()
            
            if not self.zotero_collections:
                st.error("❌ No Zotero collections found or connection failed")
                return False
            
            # Collection selection interface
            st.markdown("**Select collections to include:**")
            
            # Search/filter interface
            search_query = st.text_input(
                "Search collections:",
                key="zotero_search",
                placeholder="Type to filter collections...",
                help="Filter collections by name"
            )
            
            # Filter collections based on search
            filtered_collections = self.zotero_collections
            if search_query:
                filtered_collections = [
                    coll for coll in self.zotero_collections
                    if search_query.lower() in coll['name'].lower()
                ]
            
            if not filtered_collections:
                st.warning(f"No collections found matching '{search_query}'")
                return False
            
            # Multi-select for collections
            collection_options = [
                f"{coll['name']} ({coll['num_items']} items)" 
                for coll in filtered_collections
            ]
            
            selected_collection_labels = st.multiselect(
                "Choose collections:",
                collection_options,
                key="selected_zotero_collections",
                help="Select one or more Zotero collections to include"
            )
            
            if not selected_collection_labels:
                st.info("👆 Please select at least one collection")
                return False
            
            # Extract collection names from labels
            selected_names = []
            for label in selected_collection_labels:
                # Extract name from "Name (X items)" format
                name = label.split(" (")[0]
                selected_names.append(name)
            
            source_selection.zotero_collections = selected_names
            
            # Show selection summary
            selected_collections = [
                coll for coll in filtered_collections 
                if coll['name'] in selected_names
            ]
            
            total_items = sum(coll['num_items'] for coll in selected_collections)
            
            if total_items > 0:
                st.success(f"✅ Selected {len(selected_collections)} collections with {total_items} total items")
                
                # Show download estimation
                if total_items > 50:
                    estimated_time = total_items * 2  # Rough estimate: 2 seconds per item
                    st.info(f"⏱️ Estimated sync time: ~{estimated_time//60} minutes")
                
                return True
            else:
                st.warning("⚠️ Selected collections contain no items")
                return False
    
    def _render_custom_folder_section(self, source_selection: SourceSelection) -> bool:
        """Render custom folder selection section."""
        with st.expander("📂 **Custom Folder**", expanded=True):
            st.markdown("Include documents from a folder of your choice:")
            
            source_selection.use_custom_folder = st.checkbox(
                "Include custom folder",
                value=False,
                key="use_custom_folder",
                help="Browse and select any folder containing documents"
            )
            
            if not source_selection.use_custom_folder:
                return False
            
            # Folder path input
            st.markdown("**Enter folder path:**")
            
            # Path input with validation
            custom_path = st.text_input(
                "Folder path:",
                key="custom_folder_path",
                placeholder="/path/to/your/documents",
                help="Enter the full path to your document folder"
            )
            
            if not custom_path:
                st.info("👆 Please enter a folder path")
                return False
            
            # Validate path
            try:
                custom_folder = Path(custom_path).expanduser().resolve()
                
                if not custom_folder.exists():
                    st.error("❌ Folder does not exist")
                    return False
                
                if not custom_folder.is_dir():
                    st.error("❌ Path is not a directory")
                    return False
                
                # Check permissions
                try:
                    list(custom_folder.iterdir())
                except PermissionError:
                    st.error("❌ No permission to read this folder")
                    return False
                
                # Count documents
                doc_count = self._count_documents_in_folder(custom_folder)
                
                if doc_count == 0:
                    st.warning("⚠️ No supported documents found in this folder")
                    st.info("Supported formats: PDF, TeX, TXT")
                    return False
                
                # Success - store the path
                source_selection.custom_folder_path = custom_folder
                
                # Show folder info
                st.success(f"✅ Found {doc_count} documents in '{custom_folder.name}'")
                
                # Show folder details
                with st.expander("📋 Folder Details", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("📄 Documents", doc_count)
                        st.metric("📁 Folder Name", custom_folder.name)
                    with col2:
                        try:
                            folder_size = sum(
                                f.stat().st_size for f in custom_folder.rglob('*') 
                                if f.is_file()
                            ) / (1024 * 1024)  # MB
                            st.metric("💾 Size", f"{folder_size:.1f} MB")
                        except:
                            st.metric("💾 Size", "Unknown")
                        
                        st.metric("📂 Full Path", str(custom_folder))
                
                return True
                
            except Exception as e:
                st.error(f"❌ Error accessing folder: {e}")
                return False
    
    def _render_selection_summary(self, source_selection: SourceSelection):
        """Render summary of selected sources."""
        st.markdown("---")
        st.markdown("### 📊 Selection Summary")
        
        total_sources = 0
        estimated_docs = 0
        
        summary_items = []
        
        # Local folders summary
        if source_selection.use_local_folders:
            folder_info = self._get_local_folder_info()
            selected_folders = []
            local_docs = 0
            
            if source_selection.literature_folder and folder_info['literature']['exists']:
                selected_folders.append("Literature")
                local_docs += folder_info['literature']['count']
            
            if source_selection.your_work_folder and folder_info['your_work']['exists']:
                selected_folders.append("Your Work")
                local_docs += folder_info['your_work']['count']
            
            if source_selection.current_drafts_folder and folder_info['current_drafts']['exists']:
                selected_folders.append("Current Drafts")
                local_docs += folder_info['current_drafts']['count']
            
            if source_selection.manual_references_folder and folder_info['manual_references']['exists']:
                selected_folders.append("Manual References")
                local_docs += folder_info['manual_references']['count']
            
            if selected_folders:
                summary_items.append(f"📁 **Local Folders:** {', '.join(selected_folders)} ({local_docs} docs)")
                total_sources += 1
                estimated_docs += local_docs
        
        # Zotero summary
        if source_selection.use_zotero and source_selection.zotero_collections:
            if self.zotero_collections:
                selected_collections = [
                    coll for coll in self.zotero_collections 
                    if coll['name'] in source_selection.zotero_collections
                ]
                zotero_items = sum(coll['num_items'] for coll in selected_collections)
                
                collection_names = [coll['name'] for coll in selected_collections]
                summary_items.append(f"🔗 **Zotero:** {', '.join(collection_names)} ({zotero_items} items)")
                total_sources += 1
                estimated_docs += zotero_items
        
        # Custom folder summary
        if source_selection.use_custom_folder and source_selection.custom_folder_path:
            folder_name = source_selection.custom_folder_path.name
            doc_count = self._count_documents_in_folder(source_selection.custom_folder_path)
            summary_items.append(f"📂 **Custom Folder:** {folder_name} ({doc_count} docs)")
            total_sources += 1
            estimated_docs += doc_count
        
        # Display summary
        if summary_items:
            for item in summary_items:
                st.markdown(item)
            
            # Overall metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🎯 Sources", total_sources)
            with col2:
                st.metric("📄 Est. Documents", estimated_docs)
            with col3:
                if estimated_docs > 0:
                    # Rough processing time estimate
                    est_minutes = max(1, estimated_docs // 20)  # ~20 docs per minute
                    st.metric("⏱️ Est. Time", f"~{est_minutes}m")
        
        # Processing notes
        if estimated_docs > 100:
            st.info("💡 **Large dataset detected:** Processing may take several minutes. Consider using fewer sources for faster creation.")
        elif estimated_docs < 5:
            st.warning("⚠️ **Small dataset:** Consider adding more sources for better knowledge base coverage.")
    
    def _get_local_folder_info(self) -> Dict[str, Dict]:
        """Get information about local folders."""
        folders = {
            'literature': self.config.literature_folder,
            'your_work': self.config.your_work_folder,
            'current_drafts': self.config.current_drafts_folder,
            'manual_references': self.config.manual_references_folder
        }
        
        folder_info = {}
        for name, path in folders.items():
            if path and path.exists():
                count = self._count_documents_in_folder(path)
                folder_info[name] = {'exists': True, 'count': count, 'path': path}
            else:
                folder_info[name] = {'exists': False, 'count': 0, 'path': path}
        
        return folder_info
    
    def _load_zotero_collections(self) -> List[Dict]:
        """Load Zotero collections."""
        try:
            from src.downloaders import create_literature_syncer
            syncer = create_literature_syncer(self.config)
            collections = syncer.zotero_manager.get_collections()
            return sorted(collections, key=lambda x: x['name'])
        except Exception as e:
            st.error(f"Error loading Zotero collections: {e}")
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