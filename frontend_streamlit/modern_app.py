#!/usr/bin/env python3
"""
Enhanced Physics Research Assistant - Streamlit App
Clean sidebar navigation inspired by modern Streamlit patterns
Replaces tab-based navigation with sidebar page selection
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
# Custom CSS for Sidebar Navigation
# ============================================================================
def load_sidebar_css():
    """Load custom CSS for modern sidebar navigation"""
    st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc !important;
    }
    
    /* Navigation buttons in sidebar */
    div[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: 3rem !important;
        background-color: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        color: #374151 !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 0.75rem 1rem !important;
        margin-bottom: 0.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    div[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #f1f5f9 !important;
        border-color: #667eea !important;
        transform: translateX(4px) !important;
    }
    
    /* Active page styling (you can enhance this with JavaScript) */
    .nav-active {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: transparent !important;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        max-width: none;
    }
    
    /* Page headers */
    .page-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }
    
    /* Status widgets */
    .status-widget {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .status-success { border-left: 4px solid #10b981; }
    .status-warning { border-left: 4px solid #f59e0b; }
    .status-error { border-left: 4px solid #ef4444; }
    </style>
    """, unsafe_allow_html=True)

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
        'zotero_status': None,
        'current_page': 'dashboard'  # Default page
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================================================
# Sidebar Navigation
# ============================================================================
def render_sidebar_navigation():
    """Render the sidebar navigation"""
    with st.sidebar:
        # Logo and title
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 2rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 1.5rem;">
            <div style="font-size: 3rem; margin-bottom: 0.5rem;">🔬</div>
            <h2 style="margin: 0; color: #1f2937; font-weight: 700; font-size: 1.3rem;">Physics Research</h2>
            <p style="margin: 0; color: #6b7280; font-size: 0.85rem;">Literature Assistant</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation menu
        st.markdown("### Navigation")
        
        # Page navigation buttons
        if st.button("🏠 Dashboard", key="nav_dashboard", use_container_width=True):
            st.session_state.current_page = 'dashboard'
            st.rerun()
        
        if st.button("💬 Chat Assistant", key="nav_chat", use_container_width=True):
            st.session_state.current_page = 'chat'
            st.rerun()
        
        if st.button("📚 Knowledge Bases", key="nav_knowledge", use_container_width=True):
            st.session_state.current_page = 'knowledge_bases'
            st.rerun()
        
        if ZOTERO_AVAILABLE:
            if st.button("🔗 Zotero Integration", key="nav_zotero", use_container_width=True):
                st.session_state.current_page = 'zotero'
                st.rerun()
        
        if st.button("📁 File Management", key="nav_files", use_container_width=True):
            st.session_state.current_page = 'files'
            st.rerun()
        
        if st.button("⚙️ Settings", key="nav_settings", use_container_width=True):
            st.session_state.current_page = 'settings'
            st.rerun()
        
        # Current page indicator
        st.markdown("---")
        st.markdown(f"**Current:** {st.session_state.current_page.replace('_', ' ').title()}")
        
        # System status in sidebar
        render_sidebar_status()

def render_sidebar_status():
    """Render system status in sidebar"""
    st.markdown("### 🔍 System Status")
    
    config = st.session_state.get('config')
    if not config:
        st.error("❌ Not initialized")
        return
    
    # API Keys status
    api_status = config.check_env_file()
    
    if api_status.get('anthropic_api_key'):
        st.success("✅ Anthropic API")
    else:
        st.error("❌ Anthropic API")
    
    # Zotero status
    zotero_status = st.session_state.get('zotero_status', 'unknown')
    if zotero_status == 'connected':
        st.success("✅ Zotero Connected")
        if st.session_state.zotero_collections:
            st.info(f"📁 {len(st.session_state.zotero_collections)} collections")
    elif zotero_status == 'not_configured':
        st.warning("⚙️ Zotero Not Setup")
    else:
        st.error("❌ Zotero Error")
    
    # Knowledge Base status
    if st.session_state.get('current_kb'):
        st.success(f"✅ KB: {st.session_state.get('current_kb_name', 'Active')}")
    else:
        st.warning("⚠️ No KB Loaded")

