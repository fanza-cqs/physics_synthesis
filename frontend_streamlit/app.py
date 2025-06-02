#!/usr/bin/env python3
"""
Physics Literature Synthesis Pipeline - Streamlit Web App
A beautiful, modern interface for your physics research assistant.
"""

# ============================================================================
# CRITICAL: PyTorch Compatibility Fix - Must be FIRST
# ============================================================================
import torch

if not hasattr(torch, 'get_default_device'):
    def get_default_device():
        """Fallback implementation for older PyTorch versions."""
        if torch.cuda.is_available():
            return torch.device('cuda')
        else:
            return torch.device('cpu')
    
    torch.get_default_device = get_default_device
    print("✅ Applied PyTorch compatibility fix")

# ============================================================================
# Now your existing imports
# ============================================================================
import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime
import time

# Add project root to path
frontend_dir = Path(__file__).parent
project_root = frontend_dir.parent
sys.path.insert(0, str(project_root))

# Import frontend utilities
sys.path.insert(0, str(frontend_dir))
from utils.css_loader import load_all_styles, apply_custom_css

# Import system components (after path setup)
from config import PipelineConfig
from src.core import KnowledgeBase
from src.chat import LiteratureAssistant
from src.downloaders import LiteratureDownloader

# Configure page
st.set_page_config(
    page_title="Physics Literature Synthesis",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS styles
load_all_styles()

def initialize_system():
    """Initialize the physics synthesis system"""
    if 'system_initialized' not in st.session_state:
        with st.spinner("🚀 Initializing Physics Literature System..."):
            try:
                # Configuration helper
                def create_config(overrides=None):
                    config = PipelineConfig(overrides)
                    config.project_root = project_root
                    config.documents_root = project_root / "documents"
                    config.literature_folder = config.documents_root / "literature"
                    config.your_work_folder = config.documents_root / "your_work"
                    config.biblio_folder = config.documents_root / "biblio"
                    config.current_drafts_folder = config.documents_root / "current_drafts"
                    config.cache_file = project_root / "physics_knowledge_base.pkl"
                    config._create_directories()
                    return config
                
                st.session_state.config = create_config()
                
                # Try to load existing knowledge base
                kb = KnowledgeBase()
                if st.session_state.config.cache_file.exists():
                    if kb.load_from_file(st.session_state.config.cache_file):
                        st.session_state.knowledge_base = kb
                        
                        # Initialize chat if API key available
                        try:
                            st.session_state.config.validate_api_keys()
                            st.session_state.assistant = LiteratureAssistant(
                                knowledge_base=kb,
                                anthropic_api_key=st.session_state.config.anthropic_api_key,
                                chat_config=st.session_state.config.get_chat_config()
                            )
                            st.session_state.chat_ready = True
                        except ValueError:
                            st.session_state.chat_ready = False
                    else:
                        st.session_state.knowledge_base = None
                else:
                    st.session_state.knowledge_base = None
                
                st.session_state.system_initialized = True
                
            except Exception as e:
                st.error(f"❌ System initialization failed: {e}")
                st.session_state.system_initialized = False

def main():
    """Main application"""
    
    # Header
    st.markdown('<h1 class="main-header">🔬 Physics Literature Synthesis</h1>', unsafe_allow_html=True)
    st.markdown("**AI-Powered Research Assistant for Physics Literature**")
    
    # Initialize system
    initialize_system()
    
    if not st.session_state.get('system_initialized', False):
        st.error("System failed to initialize. Please check your configuration.")
        return
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Control Panel")
        
        # Chat Settings (replacing system status)
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("#### ⚙️ Chat Settings")
        
        # Initialize chat settings in session state
        if "chat_temperature" not in st.session_state:
            st.session_state.chat_temperature = 0.3
        if "chat_max_sources" not in st.session_state:
            st.session_state.chat_max_sources = 8
        
        # Temperature slider
        st.session_state.chat_temperature = st.slider(
            "🌡️ Creativity", 
            0.0, 1.0, 
            st.session_state.chat_temperature, 
            0.1,
            help="Lower = more focused responses, Higher = more creative responses"
        )
        
        # Max sources slider
        st.session_state.chat_max_sources = st.slider(
            "📄 Max Sources", 
            1, 20, 
            st.session_state.chat_max_sources,
            help="Number of document chunks to use as context for responses"
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Quick Actions
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown("#### ⚡ Quick Actions")
        
        if st.button("🔄 Rebuild Knowledge Base", type="secondary"):
            st.rerun()
        
        if st.button("🗑️ Clear Chat History", type="secondary"):
            st.session_state.messages = []
            st.success("Chat history cleared!")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Main content tabs - simplified to essential functions
    tab1, tab2 = st.tabs(["💬 Chat Assistant", "📥 Literature Manager"])
    
    with tab1:
        chat_interface()
    
    with tab2:
        literature_manager_interface()

def chat_interface():
    """Chat interface with the literature assistant"""
    st.header("💬 Literature-Aware Chat Assistant")
    
    if not st.session_state.get('chat_ready'):
        st.warning("🔑 Chat assistant requires ANTHROPIC_API_KEY. Please set it in your environment variables.")
        st.code("export ANTHROPIC_API_KEY='your-api-key-here'")
        return
    
    if not st.session_state.get('knowledge_base'):
        st.warning("📚 No knowledge base loaded. Please build one in the Literature Manager tab.")
        return
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Clean header
    st.markdown("**Ask questions about your research papers and get AI-powered insights!**")
    
    # Display chat history
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message"><strong>🧑‍🔬 You:</strong> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="assistant-message"><strong>🤖 Assistant:</strong> {message["content"]}</div>', unsafe_allow_html=True)
            if "sources" in message and message["sources"]:
                st.markdown(f'<div class="chat-sources">📚 Sources: {", ".join(message["sources"])}</div>', unsafe_allow_html=True)
    
    # Thin custom divider
    #st.markdown('<div class="thin-divider"></div>', unsafe_allow_html=True)
    
    # Chat input (uses settings from sidebar)
    if prompt := st.chat_input("Ask about your research papers..."):
        process_chat_message(prompt, st.session_state.chat_temperature, st.session_state.chat_max_sources)
    
    # Suggested questions
    st.markdown('<div class="suggested-questions">', unsafe_allow_html=True)
    st.markdown("**💡 Quick Start:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📋 What papers do I have?"):
            process_chat_message("What papers do I have in my knowledge base?", st.session_state.chat_temperature, st.session_state.chat_max_sources)
    
    with col2:
        if st.button("🔬 Main research topics?"):
            process_chat_message("What are the main research topics in my collection?", st.session_state.chat_temperature, st.session_state.chat_max_sources)
    
    with col3:
        if st.button("✍️ Help with writing"):
            process_chat_message("Help me write an introduction about quantum information theory", st.session_state.chat_temperature, st.session_state.chat_max_sources)
    
    st.markdown('</div>', unsafe_allow_html=True)

def process_chat_message(prompt, temperature, max_context):
    """Process a chat message"""
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get AI response
    with st.spinner("🤖 Thinking..."):
        try:
            response = st.session_state.assistant.ask(
                prompt, 
                temperature=temperature,
                max_context_chunks=max_context
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

def knowledge_base_interface():
    """Knowledge base management interface"""
    st.header("📚 Knowledge Base Management")
    
    # Knowledge base status
    if st.session_state.get('knowledge_base'):
        stats = st.session_state.knowledge_base.get_statistics()
        
        # Metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📚 Total Documents", stats.get('total_documents', 0))
        with col2:
            st.metric("✅ Successfully Processed", stats.get('successful_documents', 0))
        with col3:
            st.metric("🧩 Text Chunks", stats.get('total_chunks', 0))
        with col4:
            st.metric("📝 Total Words", f"{stats.get('total_words', 0):,}")
        
        # Source breakdown
        st.subheader("📊 Source Breakdown")
        source_data = []
        for source_type, info in stats.get('source_breakdown', {}).items():
            count = info.get('successful', 0) if isinstance(info, dict) else info
            source_data.append({"Source": source_type.replace('_', ' ').title(), "Documents": count})
        
        if source_data:
            df = pd.DataFrame(source_data)
            fig = px.pie(df, values='Documents', names='Source', 
                        title="Document Distribution by Source")
            st.plotly_chart(fig, use_container_width=True)
        
        # Document list
        st.subheader("📄 Document Details")
        papers = st.session_state.knowledge_base.list_documents()
        if papers:
            df_papers = pd.DataFrame(papers)
            st.dataframe(df_papers, use_container_width=True)
        
    else:
        st.warning("📭 No knowledge base loaded")
        
        if st.button("🏗️ Build Knowledge Base", type="primary"):
            build_knowledge_base()

def build_knowledge_base():
    """Build the knowledge base"""
    with st.spinner("🏗️ Building knowledge base..."):
        try:
            kb = KnowledgeBase(
                embedding_model=st.session_state.config.embedding_model,
                chunk_size=st.session_state.config.chunk_size,
                chunk_overlap=st.session_state.config.chunk_overlap
            )
            
            stats = kb.build_from_directories(
                literature_folder=st.session_state.config.literature_folder,
                your_work_folder=st.session_state.config.your_work_folder,
                current_drafts_folder=st.session_state.config.current_drafts_folder
            )
            
            kb.save_to_file(st.session_state.config.cache_file)
            st.session_state.knowledge_base = kb
            
            # Initialize assistant if API key available
            try:
                st.session_state.config.validate_api_keys()
                st.session_state.assistant = LiteratureAssistant(
                    knowledge_base=kb,
                    anthropic_api_key=st.session_state.config.anthropic_api_key,
                    chat_config=st.session_state.config.get_chat_config()
                )
                st.session_state.chat_ready = True
            except ValueError:
                pass
            
            st.success(f"✅ Knowledge base built successfully! Processed {stats.get('total_documents', 0)} documents.")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to build knowledge base: {e}")

def literature_manager_interface():
    """Literature download and management interface"""
    st.header("📥 Literature Manager")
    
    # File upload section
    st.subheader("📂 Upload BibTeX Files")
    uploaded_files = st.file_uploader(
        "Upload .bib files from Zotero",
        type=['bib'],
        accept_multiple_files=True,
        help="Export your Zotero collection as BibTeX format"
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            # Save uploaded file
            bib_path = st.session_state.config.biblio_folder / uploaded_file.name
            with open(bib_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"✅ Saved {uploaded_file.name}")
    
    # Show existing .bib files
    st.subheader("📚 Available BibTeX Files")
    bib_files = list(st.session_state.config.biblio_folder.glob("*.bib"))
    
    if bib_files:
        selected_bib = st.selectbox("Select .bib file to process:", [f.name for f in bib_files])
        
        if st.button("🚀 Download Literature from arXiv", type="primary"):
            download_literature(selected_bib)
    else:
        st.info("📭 No .bib files found. Upload some above!")
    
    # Show downloaded papers
    st.subheader("📄 Downloaded Papers")
    if st.session_state.config.literature_folder.exists():
        papers = list(st.session_state.config.literature_folder.iterdir())
        if papers:
            st.metric("Downloaded Files", len(papers))
            
            # Show recent downloads
            papers_data = []
            for paper in papers[:10]:  # Show first 10
                size_mb = paper.stat().st_size / (1024 * 1024)
                papers_data.append({
                    "File": paper.name,
                    "Type": paper.suffix.upper(),
                    "Size (MB)": f"{size_mb:.2f}"
                })
            
            if papers_data:
                df = pd.DataFrame(papers_data)
                st.dataframe(df, use_container_width=True)
        else:
            st.info("📭 No papers downloaded yet")

def download_literature(bib_filename):
    """Download literature from selected .bib file"""
    with st.spinner("🚀 Downloading literature from arXiv..."):
        try:
            bib_path = st.session_state.config.biblio_folder / bib_filename
            
            downloader = LiteratureDownloader(
                output_directory=st.session_state.config.literature_folder,
                delay_between_downloads=st.session_state.config.download_delay,
                arxiv_config=st.session_state.config.get_arxiv_config()
            )
            
            results = downloader.download_from_bibtex(bib_path)
            
            st.success(f"✅ Download complete! Found {len(results['successful'])} papers, failed {len(results['failed'])}")
            
            # Show results
            if results['successful']:
                st.subheader("📥 Successfully Downloaded")
                for result in results['successful'][:5]:  # Show first 5
                    st.write(f"• {result.paper_metadata.title[:60]}... (arXiv:{result.search_result.arxiv_id})")
            
            if results['failed']:
                st.subheader("❌ Failed Downloads")
                for result in results['failed'][:5]:  # Show first 5
                    st.write(f"• {result.paper_metadata.title[:60]}...")
            
        except Exception as e:
            st.error(f"❌ Download failed: {e}")

def analytics_interface():
    """Analytics and visualization interface"""
    st.header("📊 Research Analytics")
    
    if not st.session_state.get('knowledge_base'):
        st.warning("📊 Build a knowledge base first to see analytics")
        return
    
    stats = st.session_state.knowledge_base.get_statistics()
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Research Volume", f"{stats.get('total_words', 0):,} words")
    with col2:
        st.metric("Average Document Size", f"{stats.get('avg_words_per_doc', 0):.0f} words")
    with col3:
        st.metric("Knowledge Density", f"{stats.get('total_chunks', 0)} chunks")
    
    # Source distribution
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📚 Document Sources")
        source_data = []
        for source_type, info in stats.get('source_breakdown', {}).items():
            count = info.get('successful', 0) if isinstance(info, dict) else info
            source_data.append({"Source": source_type.replace('_', ' ').title(), "Count": count})
        
        if source_data:
            df = pd.DataFrame(source_data)
            fig = px.bar(df, x='Source', y='Count', 
                        title="Documents by Source Type",
                        color='Source')
            st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("💾 Storage Analytics")
        # Create sample storage data
        storage_data = {
            "Component": ["Embeddings", "Text Content", "Metadata", "Cache"],
            "Size (MB)": [15.2, 8.7, 2.1, 5.4]
        }
        df_storage = pd.DataFrame(storage_data)
        fig = px.pie(df_storage, values='Size (MB)', names='Component', 
                    title="Storage Distribution")
        st.plotly_chart(fig, use_container_width=True)

if __name__ == "__main__":
    main()