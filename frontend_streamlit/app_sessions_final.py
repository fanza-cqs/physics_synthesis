# frontend_streamlit/app_sessions_final.py
"""
Physics Literature Synthesis Pipeline - Final Session-Based Application
Complete integration of session system with enhanced UI components
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
    from src.sessions.session_integration import init_session_integration, get_session_integration
    SESSIONS_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Sessions module import failed: {e}")
    st.stop()

try:
    from src.ui.enhanced_sidebar import EnhancedSidebar, render_enhanced_sidebar_css
    from src.ui.enhanced_chat_interface import EnhancedChatInterface, render_enhanced_chat_css
    from src.ui.kb_management import KBManagement, render_kb_management_css
    UI_AVAILABLE = True
except ImportError as e:
    st.error(f"❌ Enhanced UI components import failed: {e}")
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

# ============================================================================
# Global CSS and Styling
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
    
    /* Global app styling */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: none;
    }
    
    /* Enhanced main content area */
    .main-content {
        background: white;
        min-height: 100vh;
        padding: 2rem;
        border-radius: 0;
    }
    
    
    /* Enhanced typography */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #1f2937;
        font-weight: 700;
    }
    
    .stMarkdown h1 {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-clip: text;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Enhanced buttons globally */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.3s ease;
        border: 1px solid #e2e8f0;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Enhanced success/error messages */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border: 1px solid #10b981;
        color: #065f46;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stError {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border: 1px solid #ef4444;
        color: #991b1b;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border: 1px solid #f59e0b;
        color: #92400e;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border: 1px solid #3b82f6;
        color: #1e40af;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .main-content {
            padding: 1rem;
        }
        
        .management-overlay {
            padding: 1rem;
            max-width: 95vw;
            max-height: 95vh;
        }
    }
    </style>
    """, unsafe_allow_html=True)

def render_all_enhanced_css():
    """Render all enhanced CSS components"""
    render_global_css()
    render_enhanced_sidebar_css()
    render_enhanced_chat_css()
    render_kb_management_css()