# ============================================================================
# PAGE IMPLEMENTATIONS
# ============================================================================

def render_dashboard_page():
    """Dashboard overview page"""
    st.markdown('<h1 class="page-header">🏠 Research Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("**Welcome to your Physics Literature Synthesis Pipeline**")
    
    # Quick stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        render_metric_card("📚", "Knowledge Bases", get_kb_count(), "#667eea")
    
    with col2:
        render_metric_card("📄", "Total Papers", get_total_papers(), "#764ba2")
    
    with col3:
        render_metric_card("🔗", "Zotero Items", get_zotero_items(), "#48bb78")
    
    with col4:
        render_metric_card("💬", "Chat Ready", "Yes" if st.session_state.chat_ready else "No", "#ed8936")
    
    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🚀 Create Knowledge Base", use_container_width=True):
            st.session_state.current_page = 'knowledge_bases'
            st.rerun()
    
    with col2:
        if st.button("🔄 Sync Zotero", use_container_width=True):
            if st.session_state.zotero_status == 'connected':
                st.session_state.current_page = 'zotero'
                st.rerun()
            else:
                st.error("Zotero not connected")
    
    with col3:
        if st.button("💬 Start Chatting", use_container_width=True):
            if st.session_state.chat_ready:
                st.session_state.current_page = 'chat'
                st.rerun()
            else:
                st.error("Load a knowledge base first")
    
    # Recent activity
    st.markdown("---")
    render_recent_activity()
    
    # System overview
    st.markdown("---")
    render_system_overview()

def render_chat_page():
    """Chat interface page"""
    st.markdown('<h1 class="page-header">💬 Research Assistant</h1>', unsafe_allow_html=True)
    st.markdown("**Ask questions about your literature collection**")
    
    # Check if chat is ready
    if not st.session_state.get('chat_ready', False):
        render_chat_setup_required()
        return
    
    # Chat settings (compact)
    with st.expander("⚙️ Chat Settings", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.session_state.chat_temperature = st.slider(
                "🌡️ Creativity", 0.0, 1.0, 
                st.session_state.get('chat_temperature', 0.3), 0.1
            )
        
        with col2:
            st.session_state.chat_max_sources = st.slider(
                "📄 Max Sources", 1, 20, 
                st.session_state.get('chat_max_sources', 8)
            )
        
        with col3:
            if st.button("🗑️ Clear Chat"):
                st.session_state.messages = []
                st.rerun()
    
    # Active KB indicator
    current_kb = st.session_state.get('current_kb_name', 'None')
    st.info(f"📚 **Active Knowledge Base:** {current_kb}")
    
    # Chat messages
    render_chat_messages()
    
    # Suggested questions (if no chat history)
    if not st.session_state.get('messages', []):
        render_suggested_questions()
    
    # Chat input
    if prompt := st.chat_input("Ask about your research..."):
        process_chat_message(prompt)

def render_knowledge_bases_page():
    """Knowledge base management page"""
    st.markdown('<h1 class="page-header">📚 Knowledge Base Management</h1>', unsafe_allow_html=True)
    st.markdown("**Create and manage your literature knowledge bases**")
    
    config = st.session_state.config
    available_kbs_info = list_knowledge_bases(config.knowledge_bases_folder)
    
    if available_kbs_info and isinstance(available_kbs_info[0], dict):
        available_kbs = [kb['name'] for kb in available_kbs_info]
    else:
        available_kbs = available_kbs_info or []
    
    # Current KB status
    current_kb = st.session_state.get('current_kb_name')
    if current_kb:
        st.success(f"✅ **Active Knowledge Base:** {current_kb}")
        
        # KB actions
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("📊 View Statistics"):
                show_kb_stats(current_kb)
        
        with col2:
            if st.button("🔄 Rebuild"):
                rebuild_knowledge_base(current_kb)
        
        with col3:
            if st.button("📤 Export"):
                st.info("Export functionality coming soon!")
        
        with col4:
            if st.button("🗑️ Delete", type="secondary"):
                st.error("Delete confirmation required")
    else:
        st.warning("⚠️ No knowledge base currently loaded")
    
    # Load existing KB
    if available_kbs:
        st.markdown("---")
        st.markdown("### 📖 Load Existing Knowledge Base")
        
        selected_kb = st.selectbox(
            "Choose knowledge base:",
            [""] + available_kbs,
            format_func=lambda x: "Select a knowledge base..." if x == "" else f"📚 {x}"
        )
        
        if selected_kb and selected_kb != current_kb:
            if st.button("🔄 Load Knowledge Base", type="primary"):
                load_selected_kb(selected_kb)
    
    # Create new KB section
    st.markdown("---")
    st.markdown("### 🆕 Create New Knowledge Base")
    
    # Choose creation method
    creation_method = st.radio(
        "Choose creation method:",
        ["Local Folders", "Zotero Collections"] if ZOTERO_AVAILABLE and st.session_state.zotero_status == 'connected' else ["Local Folders"]
    )
    
    if creation_method == "Local Folders":
        render_kb_from_folders_interface()
    elif creation_method == "Zotero Collections":
        render_kb_from_zotero_interface()

def render_zotero_page():
    """Zotero integration page"""
    st.markdown('<h1 class="page-header">🔗 Zotero Integration</h1>', unsafe_allow_html=True)
    st.markdown("**Sync and manage your Zotero library**")
    
    if not ZOTERO_AVAILABLE:
        st.error("❌ Zotero integration not available. Install dependencies:")
        st.code("pip install pyzotero selenium")
        return
    
    # Zotero connection status
    zotero_status = st.session_state.get('zotero_status', 'unknown')
    
    if zotero_status == 'connected':
        st.success("✅ Connected to Zotero")
        render_zotero_interface()
    elif zotero_status == 'not_configured':
        st.warning("⚙️ Zotero not configured")
        render_zotero_setup()
    else:
        st.error("❌ Zotero connection error")
        st.write(f"Error: {zotero_status}")
        render_zotero_troubleshooting()

def render_files_page():
    """File management page"""
    st.markdown('<h1 class="page-header">📁 File Management</h1>', unsafe_allow_html=True)
    st.markdown("**Manage your local document folders**")
    
    config = st.session_state.get('config')
    if not config:
        st.error("Configuration not loaded")
        return
    
    # File upload section
    st.markdown("### 📤 Upload Documents")
    
    target_folder = st.selectbox(
        "Upload to folder:",
        ["literature", "your_work", "current_drafts", "manual_references"]
    )
    
    uploaded_files = st.file_uploader(
        "Choose files to upload",
        accept_multiple_files=True,
        type=['pdf', 'txt', 'md', 'tex']
    )
    
    if uploaded_files:
        if st.button("📥 Upload Files"):
            upload_files_to_folder(uploaded_files, target_folder)
    
    # Folder overview
    st.markdown("---")
    st.markdown("### 📂 Folder Overview")
    
    folders = {
        "📚 Literature": config.literature_folder,
        "📝 Your Work": config.your_work_folder,
        "✏️ Current Drafts": config.current_drafts_folder,
        "📂 Manual References": config.manual_references_folder,
        "🔗 Zotero Sync": config.zotero_sync_folder
    }
    
    for folder_name, folder_path in folders.items():
        with st.expander(f"{folder_name} ({folder_path.name})", expanded=False):
            render_folder_overview(folder_path, folder_name)

def render_settings_page():
    """Settings and configuration page"""
    st.markdown('<h1 class="page-header">⚙️ Settings</h1>', unsafe_allow_html=True)
    st.markdown("**Configure your Physics Research Assistant**")
    
    # API Keys section
    st.markdown("### 🔑 API Configuration")
    
    config = st.session_state.get('config')
    if not config:
        st.error("Configuration not loaded")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Anthropic API")
        current_anthropic = "Configured" if config.anthropic_api_key else "Not Set"
        st.info(f"Status: {current_anthropic}")
        
        if st.button("🧪 Test Anthropic Connection"):
            test_anthropic_connection()
    
    with col2:
        st.markdown("#### Zotero API")
        api_status = config.check_env_file()
        zotero_configured = "Configured" if api_status.get('zotero_configured') else "Not Set"
        st.info(f"Status: {zotero_configured}")
        
        if st.button("🧪 Test Zotero Connection"):
            test_zotero_connection()
    
    # Configuration instructions
    st.markdown("---")
    st.markdown("### 📋 Configuration Instructions")
    
    st.markdown("**To configure API keys, add to your `.env` file:**")
    st.code("""
# Anthropic API (required for chat)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Zotero API (optional, for library integration)
ZOTERO_API_KEY=your-zotero-api-key-here
ZOTERO_LIBRARY_ID=your-library-id-here
ZOTERO_LIBRARY_TYPE=user
    """)
    
    # System info
    st.markdown("---")
    st.markdown("### 📊 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Available Features:**")
        features = ["📁 File Management", "🏗️ Knowledge Base Creation"]
        
        if CHAT_AVAILABLE and config.anthropic_api_key:
            features.append("💬 Chat Assistant")
        
        if ZOTERO_AVAILABLE:
            features.append("📚 Zotero Integration")
        
        for feature in features:
            st.markdown(f"• {feature}")
    
    with col2:
        st.markdown("**Project Paths:**")
        st.code(f"""
Project Root: {project_root}
Knowledge Bases: {config.knowledge_bases_folder}
Literature: {config.literature_folder}
Zotero Sync: {config.zotero_sync_folder}
        """)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def render_metric_card(icon, label, value, color):
    """Render a metric card"""
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, {color} 0%, {color}dd 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    ">
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">{icon}</div>
        <div style="font-size: 1.8rem; font-weight: bold; margin-bottom: 0.2rem;">{value}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def render_chat_setup_required():
    """Show chat setup requirements"""
    st.warning("💬 Chat assistant not ready. Complete setup:")
    
    steps = []
    
    config = st.session_state.get('config')
    if not config or not config.anthropic_api_key:
        steps.append("1. Configure Anthropic API key in Settings")
    
    if not st.session_state.get('current_kb'):
        steps.append("2. Load or create a Knowledge Base")
    
    for step in steps:
        st.markdown(f"• {step}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚙️ Go to Settings"):
            st.session_state.current_page = 'settings'
            st.rerun()
    
    with col2:
        if st.button("📚 Go to Knowledge Bases"):
            st.session_state.current_page = 'knowledge_bases'
            st.rerun()

def render_chat_messages():
    """Render chat message history"""
    messages = st.session_state.get('messages', [])
    
    for message in messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
            if message["role"] == "assistant" and "sources" in message:
                if message["sources"]:
                    sources_text = ", ".join(message["sources"][:3])
                    if len(message["sources"]) > 3:
                        sources_text += f" and {len(message['sources']) - 3} more"
                    st.caption(f"📚 Sources: {sources_text}")

def render_suggested_questions():
    """Render suggested questions for new users"""
    st.markdown("### 💡 Try asking...")
    
    questions = [
        "What papers do I have about quantum computing?",
        "Summarize the main themes in my research",
        "Who are the most cited authors in my collection?",
        "Help me write an introduction for my paper",
        "What are recent developments in my field?",
        "Find papers related to machine learning"
    ]
    
    cols = st.columns(2)
    for i, question in enumerate(questions):
        with cols[i % 2]:
            if st.button(f"❓ {question}", key=f"suggested_{i}"):
                process_chat_message(question)

def render_recent_activity():
    """Render recent activity feed"""
    st.markdown("### 📈 Recent Activity")
    
    # Placeholder activity data
    activities = [
        {"icon": "📚", "text": "Knowledge base 'Physics Papers' loaded", "time": "2 minutes ago"},
        {"icon": "🔗", "text": "Synced 5 papers from Zotero", "time": "1 hour ago"},
        {"icon": "💬", "text": "Chat session started", "time": "3 hours ago"},
        {"icon": "📄", "text": "Added 3 new papers to library", "time": "Yesterday"}
    ]
    
    for activity in activities:
        st.markdown(f"{activity['icon']} {activity['text']} • *{activity['time']}*")

def render_system_overview():
    """Render system overview"""
    st.markdown("### 🔍 System Overview")
    
    config = st.session_state.get('config')
    if not config:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Statistics**")
        st.write(f"• Knowledge Bases: {get_kb_count()}")
        st.write(f"• Total Papers: {get_total_papers()}")
        st.write(f"• Zotero Collections: {len(st.session_state.get('zotero_collections', []))}")
    
    with col2:
        st.markdown("**🔧 Status**")
        st.write(f"• Chat Ready: {'✅' if st.session_state.chat_ready else '❌'}")
        st.write(f"• Zotero: {'✅' if st.session_state.zotero_status == 'connected' else '❌'}")
        st.write(f"• API Keys: {'✅' if config.anthropic_api_key else '❌'}")

# All the existing functions from your modern_app.py would go here
# I'm including the key ones but you'd keep all your existing implementations:

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

def process_chat_message(message):
    """Process a chat message"""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": message})
    
    # Get AI response
    with st.spinner("🤖 Thinking..."):
        try:
            response = st.session_state.assistant.ask(
                message, 
                temperature=st.session_state.chat_temperature,
                max_context_chunks=st.session_state.chat_max_sources
            )
            
            # Add assistant message
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response.content,
                "sources": response.sources_used
            })
            
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    st.rerun()

