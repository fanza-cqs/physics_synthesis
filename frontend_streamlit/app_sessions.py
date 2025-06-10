# frontend_streamlit/app_sessions.py
"""
Physics Literature Synthesis Pipeline - Session-Based Streamlit App
Complete redesign with ChatGPT/Claude-style session management and sidebar navigation
"""

import streamlit as st
import sys
import os
from pathlib import Path
import time

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
    from src.sessions import SessionManager
    SESSIONS_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Sessions module import failed: {e}")
    st.stop()

try:
    from src.ui import Sidebar, ChatInterface, ChatState, KBManagement, render_all_css
    UI_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ UI components import failed: {e}")
    st.stop()

try:
    from src.chat import LiteratureAssistant
    CHAT_AVAILABLE = True
except ImportError as e:
    st.warning(f"⚠️ Chat module not available: {e}")
    CHAT_AVAILABLE = False

try:
    from src.downloaders import (
        create_zotero_manager,
        get_zotero_capabilities
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

# Load all component CSS
render_all_css()

# ============================================================================
# Global CSS for App Layout
# ============================================================================
def render_global_css():
    """Render global CSS for the application"""
    st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {visibility: hidden;}
    
    /* Main app layout */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: none;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* Main content area */
    .main-content {
        background: white;
        min-height: 100vh;
        padding: 2rem;
    }
    
    /* Management overlay styling */
    .management-overlay {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 2rem;
        box-shadow: 0 25px 50px rgba(0,0,0,0.15);
        max-width: 90vw;
        max-height: 90vh;
        overflow-y: auto;
        z-index: 1000;
    }
    
    .overlay-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0,0,0,0.5);
        z-index: 999;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-content {
            padding: 1rem;
        }
        
        .management-overlay {
            padding: 1rem;
            max-width: 95vw;
        }
    }
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
        'session_manager': None,
        'zotero_manager': None,
        'zotero_collections': [],
        'zotero_status': None,
        'zotero_available': ZOTERO_AVAILABLE,
        'chat_available': CHAT_AVAILABLE,
        
        # UI state
        'show_kb_management': False,
        'show_zotero_management': False,
        'show_settings': False,
        
        # Chat settings
        'chat_temperature': 0.3,
        'chat_max_sources': 8
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    
    # Initialize chat state
    ChatState.initialize()

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
            
            # Initialize session manager
            session_manager = SessionManager(project_root)
            st.session_state.session_manager = session_manager
            
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
# Management Overlays
# ============================================================================
def render_management_overlays():
    """Render management overlays when requested"""
    session_manager = st.session_state.session_manager
    
    # Knowledge Base Management
    if st.session_state.get('show_kb_management', False):
        with st.container():
            kb_management = KBManagement(session_manager)
            kb_management.render_overlay()
    
    # Zotero Management (placeholder)
    if st.session_state.get('show_zotero_management', False):
        with st.container():
            render_zotero_management_overlay()
    
    # Settings (placeholder)
    if st.session_state.get('show_settings', False):
        with st.container():
            render_settings_overlay()

def render_zotero_management_overlay():
    """Render Zotero management overlay"""
    st.markdown("## 🔗 Zotero Integration")
    
    # Close button
    if st.button("✖️ Close", key="close_zotero_management"):
        st.session_state.show_zotero_management = False
        st.rerun()
    
    st.markdown("---")
    
    zotero_status = st.session_state.get('zotero_status', 'unknown')
    
    if zotero_status == 'connected':
        st.success("✅ Connected to Zotero")
        
        # Show collections
        collections = st.session_state.get('zotero_collections', [])
        if collections:
            st.markdown(f"**Found {len(collections)} collections:**")
            for collection in collections[:10]:  # Show first 10
                st.markdown(f"• **{collection['name']}** ({collection.get('num_items', 0)} items)")
        else:
            st.info("📭 No collections found")
        
        if st.button("🔄 Reload Collections"):
            load_zotero_collections()
            st.rerun()
    
    elif zotero_status == 'not_configured':
        st.warning("⚙️ Zotero not configured")
        st.markdown("**To configure Zotero, add to your `.env` file:**")
        st.code("""
# Get these from https://www.zotero.org/settings/keys
ZOTERO_API_KEY=your-api-key-here
ZOTERO_LIBRARY_ID=your-library-id-here
ZOTERO_LIBRARY_TYPE=user
        """)
    else:
        st.error(f"❌ Zotero error: {zotero_status}")

