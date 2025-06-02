#!/usr/bin/env python3
"""
Minimalistic Physics Literature Synthesis App - Streamlit Web App
Three-step wizard: Upload BibTeX, Download & Embed, Chat & Explore
"""

# ============================================================================
# PyTorch Compatibility Fix - Must be FIRST
# ============================================================================
import torch

if not hasattr(torch, 'get_default_device'):
    def get_default_device():
        if torch.cuda.is_available():
            return torch.device('cuda')
        return torch.device('cpu')
    torch.get_default_device = get_default_device
    print("✅ Applied PyTorch compatibility fix")

# ============================================================================
# Imports
# ============================================================================
import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import re
from typing import List, Dict, Any

# Add project root to path
frontend_dir = Path(__file__).parent
project_root = frontend_dir.parent
sys.path.insert(0, str(project_root))

# Import frontend utilities
sys.path.insert(0, str(frontend_dir))
from utils.css_loader import load_all_styles

# Import system components
from config import PipelineConfig
from src.core import KnowledgeBase
from src.chat import LiteratureAssistant
from src.downloaders import LiteratureDownloader

# ============================================================================
# Page Configuration
# ============================================================================
st.set_page_config(
    page_title="Physics Literature Synthesizer",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load existing CSS styles
load_all_styles()

# Add minimalist CSS overrides
st.markdown("""
<style>
/* Main title styling */
.main-title {
    font-size: 2.5rem;
    font-weight: 600;
    color: #1a1a1a;
    text-align: center;
    margin-bottom: 0.5rem;
}

.step-indicator {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 8px;
    padding: 1rem;
    margin-bottom: 2rem;
    text-align: center;
    font-size: 1.1rem;
}

.step-card {
    background: white;
    border: 1px solid #e9ecef;
    border-radius: 12px;
    padding: 2rem;
    margin-bottom: 2rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.upload-area {
    border: 2px dashed #cbd5e0;
    border-radius: 8px;
    padding: 3rem;
    text-align: center;
    background: #f8f9fa;
    margin: 1rem 0;
}

.upload-area:hover {
    border-color: #17a2b8;
    background: #e8f4f8;
}

.status-success {
    color: #28a745;
    font-weight: 500;
}

.status-error {
    color: #dc3545;
    font-weight: 500;
}

.chat-message {
    margin-bottom: 1rem;
    padding: 1rem;
    border-radius: 8px;
}

.user-message {
    background: #e3f2fd;
    margin-left: 2rem;
}

.assistant-message {
    background: #f5f5f5;
    margin-right: 2rem;
}

.progress-info {
    background: #f8f9fa;
    border-radius: 6px;
    padding: 1rem;
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ============================================================================
# Session State Initialization
# ============================================================================
def init_session_state():
    defaults = {
        'step': 1,
        'bib_files': [],
        'download_results': None,
        'system_initialized': False,
        'knowledge_base': None,
        'assistant': None,
        'chat_ready': False,
        'messages': [],
        'chat_temperature': 0.3,
        'chat_max_sources': 8
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# ============================================================================
# System Initialization
# ============================================================================
def initialize_system():
    if not st.session_state.system_initialized:
        with st.spinner("🚀 Initializing system..."):
            try:
                # Configuration helper (same as original app.py)
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
                        st.session_state.step = 3  # Skip to chat
                        
                        # Initialize chat if API key available (same as original)
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

# ============================================================================
# BibTeX Parser (removed - not needed for simple approach)
# ============================================================================

# ============================================================================
# Step Interfaces
# ============================================================================

# ----------------------------------------------------------------------------
# Step 1: Upload & Preview BibTeX
# - File uploader
# - Preview table of filenames
# - Advance to next step on validation
# ----------------------------------------------------------------------------
def step1_interface():
    st.subheader("Step 1: Upload & Preview BibTeX")
    uploaded = st.file_uploader(
        "Upload .bib files", type=['bib'], accept_multiple_files=True
    )
    if uploaded:
        st.session_state.bib_files = []
        table = []
        for f in uploaded:
            # Save each upload to project biblio folder
            dest = st.session_state.config.biblio_folder / f.name
            dest.write_bytes(f.getbuffer())
            st.session_state.bib_files.append(dest)
            table.append({"File": f.name})
        # Render simple table preview
        st.table(pd.DataFrame(table))
        # Proceed only when user confirms
        if st.button("Validate & Next"):
            st.session_state.step = 2
            st.rerun()

# ----------------------------------------------------------------------------
# Step 2: Download & Embed
# - Tabbed: Download from arXiv, then Embed to vector DB
# - Show status and results
# ----------------------------------------------------------------------------
def step2_interface():
    st.subheader("Step 2: Download & Embed")
    tab_dl, tab_emb = st.tabs(["Download", "Embed"])

    # ----- Download tab -----
    with tab_dl:
        selected = st.selectbox(
            "Select .bib file to process",
            [p.name for p in st.session_state.bib_files]
        )
        if st.button("🚀 Download Literature"):
            downloader = LiteratureDownloader(
                output_directory=st.session_state.config.literature_folder,
                delay_between_downloads=st.session_state.config.download_delay,
                arxiv_config=st.session_state.config.get_arxiv_config()
            )
            res = downloader.download_from_bibtex(
                st.session_state.config.biblio_folder / selected
            )
            st.session_state.download_results = res
        if st.session_state.download_results:
            succ = len(st.session_state.download_results['successful'])
            fail = len(st.session_state.download_results['failed'])
            st.markdown(f"✅ {succ} succeeded, ❌ {fail} failed")

    # ----- Embed tab -----
    with tab_emb:
        if st.button("🚀 Build Knowledge Base"):
            # Build vector store and chunk text
            kb = KnowledgeBase(
                embedding_model=st.session_state.config.embedding_model,
                chunk_size=st.session_state.config.chunk_size,
                chunk_overlap=st.session_state.config.chunk_overlap
            )
            kb.build_from_directories(
                st.session_state.config.literature_folder,
                st.session_state.config.your_work_folder,
                st.session_state.config.current_drafts_folder
            )
            kb.save_to_file(st.session_state.config.cache_file)
            st.session_state.knowledge_base = kb
            st.session_state.step = 3
            st.rerun()
        else:
            # Placeholder until embedding begins
            st.progress(0)
            st.write("Ready to embed once knowledge base is built.")

# ----------------------------------------------------------------------------
# Step 3: Chat & Explore
# - Sidebar settings for chat
# - Interactive chat window
# ----------------------------------------------------------------------------
def step3_interface():
    st.subheader("Step 3: Chat & Explore")
    # Sidebar only appears in final step
    with st.sidebar:
        st.header("⚙️ Chat Settings")
        st.session_state.chat_temperature = st.slider(
            "Creativity", 0.0, 1.0,
            st.session_state.get('chat_temperature', 0.3), 0.1
        )
        st.session_state.chat_max_sources = st.slider(
            "Max Sources", 1, 20,
            st.session_state.get('chat_max_sources', 8)
        )

    # Ensure KB loaded
    kb = st.session_state.get('knowledge_base')
    if not kb:
        st.warning("Knowledge base not found. Return to Step 2.")
        return

    # Lazy-init assistant with API keys (improved from original app.py)
    if 'assistant' not in st.session_state:
        try:
            cfg = st.session_state.config
            cfg.validate_api_keys()
            st.session_state.assistant = LiteratureAssistant(
                knowledge_base=kb,
                anthropic_api_key=cfg.anthropic_api_key,
                chat_config=cfg.get_chat_config()
            )
            st.session_state.chat_ready = True
        except ValueError:
            st.session_state.chat_ready = False
    
    if not st.session_state.get('chat_ready', False):
        st.warning("🔑 Chat assistant requires ANTHROPIC_API_KEY. Please set it in your environment variables.")
        st.code("export ANTHROPIC_API_KEY='your-api-key-here'")
        return

    # Display chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        prefix = "You:" if msg['role']=='user' else "Assistant:"
        st.markdown(f"**{prefix}** {msg['content']}")

    # Chat input and processing
    if prompt := st.chat_input("Ask about your papers..."):
        st.session_state.messages.append({'role':'user','content':prompt})
        with st.spinner("🤖 Thinking..."):
            resp = st.session_state.assistant.ask(
                prompt,
                temperature=st.session_state.chat_temperature,
                max_context_chunks=st.session_state.chat_max_sources
            )
            st.session_state.messages.append({'role':'assistant','content':resp.content})
        st.rerun()

# ============================================================================
# Main Application
# ============================================================================
def main():
    init_session_state()
    initialize_system()
    
    # Header
    st.title("🔬 Physics Literature Synthesizer")
    st.caption(f"Step {st.session_state.step} of 3")
    
    # Render current step
    if st.session_state.step == 1:
        step1_interface()
    elif st.session_state.step == 2:
        step2_interface()
    elif st.session_state.step == 3:
        step3_interface()

if __name__ == "__main__":
    main()