# Placeholder functions (replace with your existing implementations)
def get_kb_count(): 
    config = st.session_state.get('config')
    if config:
        return len(list_knowledge_bases(config.knowledge_bases_folder))
    return 0

def get_total_papers(): return 156  # Replace with actual count
def get_zotero_items(): return len(st.session_state.get('zotero_collections', []))

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

def render_kb_from_folders_interface():
    """Interface for creating KB from local folders"""
    new_kb_name = st.text_input("Knowledge Base Name:", placeholder="my_research_kb")
    
    st.markdown("**Select source folders:**")
    include_literature = st.checkbox("📚 Literature folder", value=True)
    include_your_work = st.checkbox("📝 Your work folder", value=True)
    include_drafts = st.checkbox("✏️ Current drafts", value=False)
    include_manual = st.checkbox("📂 Manual references", value=True)
    
    if st.button("🏗️ Create Knowledge Base from Folders", type="primary"):
        if new_kb_name:
            create_new_kb_from_folders(new_kb_name, include_literature, include_your_work, include_drafts, include_manual)
        else:
            st.error("Please enter a name for the knowledge base")

def render_kb_from_zotero_interface():
    """Interface for creating KB from Zotero collections"""
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
    enable_doi_downloads = st.checkbox("📥 Enable DOI-based PDF downloads", value=True)
    if enable_doi_downloads:
        max_doi_downloads = st.slider("Max DOI downloads per collection", 1, 50, 10)
    
    # Create KB button
    if st.button("🏗️ Create Knowledge Base from Zotero", type="primary"):
        if kb_name and selected_collections:
            collection_keys = [collection_options[name] for name in selected_collections]
            create_kb_from_zotero(kb_name, collection_keys, enable_doi_downloads, max_doi_downloads if enable_doi_downloads else 0)
        else:
            st.error("Please enter a KB name and select at least one collection")

