"""
CSS Loading Utility for Streamlit App
"""

import streamlit as st
from pathlib import Path

def load_css_file(css_file_path):
    """Load CSS from a file"""
    try:
        with open(css_file_path, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        st.markdown(f"""
        <style>
        {css_content}
        </style>
        """, unsafe_allow_html=True)
        
        return True
    except FileNotFoundError:
        st.error(f"CSS file not found: {css_file_path}")
        return False
    except Exception as e:
        st.error(f"Error loading CSS file: {e}")
        return False

def load_all_styles():
    """Load all CSS files for the application"""
    frontend_dir = Path(__file__).parent.parent
    styles_dir = frontend_dir / "styles"
    
    # Load main styles
    main_css = styles_dir / "main.css"
    chat_css = styles_dir / "chat.css"
    
    success = True
    
    if main_css.exists():
        success &= load_css_file(main_css)
    else:
        st.warning(f"Main CSS file not found: {main_css}")
        success = False
    
    if chat_css.exists():
        success &= load_css_file(chat_css)
    else:
        st.warning(f"Chat CSS file not found: {chat_css}")
        success = False
    
    return success

def apply_custom_css(additional_css=""):
    """Apply custom CSS styles"""
    if additional_css:
        st.markdown(f"""
        <style>
        {additional_css}
        </style>
        """, unsafe_allow_html=True)

def get_css_for_theme(theme="light"):
    """Get theme-specific CSS"""
    if theme == "dark":
        return """
        .main-header {
            background: linear-gradient(90deg, #9333ea 0%, #3b82f6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .metric-card {
            background: linear-gradient(135deg, #1f2937 0%, #374151 100%);
            border: 1px solid #4b5563;
        }
        
        .sidebar-section {
            background: #1f2937;
            color: #f9fafb;
            border: 1px solid #374151;
        }
        """
    else:
        return ""  # Use default light theme CSS