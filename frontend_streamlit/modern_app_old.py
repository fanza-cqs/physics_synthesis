#!/usr/bin/env python3
"""
Enhanced Physics Research Assistant - Streamlit App
Now with full Zotero integration for building knowledge bases from collections
"""

import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
import time
import json

# ============================================================================
# PyTorch Compatibility Fix
# ============================================================================
try:
    import torch
    if not hasattr(torch, 'get_default_device'):
        def get_default_device():
            if torch.cuda.is_available():
                return torch.device('cuda')
            return torch.device('cpu')
        torch.get_default_device = get_default_device
        print("✅ Applied PyTorch compatibility fix")
except ImportError:
    print("⚠️ PyTorch not available - continuing without")

# ============================================================================
# Path Setup - Find project root
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

# Add to Python path
sys.path.insert(0, str(project_root))

# ============================================================================
# Imports - With Error Handling
# ============================================================================
try:
    from config import PipelineConfig
    CONFIG_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Config import failed: {e}")
    st.stop()

try:
    from src.core import KnowledgeBase, create_knowledge_base, load_knowledge_base, list_knowledge_bases
    CORE_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Core modules import failed: {e}")
    st.stop()

try:
    from src.chat import LiteratureAssistant
    CHAT_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Chat module not available: {e}")
    CHAT_AVAILABLE = False