# ============================================================================
# Session State Initialization
# ============================================================================
def init_app_session_state():
    """Initialize application session state"""
    defaults = {
        'system_initialized': False,
        'config': None,
        'session_manager': None,
        'session_integration': None,
        'zotero_manager': None,
        'zotero_collections': [],
        'zotero_status': None,
        'zotero_available': ZOTERO_AVAILABLE,
        'chat_available': CHAT_AVAILABLE,
        
        # SIMPLE PAGE NAVIGATION - Replace overlay state
        'current_page': 'chat',  # 'chat', 'knowledge_bases', 'zotero', 'settings'
        
        # Session state
        'current_session_id': None,
        'current_session_name': None,
        'current_kb_name': None,
        
        # Auto-save tracking
        'last_session_save': 0,
        
        # UI feedback
        'show_success_message': None,
        'show_error_message': None,
        'show_info_message': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================================================
# System Initialization
# ============================================================================
def initialize_system():
    """Initialize all system components with proper error handling and ordering"""
    try:
        if st.session_state.system_initialized:
            return True
        
        # Initialize config
        with st.spinner("🔧 Loading configuration..."):
            config = PipelineConfig()
            st.session_state.config = config
        
        # Initialize session manager FIRST (before session integration)
        with st.spinner("📂 Initializing session system..."):
            session_manager = SessionManager(project_root)
            st.session_state.session_manager = session_manager
            
            # Ensure we have a current session
            if not session_manager.current_session:
                existing_sessions = session_manager.list_sessions()
                if existing_sessions:
                    # Load the most recent session
                    most_recent_id = existing_sessions[0]['id']
                    session_manager.switch_to_session(most_recent_id)
                else:
                    # Create new default session
                    session_manager.create_session("New Session", auto_activate=True)
        
        # NOW initialize session integration (after session_manager is in state)
        with st.spinner("🔗 Setting up session integration..."):
            try:
                #print(f"🔍 DEBUG: About to create session integration")
                #print(f"🔍 DEBUG: session_manager = {session_manager}")
                #print(f"🔍 DEBUG: st.session_state keys before: {list(st.session_state.keys())}")
        
                # Don't use init_session_integration() - do it manually here
                from src.sessions.session_integration import SessionIntegration
                
                # FIXED: Always create new integration (don't check if it exists)
                #print(f"🔍 DEBUG: Creating new SessionIntegration")
                st.session_state.session_integration = SessionIntegration(session_manager)
                #print(f"🔍 DEBUG: Created session_integration: {st.session_state.session_integration}")
        

                #if 'session_integration' not in st.session_state:
                #    print(f"🔍 DEBUG: Creating new SessionIntegration")
                #    st.session_state.session_integration = SessionIntegration(session_manager)
                #    print(f"🔍 DEBUG: Created session_integration: {st.session_state.session_integration}")
        
                
                # Sync current session to Streamlit state
                integration = st.session_state.session_integration
                #print(f"🔍 DEBUG: Got integration from session_state: {integration}")

                current_session = integration.ensure_current_session()
                #print(f"🔍 DEBUG: ensure_current_session returned: {current_session}")

                integration.sync_session_to_streamlit(current_session)
                #print(f"🔍 DEBUG: Session integration setup complete")
                
            except Exception as e:
                #print(f"🔍 DEBUG: Session integration failed with error: {e}")
                import traceback
                traceback.print_exc()
                st.error(f"❌ Session integration failed: {e}")
                # Continue without session integration for now
                st.session_state.session_integration = None
        
        # Initialize other components
        if ZOTERO_AVAILABLE:
            with st.spinner("📚 Setting up Zotero integration..."):
                try:
                    zotero_manager = create_zotero_manager(config)
                    st.session_state.zotero_manager = zotero_manager
                    st.session_state.zotero_status = "✅ Connected"
                except Exception as e:
                    st.session_state.zotero_manager = None
                    st.session_state.zotero_status = f"❌ Failed: {e}"
        
        # Test chat availability
        if CHAT_AVAILABLE:
            with st.spinner("🤖 Testing chat system..."):
                try:
                    # Simple test - try to create a LiteratureAssistant
                    test_assistant = LiteratureAssistant(config, None)
                    st.session_state.chat_available = True
                    st.session_state.chat_status = "✅ Ready"
                except Exception as e:
                    st.session_state.chat_available = False
                    st.session_state.chat_status = f"❌ Failed: {e}"
        
        st.session_state.system_initialized = True
        st.success("🎉 System initialized successfully!")
        return True
        
    except Exception as e:
        st.error(f"❌ System initialization failed: {e}")
        print(f"System initialization error: {e}")
        return False

def get_session_integration_safe():
    """Get session integration with better error handling"""
    if 'session_integration' not in st.session_state:
        session_manager = st.session_state.get('session_manager')
        if not session_manager:
            st.error("❌ Session system not properly initialized. Please refresh the page.")
            st.stop()
        
        from src.sessions.session_integration import SessionIntegration
        st.session_state.session_integration = SessionIntegration(session_manager)
    
    return st.session_state.session_integration



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
# Page Navigation System
# ============================================================================
def render_main_content_area(session_manager):
    """Render main content area based on current page"""
    current_page = st.session_state.get('current_page', 'chat')
    
    if current_page == 'chat':
        # Render chat interface
        chat_interface = EnhancedChatInterface(session_manager)
        chat_interface.render()
        
    elif current_page == 'knowledge_bases':
        # Render Knowledge Base management page
        render_knowledge_bases_page(session_manager)
        
    elif current_page == 'zotero':
        # Render Zotero management page  
        render_zotero_page()
        
    elif current_page == 'settings':
        # Render settings page
        render_settings_page()
        
    else:
        # Fallback to chat
        st.session_state.current_page = 'chat'
        st.rerun()


def render_knowledge_bases_page(session_manager):
    """Render the Knowledge Bases management page"""
    st.markdown("# 📚 Knowledge Base Management")
    
    # Back to chat button
    if st.button("← Back to Chat", key="back_to_chat_from_kb"):
        st.session_state.current_page = 'chat'
        st.rerun()
    
    st.markdown("---")
    
    # Use the existing KB management component but render as full page
    kb_management = KBManagement(session_manager)
    kb_management._render_kb_interface()  # Call the internal interface method directly


def render_zotero_page():
    """Render the Zotero management page"""
    st.markdown("# 🔗 Zotero Integration")
    
    # Back to chat button
    if st.button("← Back to Chat", key="back_to_chat_from_zotero"):
        st.session_state.current_page = 'chat'
        st.rerun()
    
    st.markdown("---")
    
    # Use existing Zotero management logic but as full page
    zotero_status = st.session_state.get('zotero_status', 'unknown')
    
    if zotero_status == 'connected':
        st.success("✅ Connected to Zotero")
        
        # Show collections
        collections = st.session_state.get('zotero_collections', [])
        if collections:
            st.markdown(f"**Found {len(collections)} collections:**")
            
            # Display collections in a nice format
            for collection in collections[:15]:  # Show first 15
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"📁 **{collection['name']}**")
                with col2:
                    st.caption(f"{collection.get('num_items', 0)} items")
        else:
            st.info("📭 No collections found")
        
        # Actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Reload Collections", use_container_width=True):
                load_zotero_collections()
                st.rerun()
        
        with col2:
            if st.button("🧪 Test Connection", use_container_width=True):
                test_zotero_connection()
    
    elif zotero_status == 'not_configured':
        st.warning("⚙️ Zotero not configured")
        st.markdown("**To configure Zotero, add to your `.env` file:**")
        st.code("""
# Get these from https://www.zotero.org/settings/keys
ZOTERO_API_KEY=your-api-key-here
ZOTERO_LIBRARY_ID=your-library-id-here
ZOTERO_LIBRARY_TYPE=user
        """)
        
        if st.button("🔄 Retry After Configuration"):
            initialize_system()
            st.rerun()
    else:
        st.error(f"❌ Zotero error: {zotero_status}")
        
        if st.button("🔄 Retry Connection"):
            initialize_system()
            st.rerun()