def render_settings_overlay():
    """Render settings overlay"""
    st.markdown("## ⚙️ Settings")
    
    # Close button
    if st.button("✖️ Close", key="close_settings"):
        st.session_state.show_settings = False
        st.rerun()
    
    st.markdown("---")
    
    config = st.session_state.get('config')
    if not config:
        st.error("Configuration not loaded")
        return
    
    # API Keys section
    st.markdown("### 🔑 API Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Anthropic API")
        anthropic_status = "✅ Configured" if config.anthropic_api_key else "❌ Not Set"
        st.info(f"Status: {anthropic_status}")
        
        if st.button("🧪 Test Anthropic", key="test_anthropic"):
            test_anthropic_connection()
    
    with col2:
        st.markdown("#### Zotero API")
        api_status = config.check_env_file()
        zotero_status = "✅ Configured" if api_status.get('zotero_configured') else "❌ Not Set"
        st.info(f"Status: {zotero_status}")
        
        if st.button("🧪 Test Zotero", key="test_zotero"):
            test_zotero_connection()
    
    # Configuration instructions
    st.markdown("---")
    st.markdown("### 📋 Configuration Instructions")
    
    st.markdown("**Add to your `.env` file:**")
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
        features = ["📁 File Management", "🏗️ Knowledge Base Creation", "💬 Session Management"]
        
        if CHAT_AVAILABLE and config.anthropic_api_key:
            features.append("🤖 AI Chat Assistant")
        
        if ZOTERO_AVAILABLE:
            features.append("📚 Zotero Integration")
        
        for feature in features:
            st.markdown(f"• {feature}")
    
    with col2:
        st.markdown("**Storage Info:**")
        if st.session_state.session_manager:
            stats = st.session_state.session_manager.get_storage_stats()
            st.markdown(f"• Sessions: {stats['total_sessions']}")
            st.markdown(f"• Documents: {stats['total_documents']}")
            st.markdown(f"• Storage: {stats['total_size_mb']:.1f} MB")

def test_anthropic_connection():
    """Test Anthropic API connection"""
    config = st.session_state.config
    if not config.anthropic_api_key:
        st.error("❌ No Anthropic API key configured")
        return
    
    with st.spinner("Testing Anthropic connection..."):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            
            # Simple test call
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}]
            )
            
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

# ============================================================================
# Main Application
# ============================================================================
def main():
    """Main application with session-based architecture"""
    # Render global CSS
    render_global_css()
    
    # Initialize
    init_session_state()
    initialize_system()
    
    if not st.session_state.system_initialized:
        st.stop()
    
    # Get session manager
    session_manager = st.session_state.session_manager
    
    # Render sidebar
    sidebar = Sidebar(session_manager)
    sidebar.render()
    
    # Main content area
    with st.container():
        # Check if any management overlays should be shown
        if (st.session_state.get('show_kb_management', False) or 
            st.session_state.get('show_zotero_management', False) or 
            st.session_state.get('show_settings', False)):
            
            # Render overlay backdrop
            st.markdown('<div class="overlay-backdrop"></div>', unsafe_allow_html=True)
            
            # Render management overlays
            render_management_overlays()
        
        else:
            # Normal chat interface
            chat_interface = ChatInterface(session_manager)
            chat_interface.render()

if __name__ == "__main__":
    main()