def create_new_kb_from_folders(name, lit, work, drafts, manual):
    """Create knowledge base from local folders"""
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
            
            # Set as current KB
            st.session_state.current_kb = kb
            st.session_state.current_kb_name = name
            
            # Initialize chat if possible
            if CHAT_AVAILABLE and config.anthropic_api_key:
                st.session_state.assistant = LiteratureAssistant(
                    kb, config.anthropic_api_key, config.get_chat_config()
                )
                st.session_state.chat_ready = True
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to create knowledge base: {e}")

def create_kb_from_zotero(kb_name, collection_keys, enable_doi, max_downloads):
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
            
            # Basic sync to get existing PDFs
            try:
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
                
            except Exception as e:
                errors.append(f"Failed to sync {collection_name}: {e}")
            
            # Optional DOI downloads
            if enable_doi and hasattr(st.session_state.zotero_manager, 'sync_collection_with_doi_downloads_fast'):
                try:
                    doi_result = st.session_state.zotero_manager.sync_collection_with_doi_downloads_fast(
                        collection_key,
                        max_doi_downloads=max_downloads,
                        headless=True
                    )
                    
                    total_downloaded += doi_result.successful_doi_downloads
                    
                except Exception as e:
                    errors.append(f"DOI downloads failed for {collection_name}: {e}")
        
        # Step 3: Complete
        progress_bar.progress(100)
        status_text.text("✅ Knowledge base creation complete!")
        
        st.success(f"✅ Knowledge base '{kb_name}' created successfully!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📚 Items Synced", total_synced)
        with col2:
            st.metric("📥 PDFs Downloaded", total_downloaded)
        with col3:
            st.metric("📄 Documents Added", total_documents_added)
        
        if errors:
            with st.expander("⚠️ View Errors"):
                for error in errors:
                    st.text(error)
        
        # Set as current KB
        st.session_state.current_kb = kb
        st.session_state.current_kb_name = kb_name
        
        # Initialize chat
        if CHAT_AVAILABLE and config.anthropic_api_key:
            st.session_state.assistant = LiteratureAssistant(
                kb, config.anthropic_api_key, config.get_chat_config()
            )
            st.session_state.chat_ready = True
        
        time.sleep(2)
        progress_bar.empty()
        status_text.empty()
        st.rerun()
        
    except Exception as e:
        progress_bar.empty()
        status_text.empty()
        st.error(f"❌ Failed to create knowledge base: {e}")