def render_settings_page():
    """Render the Settings page"""
    st.markdown("# ⚙️ Settings")
    
    # Back to chat button
    if st.button("← Back to Chat", key="back_to_chat_from_settings"):
        st.session_state.current_page = 'chat'
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
        zotero_status_text = "✅ Configured" if api_status.get('zotero_configured') else "❌ Not Set"
        st.info(f"Status: {zotero_status_text}")
        
        if st.button("🧪 Test Zotero", key="test_zotero"):
            test_zotero_connection()
    
    # Configuration instructions
    st.markdown("### 📖 Configuration Instructions")
    st.markdown("""
    **To set up your APIs:**
    
    1. **Anthropic API**: Get your API key from [Anthropic Console](https://console.anthropic.com/)
    2. **Zotero API**: Get your key from [Zotero Settings](https://www.zotero.org/settings/keys)
    
    Add them to your `.env` file in the project root.
    """)









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
# Auto-save and Cleanup
# ============================================================================
def handle_auto_save():
    """Handle automatic session saving"""
    if not st.session_state.get('session_manager'):
        return
    
    current_time = time.time()
    last_save = st.session_state.get('last_session_save', 0)
    
    # Auto-save every 30 seconds
    if current_time - last_save > 30:
        try:
            session_manager = st.session_state.session_manager
            if session_manager.current_session:
                # Sync any pending Streamlit state changes
                integration = get_session_integration()
                integration.sync_streamlit_to_session(session_manager.current_session)
                
                # Save session
                session_manager.save_current_session()
                st.session_state.last_session_save = current_time
                
        except Exception as e:
            # Silent failure for auto-save
            pass

def handle_ui_feedback():
    """Handle UI feedback messages"""
    # Show success messages
    if st.session_state.get('show_success_message'):
        st.success(st.session_state.show_success_message)
        del st.session_state.show_success_message
    
    # Show error messages
    if st.session_state.get('show_error_message'):
        st.error(st.session_state.show_error_message)
        del st.session_state.show_error_message
    
    # Show info messages
    if st.session_state.get('show_info_message'):
        st.info(st.session_state.show_info_message)
        del st.session_state.show_info_message

# ============================================================================
# Main Application
# ============================================================================
def main():
    """Main application with complete session integration"""
    # Render enhanced CSS
    render_all_enhanced_css()
    
    # Initialize app state
    init_app_session_state()
    
    # Initialize system
    if not initialize_system():
        st.stop()
    
    # Handle auto-save
    handle_auto_save()
    
    # Handle UI feedback
    handle_ui_feedback()
    
    # Get session manager
    session_manager = st.session_state.session_manager
    
    # Render enhanced sidebar
    sidebar = EnhancedSidebar(session_manager)
    sidebar.render()
    
    # Main content area
    render_main_content_area(session_manager)


# ============================================================================
# Application Entry Point
# ============================================================================
if __name__ == "__main__":
    main()