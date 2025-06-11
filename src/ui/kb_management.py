# src/ui/kb_management.py
"""
Knowledge Base Management component for Physics Literature Synthesis Pipeline
Handles KB creation, management, and Zotero integration with redesigned selection interface
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
    
    def _render_kb_interface(self):
        """Render main KB management interface - UPDATED WITH STATUS CONSTANTS"""
        config = st.session_state.get('config')
        if not config:
            st.error("Configuration not loaded")
            return
        
        # KB Selection Section with new design
        self._render_kb_selection_section(config)
        
        st.markdown("---")
        
        # KB Creation Section
        self._render_kb_creation_section()


    
    def _render_kb_selection_section(self, config):
        """
        Render the redesigned KB selection interface
        """
        st.markdown("### 📖 Available Knowledge Bases")
        
        # Current session indicator
        current_session = self.session_manager.current_session if self.session_manager else None
        current_kb = current_session.knowledge_base_name if current_session else None
        
        if current_kb:
            st.success(f"✅ Current KB in session: **{current_kb}**")
        else:
            st.info("ℹ️ No knowledge base selected in current session")
        
        st.markdown("---")
        
        # Get available knowledge bases
        available_kbs = self._get_available_knowledge_bases(config)
        
        if not available_kbs:
            st.warning("📝 No knowledge bases available. Create one first!")
            return
        
        # Knowledge base selector
        # Use empty string as default to show placeholder
        kb_options = [""] + sorted(available_kbs)
        
        # Format function to show placeholder text
        def format_kb_option(option):
            if option == "":
                return "Choose a knowledge base..."
            return option
        
        selected_kb = st.selectbox(
            "**Select Knowledge Base:**",
            options=kb_options,
            format_func=format_kb_option,
            key="kb_selector",
            help="Select a knowledge base to use or manage"
        )
        
        # Show action buttons only when KB is selected
        if selected_kb and selected_kb != "":
            st.markdown("") # Add some spacing
            
            # Create columns for buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                use_clicked = st.button(
                    "🔄 Use", 
                    key="use_kb_btn", 
                    help="Load this KB into current session",
                    use_container_width=True
                )
                
            with col2:
                delete_clicked = st.button(
                    "🗑️ Delete", 
                    key="delete_kb_btn", 
                    help="Delete this knowledge base",
                    use_container_width=True,
                    type="secondary"
                )
            
            # Handle button clicks
            if use_clicked:
                self._handle_use_kb(selected_kb)
                
            if delete_clicked:
                self._handle_delete_kb_request(selected_kb)
        
        # Handle any pending delete confirmations
        self._handle_pending_delete_confirmations()
    
    def _get_available_knowledge_bases(self, config) -> List[str]:
        """
        Get list of available knowledge bases
        
        Args:
            config: Pipeline configuration
            
        Returns:
            List of knowledge base names
        """
        try:
            available_kbs_info = list_knowledge_bases(config.knowledge_bases_folder)
            
            if available_kbs_info and isinstance(available_kbs_info[0], dict):
                return [kb['name'] for kb in available_kbs_info]
            else:
                return available_kbs_info or []
                
        except Exception as e:
            st.error(f"❌ Failed to load knowledge bases: {e}")
            return []
    
    def _handle_use_kb(self, kb_name: str):
        """
        Handle loading KB into current session
        
        Args:
            kb_name: Name of the knowledge base to load
        """
        try:
            if not self.session_manager:
                st.error("❌ Session manager not available")
                return
                
            # Check if we have a current session
            if not self.session_manager.current_session:
                # Create a new session if none exists
                self.session_manager.create_session("New Session", auto_activate=True)
            
            # Set the knowledge base for current session
            success = self.session_manager.set_knowledge_base_for_current(kb_name)
            
            if success:
                # Update session state
                st.session_state.current_kb_name = kb_name
                
                # Show success message
                st.success(f"✅ Loaded **{kb_name}** into current session!")
                
                # Clear the selector to reset the interface
                if "kb_selector" in st.session_state:
                    st.session_state.kb_selector = ""
                
                # Add to session state for UI feedback
                st.session_state.show_kb_change_success = f"Knowledge base '{kb_name}' is now active"
                
                # Refresh the page to update current session indicator
                st.rerun()
            else:
                st.error(f"❌ Failed to load knowledge base: {kb_name}")
                
        except Exception as e:
            st.error(f"❌ Error loading knowledge base: {e}")
            # Log the error for debugging
            import traceback
            logger.error(f"KB loading error: {traceback.format_exc()}")
    
    def _handle_delete_kb_request(self, kb_name: str):
        """
        Handle KB deletion request - sets up confirmation dialog
        
        Args:
            kb_name: Name of the knowledge base to delete
        """
        # Store pending deletion in session state for confirmation
        confirmation_key = f"confirm_delete_{kb_name}"
        
        if confirmation_key not in st.session_state:
            st.session_state[confirmation_key] = True
            st.rerun()  # Refresh to show confirmation dialog
    
    def _handle_pending_delete_confirmations(self):
        """
        Handle any pending delete confirmations
        """
        # Find any pending confirmations
        confirmation_keys = [key for key in st.session_state.keys() 
                            if key.startswith("confirm_delete_")]
        
        for confirmation_key in confirmation_keys:
            # Extract KB name from key
            kb_name = confirmation_key.replace("confirm_delete_", "")
            
            # Show confirmation dialog
            st.warning(f"⚠️ **Confirm Deletion**")
            st.markdown(f"Are you sure you want to delete the knowledge base **'{kb_name}'**?")
            st.markdown("This action cannot be undone.")
            
            # Check for sessions using this KB
            try:
                affected_sessions = self.session_manager.get_sessions_for_knowledge_base(kb_name)
                if affected_sessions:
                    st.markdown(f"**📝 {len(affected_sessions)} session(s) are using this KB:**")
                    for session in affected_sessions[:3]:  # Show first 3
                        st.markdown(f"• {session['name']}")
                    if len(affected_sessions) > 3:
                        st.markdown(f"• ... and {len(affected_sessions) - 3} more")
                    st.markdown("*These sessions will continue without the KB.*")
            except:
                # If method doesn't exist, skip session checking
                pass
            
            # Create confirmation buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                confirm_yes = st.button(
                    "✅ Yes, Delete", 
                    key=f"confirm_yes_{kb_name}",
                    type="primary"
                )
                
            with col2:
                confirm_no = st.button(
                    "❌ Cancel", 
                    key=f"confirm_no_{kb_name}"
                )
            
            # Handle confirmation responses
            if confirm_yes:
                success = self._execute_kb_deletion(kb_name)
                if success:
                    st.success(f"🗑️ Successfully deleted knowledge base: **{kb_name}**")
                else:
                    st.error(f"❌ Failed to delete knowledge base: {kb_name}")
                
                # Clear confirmation state
                del st.session_state[confirmation_key]
                
                # Clear the selector
                if "kb_selector" in st.session_state:
                    st.session_state.kb_selector = ""
                
                st.rerun()
                
            elif confirm_no:
                # Clear confirmation state
                del st.session_state[confirmation_key]
                st.rerun()
            
            # Only handle one confirmation at a time
            break
    
    def _execute_kb_deletion(self, kb_name: str) -> bool:
        """
        Execute the actual deletion of a knowledge base
        
        Args:
            kb_name: Name of the knowledge base to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        try:
            config = st.session_state.config
            
            # Handle affected sessions first (if method exists)
            try:
                affected_count, affected_names = self.session_manager.handle_knowledge_base_deleted(kb_name)
                if affected_count > 0:
                    logger.info(f"Updated {affected_count} sessions that were using KB {kb_name}")
            except AttributeError:
                # Method doesn't exist yet, handle manually
                if (self.session_manager.current_session and 
                    self.session_manager.current_session.knowledge_base_name == kb_name):
                    self.session_manager.set_knowledge_base_for_current(None)
                    st.session_state.current_kb_name = None
            
            # Delete KB directory
            kb_path = config.knowledge_bases_folder / kb_name
            if kb_path.exists():
                import shutil
                shutil.rmtree(kb_path)
                logger.info(f"Deleted knowledge base directory: {kb_path}")
                return True
            else:
                logger.error(f"Knowledge base folder not found: {kb_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete KB {kb_name}: {e}")
            return False
    

    def _check_zotero_availability_for_kb_creation(self) -> tuple[bool, str]:
        """
        Check if Zotero is available for KB creation using status constants
        
        Returns:
            tuple: (is_available, status_message)
        """
        from ..utils.status_constants import (
            ZoteroStatus, 
            check_zotero_status, 
            is_zotero_working
        )
        
        # Get current Zotero status
        zotero_status, display_string = check_zotero_status(st.session_state)
        zotero_manager = st.session_state.get('zotero_manager')
        
        # Check if Zotero is working
        is_working = is_zotero_working(zotero_status, zotero_manager is not None)
        
        if is_working:
            return True, display_string
        else:
            # Return appropriate error message based on status
            if zotero_status == ZoteroStatus.NOT_CONFIGURED:
                return False, "Zotero not configured. Please set up your API credentials in Settings."
            elif zotero_status == ZoteroStatus.FAILED:
                return False, "Zotero connection failed. Please check your settings and try reconnecting."
            elif zotero_status == ZoteroStatus.CONNECTING:
                return False, "Zotero is currently connecting. Please wait for the connection to complete."
            else:
                return False, "Zotero status unknown. Please verify your connection in Settings."

    def _get_zotero_status_display(self) -> str:
        """Get formatted Zotero status display string"""
        from ..utils.status_constants import check_zotero_status
        
        zotero_status, display_string = check_zotero_status(st.session_state)
        return display_string



    # Keep the existing KB creation methods unchanged
    def _render_kb_creation_section(self):
        """Render knowledge base creation interface - UPDATED"""
        st.markdown("### 🆕 Create New Knowledge Base")
        
        # Show Zotero status in tab labels for better UX
        zotero_available, _ = self._check_zotero_availability_for_kb_creation()
        
        if zotero_available:
            zotero_status_display = self._get_zotero_status_display()
            tab2_label = f"🔗 From Zotero {zotero_status_display}"
        else:
            tab2_label = "🔗 From Zotero ❌"
        
        # Choose creation method
        tab1, tab2 = st.tabs(["📁 From Local Folders", tab2_label])
        
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
        """Render KB creation from Zotero collections - SIMPLIFIED UI VERSION"""
        st.markdown("**Create from Zotero Collections**")
        
        # Use the status constants for connection checking
        from ..utils.status_constants import (
            ZoteroStatus, 
            check_zotero_status, 
            is_zotero_working
        )
        
        # Check Zotero status
        zotero_status, display_string = check_zotero_status(st.session_state)
        zotero_manager = st.session_state.get('zotero_manager')
        
        # Simple status check (like in scripts)
        if not is_zotero_working(zotero_status, zotero_manager is not None):
            st.warning("🔗 Zotero not properly connected")
            st.markdown("Please check your Zotero configuration in Settings.")
            
            if st.button("🔄 Retry Connection", key="retry_zotero_kb"):
                st.rerun()
            return
        
        # Show connection success
        st.success(f"{display_string} to Zotero")
        
        # Get collections (simple approach)
        zotero_collections = st.session_state.get('zotero_collections', [])
        if not zotero_collections:
            try:
                zotero_collections = zotero_manager.get_collections()
                st.session_state.zotero_collections = zotero_collections
            except Exception as e:
                st.error(f"❌ Failed to load collections: {str(e)}")
                return
        
        if not zotero_collections:
            st.info("📭 No collections found")
            return
        
        # Simple UI layout
        kb_name = st.text_input(
            "Knowledge Base Name:",
            placeholder="my_zotero_kb",
            key="zotero_kb_name"
        )
        
        # Collection selection (simplified)
        collection_options = {f"{c['name']} ({c.get('num_items', 0)} items)": c 
                            for c in zotero_collections}
        
        selected_collection_names = st.multiselect(
            "Select Collections:",
            options=list(collection_options.keys()),
            help="Choose collections to include"
        )
        
        # Simple options
        col1, col2 = st.columns(2)
        with col1:
            download_pdfs = st.checkbox("📥 Download missing PDFs", value=True)
            max_downloads = st.slider("Max downloads per collection", 1, 20, 5) if download_pdfs else 0
        
        with col2:
            include_existing = st.checkbox("📄 Include existing PDFs", value=True)
            include_metadata = st.checkbox("📝 Include metadata", value=True)
        
        # Create button
        if st.button("🏗️ Create Knowledge Base", type="primary", key="create_zotero_kb"):
            if not kb_name.strip():
                st.error("❌ Please enter a knowledge base name")
                return
            
            if not selected_collection_names:
                st.error("❌ Please select at least one collection")
                return
            
            # Check if KB already exists (like in manage_knowledge_bases.py)
            config = st.session_state.config
            existing_kbs = list_knowledge_bases(config.knowledge_bases_folder)
            if any(kb['name'] == kb_name.strip() for kb in existing_kbs):
                st.error(f"❌ Knowledge base '{kb_name.strip()}' already exists")
                return
            
            # Prepare collection data
            selected_collections = [collection_options[name] for name in selected_collection_names]
            collection_data = [{'name': c['name'], 'key': c['key']} for c in selected_collections]
            
            # Create the KB
            self._create_kb_from_zotero(
                kb_name.strip(),
                collection_data,
                include_existing,
                download_pdfs,
                max_downloads,
                include_metadata
            )





    
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
                self._handle_use_kb(name)
            
            time.sleep(2)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            logger.error(f"Failed to create KB from folders: {e}")
            st.error(f"❌ Failed to create knowledge base: {str(e)}")
    
    def _create_kb_from_zotero(self, name: str, collection_data: list, 
                          include_existing_pdfs: bool, download_missing_pdfs: bool,
                          max_downloads: int, include_metadata_only: bool):
        """
        Create knowledge base from Zotero collections - SIMPLIFIED IMPLEMENTATION
        Based on patterns from quick_start_rag.py and manage_knowledge_bases.py
        
        Args:
            name: KB name
            collection_data: List of collection info dicts
            include_existing_pdfs: Whether to include existing PDFs
            download_missing_pdfs: Whether to download missing PDFs via DOI
            max_downloads: Maximum downloads per collection
            include_metadata_only: Whether to include metadata for items without PDFs
        """
        config = st.session_state.config
        zotero_manager = st.session_state.get('zotero_manager')
        
        if not zotero_manager:
            st.error("❌ Zotero manager not available")
            return
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Create the knowledge base (like in manage_knowledge_bases.py)
            status_text.text("🏗️ Creating knowledge base...")
            progress_bar.progress(10)
            
            kb_config = config.get_knowledge_base_config(name)
            kb = create_knowledge_base(
                name=name,
                base_storage_dir=config.knowledge_bases_folder,
                embedding_model=kb_config.embedding_model,
                chunk_size=kb_config.chunk_size,
                chunk_overlap=kb_config.chunk_overlap
            )
            
            st.success(f"✅ Knowledge base '{name}' created")
            
            # Step 2: Sync Zotero collections (like in quick_start_rag.py)
            if download_missing_pdfs:
                status_text.text("📥 Syncing Zotero collections with DOI downloads...")
                progress_bar.progress(30)
                
                success = self._sync_zotero_collections_for_kb(
                    collection_data, max_downloads, status_text, progress_bar
                )
                
                if not success:
                    st.warning("⚠️ Zotero sync had issues, but continuing with available files...")
            
            # Step 3: Build knowledge base from all available sources
            status_text.text("🧠 Building knowledge base...")
            progress_bar.progress(70)
            
            # Determine folders to include (like in quick_start_rag.py)
            folders_to_include = {}
            
            if include_existing_pdfs or download_missing_pdfs:
                # Include Zotero sync folder
                folders_to_include['zotero_folder'] = config.zotero_sync_folder
            
            if include_metadata_only:
                # For now, metadata-only is handled during sync
                pass
            
            # Build the knowledge base
            if folders_to_include:
                stats = kb.build_from_directories(
                    **folders_to_include,
                    force_rebuild=False
                )
            else:
                # Create empty KB for metadata-only
                stats = {
                    'total_documents': 0,
                    'total_chunks': 0,
                    'success_rate': 100.0,
                    'storage_location': str(kb.kb_dir)
                }
            
            progress_bar.progress(100)
            status_text.text("✅ Knowledge base created successfully!")
            
            # Show results (like in manage_knowledge_bases.py)
            st.success(f"🎉 Created knowledge base '{name}' from Zotero!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Collections", len(collection_data))
            with col2:
                st.metric("Documents", stats['total_documents'])
            with col3:
                st.metric("Chunks", stats['total_chunks'])
            
            # Offer to use in current session
            if st.button("🔄 Use in Current Session", key="use_new_zotero_kb"):
                self._handle_use_kb(name)
            
            # Cleanup
            time.sleep(2)
            progress_bar.empty()
            status_text.empty()
            
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            logger.error(f"Failed to create KB from Zotero: {e}")
            st.error(f"❌ Failed to create knowledge base: {str(e)}")


    def _sync_zotero_collections_for_kb(self, collection_data: list, max_downloads: int, 
                                   status_text, progress_bar) -> bool:
        """
        Sync Zotero collections for KB creation - SIMPLIFIED VERSION
        Based on sync_zotero_collections from quick_start_rag.py
        """
        config = st.session_state.config
        
        try:
            # Create literature syncer (like in quick_start_rag.py)
            from ..downloaders import create_literature_syncer
            syncer = create_literature_syncer(config)
            
            total_collections = len(collection_data)
            collections_synced = 0
            
            for i, collection_info in enumerate(collection_data):
                collection_name = collection_info['name']
                
                # Update progress
                progress = 30 + (i * 40 // total_collections)
                progress_bar.progress(progress)
                status_text.text(f"📚 Syncing: {collection_name}")
                
                try:
                    # Use the enhanced syncer method
                    result = syncer.sync_collection_with_doi_downloads_and_integration(
                        collection_name=collection_name,
                        max_doi_downloads=max_downloads,
                        update_knowledge_base=False,  # We'll handle KB building separately
                        headless=True,
                        integration_mode="download_only"  # Just download, don't modify Zotero
                    )
                    
                    # Check if sync was successful
                    if result.zotero_sync_result.total_items > 0:
                        collections_synced += 1
                        st.info(f"✅ {collection_name}: {result.zotero_sync_result.total_items} items, "
                            f"{result.zotero_sync_result.successful_doi_downloads} PDFs downloaded")
                    else:
                        st.warning(f"⚠️ {collection_name}: No items found")
                    
                except Exception as e:
                    logger.warning(f"Error syncing collection {collection_name}: {e}")
                    st.warning(f"⚠️ {collection_name}: Sync failed - {str(e)}")
                    continue
            
            # Summary
            if collections_synced > 0:
                st.success(f"📊 Synced {collections_synced}/{total_collections} collections")
                return True
            else:
                st.error("❌ No collections were successfully synced")
                return False
                
        except Exception as e:
            logger.error(f"Error during Zotero sync: {e}")
            st.error(f"❌ Zotero sync failed: {str(e)}")
            return False

    




    def _reload_zotero_collections(self):
        """Reload Zotero collections - SIMPLIFIED VERSION"""
        try:
            zotero_manager = st.session_state.get('zotero_manager')
            if not zotero_manager:
                st.error("❌ Zotero manager not available")
                return
            
            with st.spinner("🔄 Reloading collections..."):
                collections = zotero_manager.get_collections()
                st.session_state.zotero_collections = collections
                
                # Update status
                from ..utils.status_constants import set_zotero_status, ZoteroStatus
                set_zotero_status(st.session_state, ZoteroStatus.CONNECTED)
                
                st.success(f"✅ Loaded {len(collections)} collections")
                st.rerun()
                
        except Exception as e:
            logger.error(f"Failed to reload collections: {e}")
            st.error(f"❌ Failed to reload: {str(e)}")
            
            # Update status
            from ..utils.status_constants import set_zotero_status, ZoteroStatus
            set_zotero_status(st.session_state, ZoteroStatus.FAILED, str(e))


    # Additional utility function for better error handling
    def _check_kb_name_available(self, kb_name: str) -> bool:
        """Check if a knowledge base name is available"""
        config = st.session_state.config
        existing_kbs = list_knowledge_bases(config.knowledge_bases_folder)
        return not any(kb['name'] == kb_name for kb in existing_kbs)

    def _get_collection_preview(self, collection_key: str, zotero_manager) -> dict:
        """Get a quick preview of what's in a collection"""
        try:
            if hasattr(zotero_manager, 'get_collection_sync_summary_fast'):
                return zotero_manager.get_collection_sync_summary_fast(collection_key)
            else:
                # Fallback to basic method
                return zotero_manager.get_collection_sync_summary(collection_key)
        except Exception as e:
            return {'error': str(e), 'total_items': 0}



def render_kb_management_css():
    """Render CSS for KB management styling with enhanced selection interface"""
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
    
    /* Enhanced KB Selection Interface */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* KB Action Buttons */
    .stButton > button {
        border-radius: 8px;
        transition: all 0.3s ease;
        font-weight: 600;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button[kind="secondary"] {
        background: #f8fafc;
        border: 2px solid #e2e8f0;
        color: #64748b;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background: #fee2e2;
        border-color: #fca5a5;
        color: #dc2626;
        transform: translateY(-1px);
    }
    
    /* Current KB Indicator */
    .stSuccess {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border: 1px solid #c3e6cb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #d1ecf1 0%, #bee5eb 100%);
        border: 1px solid #bee5eb;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Confirmation Dialog Styling */
    .stWarning {
        background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%);
        border: 2px solid #f39c12;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(243, 156, 18, 0.2);
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
    
    /* Progress bar styling */
    .stProgress > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
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
    
    /* Error styling */
    .stError {
        background: linear-gradient(135deg, #fef2f2 0%, #fecaca 100%);
        border: 2px solid #ef4444;
        color: #991b1b;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.2);
    }
    
    /* Spacing improvements */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .kb-management-overlay {
            margin: 1rem;
            padding: 1rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)