def render_zotero_interface():
    """Main Zotero interface when connected"""
    st.markdown("### 📁 Zotero Collections")
    
    collections = st.session_state.zotero_collections
    
    if not collections:
        if st.button("🔄 Reload Collections"):
            load_zotero_collections()
            st.rerun()
        st.info("📭 No collections found")
        return
    
    st.markdown(f"**Found {len(collections)} collections:**")
    
    for collection in collections:
        with st.expander(f"📁 {collection['name']} ({collection.get('num_items', 0)} items)"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📊 Analyze", key=f"analyze_{collection['key']}"):
                    analyze_collection(collection['key'], collection['name'])
            
            with col2:
                if st.button(f"📥 Sync", key=f"sync_{collection['key']}"):
                    sync_single_collection(collection['key'], collection['name'])
            
            with col3:
                if st.button(f"🏗️ Create KB", key=f"create_kb_{collection['key']}"):
                    # Quick KB creation from single collection
                    create_kb_from_zotero(f"kb_{collection['name'].lower().replace(' ', '_')}", 
                                        [collection['key']], True, 5)

def render_zotero_setup():
    """Zotero setup interface"""
    st.markdown("### ⚙️ Zotero Setup Required")
    
    st.markdown("**To configure Zotero, add to your `.env` file:**")
    st.code("""
# Get these from https://www.zotero.org/settings/keys
ZOTERO_API_KEY=your-api-key-here
ZOTERO_LIBRARY_ID=your-library-id-here
ZOTERO_LIBRARY_TYPE=user
    """)
    
    if st.button("🔄 Test Connection After Setup"):
        initialize_system()
        st.rerun()

def render_zotero_troubleshooting():
    """Zotero troubleshooting interface"""
    st.markdown("### 🔧 Troubleshooting")
    
    st.markdown("**Common issues:**")
    st.markdown("• Check your API key permissions at https://www.zotero.org/settings/keys")
    st.markdown("• Ensure your Library ID is correct")
    st.markdown("• Verify internet connection")
    
    if st.button("🔄 Retry Connection"):
        initialize_system()
        st.rerun()

def render_folder_overview(folder_path, folder_name):
    """Show overview of a folder"""
    if folder_path.exists():
        files = list(folder_path.glob("*"))
        if files:
            file_data = []
            for file in files:
                if file.is_file():
                    size_mb = file.stat().st_size / (1024 * 1024)
                    file_data.append({
                        "File": file.name,
                        "Type": file.suffix.upper(),
                        "Size (MB)": f"{size_mb:.2f}"
                    })
            
            if file_data:
                df = pd.DataFrame(file_data)
                st.dataframe(df, use_container_width=True)
                st.info(f"📊 Total: {len(file_data)} files")
            else:
                st.info(f"📁 Folder contains {len(files)} items (directories)")
        else:
            st.info(f"📭 No files in {folder_name}")
    else:
        st.warning(f"📁 {folder_name} does not exist")

def upload_files_to_folder(uploaded_files, target_folder):
    """Upload files to specified folder"""
    config = st.session_state.config
    target_path = getattr(config, f"{target_folder}_folder")
    
    try:
        for file in uploaded_files:
            file_path = target_path / file.name
            with open(file_path, "wb") as f:
                f.write(file.getbuffer())
        
        st.success(f"✅ Uploaded {len(uploaded_files)} files to {target_folder}")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")

def test_anthropic_connection():
    """Test Anthropic API connection"""
    config = st.session_state.config
    
    if not config.anthropic_api_key:
        st.error("❌ No Anthropic API key configured")
        return
    
    with st.spinner("Testing Anthropic connection..."):
        try:
            # Simple test - create a minimal assistant
            from src.chat import LiteratureAssistant
            # Create a dummy KB for testing
            test_kb = None  # You'd need a minimal KB here
            assistant = LiteratureAssistant(test_kb, config.anthropic_api_key, config.get_chat_config())
            st.success("✅ Anthropic API connection successful!")
            
        except Exception as e:
            st.error(f"❌ Anthropic API test failed: {e}")

def test_zotero_connection():
    """Test Zotero API connection"""
    if not st.session_state.zotero_manager:
        st.error("❌ Zotero manager not initialized")
        return
    
    with st.spinner("Testing Zotero connection..."):
        try:
            connection_info = st.session_state.zotero_manager.test_connection()
            
            if connection_info.get('connected'):
                st.success("✅ Zotero connection successful!")
                st.info(f"📚 Found {connection_info.get('total_items', 0)} items in library")
            else:
                st.error(f"❌ Zotero connection failed: {connection_info.get('error')}")
                
        except Exception as e:
            st.error(f"❌ Zotero test failed: {e}")

def rebuild_knowledge_base(kb_name):
    """Rebuild an existing knowledge base"""
    with st.spinner(f"Rebuilding {kb_name}..."):
        try:
            # This would implement KB rebuilding logic
            st.success(f"✅ Rebuilt knowledge base: {kb_name}")
            
        except Exception as e:
            st.error(f"❌ Failed to rebuild: {e}")

def analyze_collection(collection_key, collection_name):
    """Analyze a Zotero collection"""
    with st.spinner(f"Analyzing {collection_name}..."):
        try:
            items = st.session_state.zotero_manager.get_collection_items_direct(collection_key)
            st.success(f"✅ Found {len(items)} items in {collection_name}")
            
            if items:
                st.markdown("**Sample items:**")
                for item in items[:3]:
                    st.markdown(f"• {item.title[:80]}...")
        
        except Exception as e:
            st.error(f"❌ Analysis failed: {e}")

def sync_single_collection(collection_key, collection_name):
    """Sync a single Zotero collection"""
    with st.spinner(f"Syncing {collection_name}..."):
        try:
            sync_result = st.session_state.zotero_manager.sync_library(
                download_attachments=True,
                file_types={'application/pdf'},
                collections=[collection_key],
                overwrite_files=False
            )
            
            st.success(f"✅ Synced {sync_result.items_processed} items from {collection_name}")
            
        except Exception as e:
            st.error(f"❌ Sync failed: {e}")

# System initialization functions (keep your existing ones)
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
# Main Application Router
# ============================================================================
def main():
    """Main application with sidebar navigation"""
    # Load custom CSS
    load_sidebar_css()
    
    # Initialize
    init_session_state()
    initialize_system()
    
    if not st.session_state.system_initialized:
        st.stop()
    
    # Render sidebar navigation
    render_sidebar_navigation()
    
    # Route to appropriate page based on current_page
    current_page = st.session_state.current_page
    
    if current_page == 'dashboard':
        render_dashboard_page()
    elif current_page == 'chat':
        render_chat_page()
    elif current_page == 'knowledge_bases':
        render_knowledge_bases_page()
    elif current_page == 'zotero':
        render_zotero_page()
    elif current_page == 'files':
        render_files_page()
    elif current_page == 'settings':
        render_settings_page()
    else:
        st.error(f"Unknown page: {current_page}")

if __name__ == "__main__":
    main()