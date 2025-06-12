#!/usr/bin/env python3
"""Zotero management page."""
import streamlit as st
from pathlib import Path
import sys

# Path setup
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from frontend_streamlit.app_sessions import initialize_system, render_zotero_page

if 'system_initialized' not in st.session_state:
    initialize_system()

render_zotero_page()