try:
    from src.downloaders import (
        create_literature_syncer, 
        get_zotero_capabilities,
        EnhancedZoteroLiteratureSyncer,
        create_zotero_manager,
        print_zotero_status
    )
    ZOTERO_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Zotero modules not available: {e}")
    ZOTERO_AVAILABLE = False

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="Physics Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Session State Initialization
# ============================================================================
def init_session_state():
    """Initialize session state variables"""
    defaults = {
        'system_initialized': False,
        'config': None,
        'current_kb': None,
        'assistant': None,
        'chat_ready': False,
        'messages': [],
        'chat_temperature': 0.3,
        'chat_max_sources': 8,
        'zotero_manager': None,
        'zotero_collections': [],
        'selected_collections': [],
        'zotero_status': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================================================
# System Initialization
# ============================================================================
def initialize_system():
    """Initialize the system with proper error handling"""
    if st.session_state.system_initialized:
        return
    
    with st.spinner("🚀 Initializing Physics Research Assistant..."):
        try:
            # Initialize configuration
            config = PipelineConfig()
            config.project_root = project_root
            config._create_directories()
            st.session_state.config = config
            
            # Initialize Zotero manager if configured
            if ZOTERO_AVAILABLE and config.check_env_file().get('zotero_configured', False):
                try:
                    zotero_manager = create_zotero_manager(
                        config, 
                        prefer_enhanced=True, 
                        require_doi_downloads=False
                    )
                    st.session_state.zotero_manager = zotero_manager
                    st.session_state.zotero_status = "connected"
                    
                    # Load collections
                    load_zotero_collections()
                    
                except Exception as e:
                    st.session_state.zotero_status = f"error: {e}"
            else:
                st.session_state.zotero_status = "not_configured"
            
            st.session_state.system_initialized = True
            st.success("✅ System initialized successfully!")
            
        except Exception as e:
            st.error(f"❌ System initialization failed: {e}")
            st.session_state.system_initialized = False

def load_zotero_collections():
    """Load Zotero collections"""
    if st.session_state.zotero_manager:
        try:
            collections = st.session_state.zotero_manager.get_collections()
            st.session_state.zotero_collections = collections
        except Exception as e:
            st.warning(f"⚠️ Could not load Zotero collections: {e}")
            st.session_state.zotero_collections = []

# ============================================================================
# Zotero Integration Interface
# ============================================================================
def zotero_integration_interface():
    """Enhanced Zotero integration interface"""
    st.header("📚 Zotero Integration")
    
    config = st.session_state.config
    zotero_status = config.check_env_file()
    
    # Status display
    if st.session_state.zotero_status == "connected":
        st.success("✅ Connected to Zotero")
    elif st.session_state.zotero_status == "not_configured":
        st.warning("⚙️ Zotero not configured")
    else:
        st.error(f"❌ Zotero error: {st.session_state.zotero_status}")
    
    # Configuration section
    with st.expander("⚙️ Zotero Configuration", expanded=(st.session_state.zotero_status == "not_configured")):
        show_zotero_config(config, zotero_status)
    
    # Collections interface (only if connected)
    if st.session_state.zotero_status == "connected":
        show_collections_interface()

def show_zotero_config(config, status):
    """Show Zotero configuration interface"""
    st.markdown("**Required Settings:**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("🔑 **API Key:**")
        if status.get('zotero_api_key'):
            st.success("✅ Configured")
        else:
            st.error("❌ Missing")
            
        st.markdown("📚 **Library ID:**")
        if status.get('zotero_library_id'):
            st.success(f"✅ {config.zotero_library_id}")
        else:
            st.error("❌ Missing")
    
    with col2:
        st.markdown("🏛️ **Library Type:**")
        st.info(f"📋 {config.zotero_library_type}")
        
        st.markdown("🔄 **Sync Status:**")
        if status.get('zotero_configured'):
            st.success("✅ Ready")
        else:
            st.error("❌ Not configured")
    
    if not status.get('zotero_configured'):
        st.markdown("**To configure Zotero, add to your .env file:**")
        st.code("""
# Get these from https://www.zotero.org/settings/keys
ZOTERO_API_KEY=your-api-key-here
ZOTERO_LIBRARY_ID=your-library-id-here
ZOTERO_LIBRARY_TYPE=user
        """)
    
    # Test connection button
    if st.button("🔍 Test Zotero Connection"):
        test_zotero_connection()

def test_zotero_connection():
    """Test Zotero connection"""
    if not st.session_state.zotero_manager:
        st.error("❌ Zotero manager not initialized")
        return
    
    with st.spinner("Testing connection..."):
        try:
            connection_info = st.session_state.zotero_manager.test_connection()
            
            if connection_info.get('connected'):
                st.success("✅ Connection successful!")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Items", connection_info.get('total_items', 0))
                with col2:
                    st.metric("Sample Items", connection_info.get('sample_items', 0))
                
                # Reload collections
                load_zotero_collections()
                st.rerun()
            else:
                st.error(f"❌ Connection failed: {connection_info.get('error')}")
                
        except Exception as e:
            st.error(f"❌ Connection test failed: {e}")

def show_collections_interface():
    """Show Zotero collections interface"""
    st.subheader("📁 Zotero Collections")
    
    collections = st.session_state.zotero_collections
    
    if not collections:
        if st.button("🔄 Reload Collections"):
            load_zotero_collections()
            st.rerun()
        st.info("📭 No collections found")
        return
    
    # Collections display
    st.markdown(f"**Found {len(collections)} collections:**")
    
    # Collection selection
    collection_options = {}
    for coll in collections:
        name = coll['name']
        items = coll.get('num_items', 0)
        collection_options[f"{name} ({items} items)"] = coll['key']
    
    selected_display = st.multiselect(
        "Select collections for knowledge base:",
        options=list(collection_options.keys()),
        help="Choose one or more collections to sync"
    )
    
    # Store selected collection keys
    st.session_state.selected_collections = [
        collection_options[display_name] for display_name in selected_display
    ]
    
    if st.session_state.selected_collections:
        show_collection_preview()

def show_collection_preview():
    """Show preview of selected collections"""
    st.subheader("🔍 Collection Preview")
    
    selected_keys = st.session_state.selected_collections
    
    for collection_key in selected_keys:
        collection = next((c for c in st.session_state.zotero_collections if c['key'] == collection_key), None)
        if not collection:
            continue
        
        with st.expander(f"📁 {collection['name']} ({collection.get('num_items', 0)} items)"):
            preview_collection_details(collection_key, collection['name'])

def preview_collection_details(collection_key, collection_name):
    """Show detailed preview of a collection"""
    
    # Basic analysis first
    with st.spinner(f"Analyzing {collection_name}..."):
        try:
            items = st.session_state.zotero_manager.get_collection_items_direct(collection_key)
            
            st.markdown(f"**Collection:** {collection_name}")
            st.markdown(f"**Key:** {collection_key}")
            st.markdown(f"**Items found:** {len(items)}")
            
            if items:
                # Show sample items
                st.markdown("**📚 Sample items:**")
                for i, item in enumerate(items[:3], 1):
                    st.markdown(f"{i}. {item.title[:80]}...")
                    if item.doi:
                        st.markdown(f"   🔗 DOI: {item.doi}")
                    
                    # Check for attachments
                    attachments = st.session_state.zotero_manager.get_item_attachments(item.key)
                    pdf_attachments = [att for att in attachments if att.content_type == 'application/pdf']
                    if pdf_attachments:
                        st.markdown(f"   📄 Has {len(pdf_attachments)} PDF(s)")
                    else:
                        st.markdown(f"   📄 No PDFs")
                
                if len(items) > 3:
                    st.markdown(f"... and {len(items) - 3} more items")
                
                # Analysis summary
                items_with_pdfs = 0
                items_with_dois = 0
                items_without_dois = 0
                
                for item in items:
                    attachments = st.session_state.zotero_manager.get_item_attachments(item.key)
                    pdf_attachments = [att for att in attachments if att.content_type == 'application/pdf']
                    
                    if pdf_attachments:
                        items_with_pdfs += 1
                    elif item.doi and item.doi.strip():
                        items_with_dois += 1
                    else:
                        items_without_dois += 1
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📄 Items with PDFs", items_with_pdfs)
                with col2:
                    st.metric("🔗 DOI Download Candidates", items_with_dois)
                with col3:
                    st.metric("❓ Items without DOIs", items_without_dois)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"📥 Test Sync", key=f"test_sync_{collection_key}"):
                        test_zotero_sync(collection_key, collection_name)
                
                with col2:
                    if st.button(f"🚀 Quick DOI Download", key=f"quick_doi_{collection_key}"):
                        quick_doi_download(collection_key, collection_name)
                
                with col3:
                    if st.button(f"📂 Check Files", key=f"check_files_{collection_key}"):
                        check_zotero_files()
            
            else:
                st.warning("📭 No items found in this collection")
        
        except Exception as e:
            st.error(f"❌ Analysis failed: {e}")
            with st.expander("🔍 Debug Details"):
                st.text(f"Collection key: {collection_key}")
                st.text(f"Collection name: {collection_name}")
                st.text(f"Error: {str(e)}")

def test_zotero_sync(collection_key, collection_name):
    """Test basic Zotero sync functionality"""
    with st.spinner(f"Testing sync for {collection_name}..."):
        try:
            # Test basic sync
            sync_result = st.session_state.zotero_manager.sync_library(
                download_attachments=True,
                file_types={'application/pdf'},
                collections=[collection_key],
                overwrite_files=False
            )
            
            st.success(f"✅ Sync test completed!")
            st.info(f"📊 Processed {sync_result.items_processed} items, downloaded {sync_result.files_downloaded} files")
            
            # Check what files were actually created
            pdf_folder = st.session_state.zotero_manager.pdf_directory
            if pdf_folder.exists():
                pdf_files = list(pdf_folder.glob("*.pdf"))
                st.info(f"📄 Found {len(pdf_files)} PDF files in {pdf_folder}")
                
                if pdf_files:
                    st.markdown("**Downloaded files:**")
                    for pdf_file in pdf_files[:5]:  # Show first 5
                        size_mb = pdf_file.stat().st_size / (1024 * 1024)
                        st.markdown(f"• {pdf_file.name} ({size_mb:.2f} MB)")
            else:
                st.warning(f"📁 PDF folder does not exist: {pdf_folder}")
        
        except Exception as e:
            st.error(f"❌ Sync test failed: {e}")

def quick_doi_download(collection_key, collection_name):
    """Test DOI download functionality"""
    with st.spinner(f"Testing DOI downloads for {collection_name}..."):
        try:
            if hasattr(st.session_state.zotero_manager, 'sync_collection_with_doi_downloads_fast'):
                result = st.session_state.zotero_manager.sync_collection_with_doi_downloads_fast(
                    collection_key,
                    max_doi_downloads=2,  # Just test with 2
                    headless=True
                )
                
                st.success(f"✅ DOI download test completed!")
                st.info(f"📥 Downloaded {result.successful_doi_downloads} PDFs, failed {result.failed_doi_downloads}")
                
                if result.downloaded_files:
                    st.markdown("**Downloaded files:**")
                    for file_path in result.downloaded_files:
                        st.markdown(f"• {Path(file_path).name}")
            else:
                st.warning("⚠️ Enhanced DOI download not available")
        
        except Exception as e:
            st.error(f"❌ DOI download test failed: {e}")

def check_zotero_files():
    """Check what files exist in Zotero folders"""
    config = st.session_state.config
    zotero_manager = st.session_state.zotero_manager
    
    st.markdown("**📂 Zotero File System Check:**")
    
    # Check main Zotero folder
    zotero_folder = config.zotero_sync_folder
    st.markdown(f"**Main Zotero folder:** `{zotero_folder}`")
    if zotero_folder.exists():
        st.success("✅ Exists")
        files = list(zotero_folder.rglob("*"))
        st.info(f"📁 Contains {len(files)} total files/folders")
    else:
        st.error("❌ Does not exist")
    
    # Check PDF folder
    pdf_folder = zotero_manager.pdf_directory
    st.markdown(f"**PDF folder:** `{pdf_folder}`")
    if pdf_folder.exists():
        pdf_files = list(pdf_folder.glob("*.pdf"))
        st.success(f"✅ Exists with {len(pdf_files)} PDF files")
        
        if pdf_files:
            for pdf_file in pdf_files[:3]:  # Show first 3
                size_mb = pdf_file.stat().st_size / (1024 * 1024)
                st.markdown(f"   • {pdf_file.name} ({size_mb:.2f} MB)")
    else:
        st.error("❌ Does not exist")
    
    # Check DOI downloads folder (if available)
    if hasattr(zotero_manager, 'doi_downloads_folder'):
        doi_folder = zotero_manager.doi_downloads_folder
        st.markdown(f"**DOI downloads folder:** `{doi_folder}`")
        if doi_folder.exists():
            doi_files = list(doi_folder.glob("*.pdf"))
            st.success(f"✅ Exists with {len(doi_files)} PDF files")
        else:
            st.error("❌ Does not exist")
    
    # Check knowledge bases folder
    kb_folder = config.knowledge_bases_folder
    st.markdown(f"**Knowledge bases folder:** `{kb_folder}`")
    if kb_folder.exists():
        kb_dirs = [d for d in kb_folder.iterdir() if d.is_dir()]
        st.success(f"✅ Exists with {len(kb_dirs)} knowledge bases")
        
        for kb_dir in kb_dirs:
            files = list(kb_dir.glob("*"))
            st.markdown(f"   📚 {kb_dir.name}: {len(files)} files")
    else:
        st.error("❌ Does not exist")

def analyze_collection(collection_key, collection_name):
    """Analyze a single collection"""
    with st.spinner(f"Analyzing {collection_name}..."):
        try:
            # Get basic collection info
            items = st.session_state.zotero_manager.get_collection_items_direct(collection_key)
            
            st.success(f"✅ Found {len(items)} items in {collection_name}")
            
            # Show sample items
            if items:
                st.markdown("**Sample items:**")
                for item in items[:3]:
                    st.markdown(f"• {item.title[:80]}...")
        
        except Exception as e:
            st.error(f"❌ Analysis failed: {e}")

def sync_single_collection(collection_key, collection_name):
    """Sync a single collection with DOI downloads"""
    with st.spinner(f"Syncing {collection_name} with DOI downloads..."):
        try:
            # Check if we have enhanced syncer
            if hasattr(st.session_state.zotero_manager, 'sync_collection_with_doi_downloads_fast'):
                result = st.session_state.zotero_manager.sync_collection_with_doi_downloads_fast(
                    collection_key,
                    max_doi_downloads=5,  # Limit for demo
                    headless=True
                )
                
                st.success(f"✅ Sync completed for {collection_name}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("📚 Total Items", result.total_items)
                with col2:
                    st.metric("📥 Downloaded", result.successful_doi_downloads)
                with col3:
                    st.metric("❌ Failed", result.failed_doi_downloads)
                
                if result.downloaded_files:
                    st.markdown("**📄 Downloaded files:**")
                    for file_path in result.downloaded_files:
                        st.markdown(f"• {Path(file_path).name}")
            else:
                st.warning("⚠️ Enhanced sync not available. Use basic collection sync.")
        
        except Exception as e:
            st.error(f"❌ Sync failed: {e}")

# ============================================================================
# Enhanced Knowledge Base Management
# ============================================================================
def enhanced_kb_interface():
    """Enhanced knowledge base interface with Zotero integration"""
    st.subheader("📚 Knowledge Base Management")
    
    # Existing KB management (unchanged)
    config = st.session_state.config
    available_kbs_info = list_knowledge_bases(config.knowledge_bases_folder)
    
    if available_kbs_info and isinstance(available_kbs_info[0], dict):
        available_kbs = [kb['name'] for kb in available_kbs_info]
    else:
        available_kbs = available_kbs_info or []
    
    # Load existing KB section
    if available_kbs:
        st.markdown("**📖 Load Existing Knowledge Base:**")
        selected_kb = st.selectbox("Choose knowledge base:", available_kbs)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📖 Load Knowledge Base", type="primary"):
                load_selected_kb(selected_kb)
        with col2:
            if st.button("📊 View Stats"):
                show_kb_stats(selected_kb)
    
    # Create KB from Zotero section
    if st.session_state.zotero_status == "connected":
        create_kb_from_zotero_interface()
    
    # Create KB from folders section
    with st.expander("🆕 Create Knowledge Base from Local Folders"):
        create_kb_from_folders_interface()

def create_kb_from_zotero_interface():
    """Interface for creating KB from Zotero collections"""
    st.markdown("**🚀 Create Knowledge Base from Zotero Collections:**")
    
    if not st.session_state.zotero_collections:
        st.info("📭 No Zotero collections loaded")
        if st.button("🔄 Load Collections"):
            load_zotero_collections()
            st.rerun()
        return
    
    # KB name input
    kb_name = st.text_input(
        "Knowledge Base Name:", 
        placeholder="physics_zotero_kb",
        help="Name for the new knowledge base"
    )
    
    # Collection selection
    collection_options = {}
    for coll in st.session_state.zotero_collections:
        name = coll['name']
        items = coll.get('num_items', 0)
        collection_options[f"{name} ({items} items)"] = coll['key']
    
    selected_collections = st.multiselect(
        "Select Zotero collections:",
        options=list(collection_options.keys()),
        help="Choose collections to include in the knowledge base"
    )
    
    # DOI download options
    st.markdown("**📥 DOI Download Options:**")
    enable_doi_downloads = st.checkbox("Enable DOI-based PDF downloads", value=True)
    max_doi_downloads = st.slider("Max DOI downloads per collection", 1, 50, 10)
    
    # PDF integration options
    if enable_doi_downloads:
        st.markdown("**📎 PDF Integration:**")
        integration_mode = st.selectbox(
            "PDF integration mode:",
            ["attach", "download_only"],
            help="attach: Add PDFs to existing Zotero records, download_only: Keep locally"
        )
    
    # Create KB button
    if st.button("🏗️ Create Knowledge Base from Zotero", type="primary"):
        if kb_name and selected_collections:
            collection_keys = [collection_options[name] for name in selected_collections]
            create_kb_from_zotero(
                kb_name, 
                collection_keys, 
                enable_doi_downloads, 
                max_doi_downloads,
                integration_mode if enable_doi_downloads else None
            )
        else:
            st.error("Please enter a KB name and select at least one collection")

def create_kb_from_zotero(kb_name, collection_keys, enable_doi, max_downloads, integration_mode):
    """Create knowledge base from Zotero collections"""
    config = st.session_state.config
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Step 1: Create empty knowledge base
        status_text.text("🏗️ Creating knowledge base...")
        progress_bar.progress(10)
        
        kb = create_knowledge_base(kb_name, config.knowledge_bases_folder)
        
        total_synced = 0
        total_downloaded = 0
        total_documents_added = 0
        errors = []
        
        # Step 2: Process each collection
        for i, collection_key in enumerate(collection_keys):
            collection = next((c for c in st.session_state.zotero_collections 
                             if c['key'] == collection_key), None)
            
            if not collection:
                errors.append(f"Collection {collection_key} not found")
                continue
            
            collection_name = collection['name']
            progress = 20 + (i * 60 // len(collection_keys))
            progress_bar.progress(progress)
            status_text.text(f"📁 Processing collection: {collection_name}")
            
            # First, try to sync existing attachments from Zotero
            try:
                # Basic sync to get existing PDFs
                sync_result = st.session_state.zotero_manager.sync_library(
                    download_attachments=True,
                    file_types={'application/pdf'},
                    collections=[collection_key],
                    overwrite_files=False
                )
                
                total_synced += sync_result.items_processed
                
                # Add existing PDFs to knowledge base
                zotero_pdf_folder = st.session_state.zotero_manager.pdf_directory
                if zotero_pdf_folder.exists():
                    for pdf_file in zotero_pdf_folder.glob("*.pdf"):
                        try:
                            success = kb.add_document(pdf_file, f"zotero_{collection_name}")
                            if success:
                                total_documents_added += 1
                        except Exception as e:
                            errors.append(f"Failed to add {pdf_file.name}: {e}")
                
                st.info(f"✅ Processed {sync_result.items_processed} items from {collection_name}")
                
            except Exception as e:
                errors.append(f"Failed to sync existing attachments from {collection_name}: {e}")
            
            # Optional: DOI downloads for items without PDFs
            if enable_doi:
                try:
                    status_text.text(f"📥 Downloading PDFs via DOI for {collection_name}...")
                    
                    # Use basic DOI download sync
                    doi_result = st.session_state.zotero_manager.sync_collection_with_doi_downloads_fast(
                        collection_key,
                        max_doi_downloads=max_downloads,
                        headless=True
                    )
                    
                    total_downloaded += doi_result.successful_doi_downloads
                    
                    # Add newly downloaded PDFs to knowledge base
                    doi_folder = st.session_state.zotero_manager.doi_downloads_folder
                    if doi_folder.exists():
                        for pdf_file in doi_folder.glob("*.pdf"):
                            try:
                                success = kb.add_document(pdf_file, f"zotero_doi_{collection_name}")
                                if success:
                                    total_documents_added += 1
                            except Exception as e:
                                errors.append(f"Failed to add DOI download {pdf_file.name}: {e}")
                    
                    st.info(f"📥 Downloaded {doi_result.successful_doi_downloads} new PDFs for {collection_name}")
                    
                except Exception as e:
                    errors.append(f"DOI downloads failed for {collection_name}: {e}")
        
        # Step 3: Build the knowledge base from all added documents
        progress_bar.progress(80)
        status_text.text("🧠 Building knowledge base embeddings...")
        
        # Force rebuild the knowledge base to process all documents
        kb_stats = kb.get_statistics()
        if total_documents_added > 0:
            st.info(f"🧠 Processing {total_documents_added} documents into knowledge base...")
        else:
            st.warning("⚠️ No PDF documents were found or successfully processed")
        
        # Step 4: Display results
        progress_bar.progress(100)
        status_text.text("✅ Knowledge base creation complete!")
        
        if total_documents_added > 0:
            st.success(f"✅ Knowledge base '{kb_name}' created successfully!")
        else:
            st.warning(f"⚠️ Knowledge base '{kb_name}' created but no documents were processed")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📚 Items Synced", total_synced)
        with col2:
            st.metric("📥 PDFs Downloaded", total_downloaded)
        with col3:
            st.metric("📄 Documents Added", total_documents_added)
        with col4:
            st.metric("❌ Errors", len(errors))
        
        # Show knowledge base stats
        final_stats = kb.get_statistics()
        if final_stats.get('total_documents', 0) > 0:
            st.info(f"📊 Final KB stats: {final_stats['total_documents']} documents, {final_stats['total_chunks']} chunks")
        
        if errors:
            with st.expander("⚠️ View Errors"):
                for error in errors:
                    st.text(error)
        
        # Set as current KB
        st.session_state.current_kb = kb
        st.session_state.current_kb_name = kb_name
        
        # Initialize chat if possible and KB has content
        if CHAT_AVAILABLE and config.anthropic_api_key:
            st.session_state.assistant = LiteratureAssistant(
                kb, config.anthropic_api_key, config.get_chat_config()
            )
            st.session_state.chat_ready = True
            
            if final_stats.get('total_documents', 0) > 0:
                st.success("💬 Chat assistant is ready! You can now ask questions about your literature.")
            else:
                st.warning("💬 Chat assistant initialized but knowledge base is empty. Add some PDFs first.")
        
        time.sleep(2)  # Let user see the completion message
        progress_bar.empty()
        status_text.empty()
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Failed to create knowledge base: {e}")
        st.error(f"🔍 Debug info: {str(e)}")
        
        # Show some debug information
        with st.expander("🔍 Debug Information"):
            st.text(f"KB name: {kb_name}")
            st.text(f"Collection keys: {collection_keys}")
            st.text(f"Config path: {config.knowledge_bases_folder}")
            st.text(f"Zotero manager type: {type(st.session_state.zotero_manager)}")
            
            # Check if folders exist
            st.text(f"Zotero PDF folder exists: {st.session_state.zotero_manager.pdf_directory.exists()}")
            if hasattr(st.session_state.zotero_manager, 'doi_downloads_folder'):
                st.text(f"DOI downloads folder exists: {st.session_state.zotero_manager.doi_downloads_folder.exists()}")
            
            # List available methods
            zotero_methods = [method for method in dir(st.session_state.zotero_manager) if not method.startswith('_')]
            st.text(f"Available Zotero methods: {', '.join(zotero_methods[:10])}...")  # Show first 10

def create_kb_from_folders_interface():
    """Interface for creating KB from local folders (existing functionality)"""
    new_kb_name = st.text_input("Knowledge Base Name:", placeholder="my_research_kb")
    
    st.markdown("**Select source folders:**")
    include_literature = st.checkbox("📚 Literature folder", value=True)
    include_your_work = st.checkbox("📝 Your work folder", value=True)
    include_drafts = st.checkbox("✏️ Current drafts", value=False)
    include_manual = st.checkbox("📂 Manual references", value=True)
    
    if st.button("🏗️ Create Knowledge Base"):
        if new_kb_name:
            create_new_kb_from_folders(new_kb_name, include_literature, include_your_work, include_drafts, include_manual)
        else:
            st.error("Please enter a name for the knowledge base")

def create_new_kb_from_folders(name, lit, work, drafts, manual):
    """Create knowledge base from local folders (existing functionality)"""
    config = st.session_state.config
    
    with st.spinner(f"Creating knowledge base '{name}'..."):
        try:
            kb = create_knowledge_base(name, config.knowledge_bases_folder)
            
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
                st.warning("⚠️ No source folders found with documents")
                return
            
            stats = kb.build_from_directories(**folders, force_rebuild=True)
            
            st.success(f"✅ Created '{name}' with {stats['total_documents']} documents")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to create knowledge base: {e}")

# ============================================================================
# Utility functions (load_selected_kb, show_kb_stats remain the same)
# ============================================================================
def load_selected_kb(kb_name):
    """Load a selected knowledge base"""
    config = st.session_state.config
    
    with st.spinner(f"Loading {kb_name}..."):
        try:
            kb = load_knowledge_base(kb_name, config.knowledge_bases_folder)
            if kb:
                st.session_state.current_kb = kb
                st.session_state.current_kb_name = kb_name
                
                # Initialize chat assistant if possible
                if CHAT_AVAILABLE and config.anthropic_api_key:
                    st.session_state.assistant = LiteratureAssistant(
                        kb, config.anthropic_api_key, config.get_chat_config()
                    )
                    st.session_state.chat_ready = True
                
                st.success(f"✅ Loaded knowledge base: {kb_name}")
                st.rerun()
            else:
                st.error(f"❌ Failed to load knowledge base: {kb_name}")
                
        except Exception as e:
            st.error(f"❌ Error loading knowledge base: {e}")

def show_kb_stats(kb_name):
    """Show knowledge base statistics"""
    config = st.session_state.config
    
    try:
        kb = load_knowledge_base(kb_name, config.knowledge_bases_folder)
        
        if kb:
            stats = kb.get_statistics()
            
            st.markdown(f"**📊 Statistics for {kb_name}:**")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Documents", stats.get('total_documents', 0))
            with col2:
                st.metric("Chunks", stats.get('total_chunks', 0))
            with col3:
                st.metric("Words", f"{stats.get('total_words', 0):,}")
            with col4:
                st.metric("Size (MB)", f"{stats.get('total_size_mb', 0):.1f}")
        else:
            st.error(f"Failed to load knowledge base: {kb_name}")
            
    except Exception as e:
        st.error(f"Error loading KB stats: {e}")

# ============================================================================
# Chat Interface (unchanged)
# ============================================================================
def chat_interface():
    """Main chat interface"""
    st.header("💬 Chat with Your Literature")
    
    # Check prerequisites
    if not st.session_state.current_kb:
        st.warning("📚 Please load a knowledge base first in the Knowledge Base tab.")
        return
    
    if not CHAT_AVAILABLE:
        st.error("❌ Chat functionality not available. Check your imports.")
        return
    
    config = st.session_state.config
    if not config.anthropic_api_key:
        st.error("🔑 ANTHROPIC_API_KEY required. Add it to your .env file:")
        st.code("ANTHROPIC_API_KEY=your-api-key-here")
        return
    
    # Chat settings in sidebar
    with st.sidebar:
        st.markdown("### ⚙️ Chat Settings")
        st.session_state.chat_temperature = st.slider("🌡️ Creativity", 0.0, 1.0, st.session_state.chat_temperature, 0.1)
        st.session_state.chat_max_sources = st.slider("📄 Max Sources", 1, 20, st.session_state.chat_max_sources)
        
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()
    
    # Display current KB
    st.info(f"📚 Using knowledge base: **{st.session_state.get('current_kb_name', 'Unknown')}**")
    
    # Chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    st.caption(f"📚 Sources: {', '.join(message['sources'][:3])}{'...' if len(message['sources']) > 3 else ''}")
    
    # Chat input
    if prompt := st.chat_input("Ask about your research..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = st.session_state.assistant.ask(
                        prompt,
                        temperature=st.session_state.chat_temperature,
                        max_context_chunks=st.session_state.chat_max_sources
                    )
                    
                    st.write(response.content)
                    if response.sources_used:
                        st.caption(f"📚 Sources: {', '.join(response.sources_used[:3])}{'...' if len(response.sources_used) > 3 else ''}")
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response.content,
                        "sources": response.sources_used
                    })
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# ============================================================================
# File Management Interface (unchanged)
# ============================================================================
def file_management_interface():
    """Simple file management interface"""
    st.header("📁 File Management")
    
    config = st.session_state.config
    
    # File upload
    st.subheader("📤 Upload Files")
    
    target_folder = st.selectbox(
        "Upload to folder:",
        ["literature", "your_work", "current_drafts", "manual_references"]
    )
    
    uploaded_files = st.file_uploader(
        "Choose files",
        type=['pdf', 'tex', 'txt'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        target_path = getattr(config, f"{target_folder}_folder")
        
        for file in uploaded_files:
            file_path = target_path / file.name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        
        st.success(f"✅ Uploaded {len(uploaded_files)} files to {target_folder}")
    
    # Show folder contents
    st.subheader("📂 Folder Contents")
    
    folder_to_show = st.selectbox(
        "Show folder:",
        ["literature", "your_work", "current_drafts", "manual_references"]
    )
    
    show_folder_contents(folder_to_show)

def show_folder_contents(folder_name):
    """Show contents of a folder"""
    config = st.session_state.config
    folder_path = getattr(config, f"{folder_name}_folder")
    
    if folder_path.exists():
        files = list(folder_path.glob("*"))
        if files:
            file_data = []
            for file in files:
                size_mb = file.stat().st_size / (1024 * 1024)
                file_data.append({
                    "File": file.name,
                    "Type": file.suffix.upper(),
                    "Size (MB)": f"{size_mb:.2f}"
                })
            
            df = pd.DataFrame(file_data)
            st.dataframe(df, use_container_width=True)
            st.info(f"📊 Total: {len(files)} files")
        else:
            st.info(f"📭 No files in {folder_name} folder")
    else:
        st.warning(f"📁 {folder_name} folder does not exist")

# ============================================================================
# Zotero Status Dashboard
# ============================================================================
def zotero_status_dashboard():
    """Show Zotero status in sidebar"""
    with st.sidebar:
        st.markdown("### 📚 Zotero Status")
        
        if st.session_state.zotero_status == "connected":
            st.success("✅ Connected")
            
            # Show collections count
            if st.session_state.zotero_collections:
                st.info(f"📁 {len(st.session_state.zotero_collections)} collections")
            
            # Quick actions
            if st.button("🔄 Refresh Collections", help="Reload Zotero collections"):
                load_zotero_collections()
                st.rerun()
        
        elif st.session_state.zotero_status == "not_configured":
            st.warning("⚙️ Not configured")
            st.markdown("Configure in Zotero tab")
        
        else:
            st.error("❌ Error")
            if st.button("🔄 Retry Connection"):
                initialize_system()
                st.rerun()

# ============================================================================
# Enhanced Status Display
# ============================================================================
def show_system_status():
    """Show comprehensive system status"""
    config = st.session_state.config
    
    with st.expander("🔍 System Status", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📚 Knowledge Bases:**")
            available_kbs = list_knowledge_bases(config.knowledge_bases_folder)
            st.info(f"Available: {len(available_kbs)}")
            
            if st.session_state.current_kb:
                st.success(f"Active: {st.session_state.get('current_kb_name', 'Unknown')}")
            else:
                st.warning("No KB loaded")
        
        with col2:
            st.markdown("**🔑 API Keys:**")
            api_status = config.check_env_file()
            
            # Anthropic
            if api_status.get('anthropic_api_key'):
                st.success("✅ Anthropic")
            else:
                st.error("❌ Anthropic")
            
            # Zotero
            if api_status.get('zotero_configured'):
                st.success("✅ Zotero")
            else:
                st.warning("⚠️ Zotero")
        
        # Capabilities summary
        st.markdown("**🚀 Available Features:**")
        capabilities = []
        
        if CHAT_AVAILABLE and config.anthropic_api_key:
            capabilities.append("💬 Chat Assistant")
        
        if ZOTERO_AVAILABLE and api_status.get('zotero_configured'):
            capabilities.append("📚 Zotero Integration")
            capabilities.append("📥 DOI Downloads")
        
        capabilities.append("📁 File Management")
        capabilities.append("🏗️ Knowledge Base Creation")
        
        for cap in capabilities:
            st.markdown(f"• {cap}")

# ============================================================================
# Main Application
# ============================================================================
def main():
    """Main application with enhanced Zotero integration"""
    # Initialize
    init_session_state()
    initialize_system()
    
    if not st.session_state.system_initialized:
        st.stop()
    
    # Header
    st.title("🔬 Physics Research Assistant")
    st.markdown("**AI-powered literature management with Zotero integration**")
    
    # System status
    show_system_status()
    
    # Sidebar with Zotero status
    zotero_status_dashboard()
    
    # Main tabs - now including Zotero integration
    if ZOTERO_AVAILABLE:
        tab1, tab2, tab3, tab4 = st.tabs([
            "📚 Knowledge Bases", 
            "🔗 Zotero Integration", 
            "📁 Files", 
            "💬 Chat"
        ])
        
        with tab1:
            enhanced_kb_interface()
        
        with tab2:
            zotero_integration_interface()
        
        with tab3:
            file_management_interface()
        
        with tab4:
            chat_interface()
    
    else:
        # Fallback to original tabs if Zotero not available
        tab1, tab2, tab3 = st.tabs(["📚 Knowledge Bases", "📁 Files", "💬 Chat"])
        
        with tab1:
            enhanced_kb_interface()
        
        with tab2:
            file_management_interface()
        
        with tab3:
            chat_interface()
        
        # Show Zotero installation help
        with st.sidebar:
            st.markdown("### 📚 Zotero Integration")
            st.warning("⚠️ Not available")
            st.markdown("Install dependencies:")
            st.code("pip install pyzotero selenium")

# ============================================================================
# Quick Start Guide
# ============================================================================
def show_quick_start():
    """Show quick start guide for new users"""
    if st.session_state.get('show_quick_start', True):
        with st.container():
            st.markdown("### 🚀 Quick Start Guide")
            
            steps_completed = []
            
            # Step 1: Configuration
            config = st.session_state.config
            api_status = config.check_env_file()
            
            if api_status.get('anthropic_api_key'):
                steps_completed.append("✅ Step 1: Anthropic API configured")
            else:
                st.warning("⏸️ Step 1: Configure Anthropic API key in .env file")
            
            # Step 2: Zotero (optional)
            if api_status.get('zotero_configured'):
                steps_completed.append("✅ Step 2: Zotero configured")
            else:
                st.info("💡 Step 2: Configure Zotero for automatic literature management (optional)")
            
            # Step 3: Knowledge Base
            if st.session_state.current_kb:
                steps_completed.append("✅ Step 3: Knowledge base loaded")
            else:
                st.info("📚 Step 3: Create or load a knowledge base")
            
            # Step 4: Chat
            if st.session_state.chat_ready:
                steps_completed.append("✅ Step 4: Chat assistant ready")
                st.success("🎉 All set! You can now chat with your literature.")
            
            # Show completed steps
            if steps_completed:
                for step in steps_completed:
                    st.markdown(step)
            
            # Hide guide button
            if len(steps_completed) >= 3:
                if st.button("✖ Hide Quick Start Guide"):
                    st.session_state.show_quick_start = False
                    st.rerun()

if __name__ == "__main__":
    main()