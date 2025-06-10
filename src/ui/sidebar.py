# src/ui/sidebar.py
"""
Sidebar component for Physics Literature Synthesis Pipeline
Implements ChatGPT/Claude-style sidebar with KB management + session list
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from ..sessions import SessionManager
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class Sidebar:
    """
    Main sidebar component with KB management and session list
    Layout: Logo -> KB/Zotero/Settings -> Divider -> Sessions
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize sidebar component
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
    
    def render(self):
        """Render the complete sidebar"""
        with st.sidebar:
            self._render_header()
            self._render_management_section()
            self._render_divider()
            self._render_sessions_section()
    
    def _render_header(self):
        """Render logo and title at top of sidebar"""
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 1.5rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 1.5rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🔬</div>
            <h3 style="margin: 0; color: #1f2937; font-weight: 700; font-size: 1.2rem;">Physics Research</h3>
            <p style="margin: 0; color: #6b7280; font-size: 0.8rem;">Literature Assistant</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_management_section(self):
        """Render KB management, Zotero, and Settings buttons"""
        st.markdown("### Management")
        
        # Knowledge Bases button
        if st.button("📚 Knowledge Bases", key="sidebar_kb", use_container_width=True):
            st.session_state.show_kb_management = True
            st.rerun()
        
        # Zotero Integration button (if available)
        if st.session_state.get('zotero_available', False):
            if st.button("🔗 Zotero Integration", key="sidebar_zotero", use_container_width=True):
                st.session_state.show_zotero_management = True
                st.rerun()
        
        # Settings button
        if st.button("⚙️ Settings", key="sidebar_settings", use_container_width=True):
            st.session_state.show_settings = True
            st.rerun()
        
        # Quick status indicators
        self._render_status_indicators()
    
    def _render_status_indicators(self):
        """Render compact status indicators"""
        config = st.session_state.get('config')
        if not config:
            return
        
        st.markdown("##### Status")
        
        # API Keys
        api_status = config.check_env_file()
        anthropic_status = "✅" if api_status.get('anthropic_api_key') else "❌"
        st.markdown(f"**Anthropic:** {anthropic_status}")
        
        # Zotero
        zotero_status = st.session_state.get('zotero_status', 'unknown')
        if zotero_status == 'connected':
            zotero_icon = "✅"
            collections_count = len(st.session_state.get('zotero_collections', []))
            zotero_text = f"✅ ({collections_count} collections)"
        elif zotero_status == 'not_configured':
            zotero_text = "⚙️ Not setup"
        else:
            zotero_text = "❌ Error"
        
        st.markdown(f"**Zotero:** {zotero_text}")
        
        # Current KB
        current_session = self.session_manager.current_session
        if current_session and current_session.knowledge_base_name:
            st.markdown(f"**KB:** ✅ {current_session.knowledge_base_name}")
        else:
            st.markdown("**KB:** ⚪ None")
    
    def _render_divider(self):
        """Render divider between management and sessions"""
        st.markdown("""
        <div style="margin: 1.5rem 0; border-bottom: 1px solid #e2e8f0;"></div>
        """, unsafe_allow_html=True)
    
    def _render_sessions_section(self):
        """Render sessions list with new session button"""
        # Section header with new session button
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("### Conversations")
        
        with col2:
            if st.button("➕", key="new_session", help="New Session", use_container_width=True):
                self._create_new_session()
        
        # Sessions list
        self._render_sessions_list()
    
    def _render_sessions_list(self):
        """Render list of all sessions"""
        sessions = self.session_manager.list_sessions()
        current_session = self.session_manager.current_session
        current_session_id = current_session.id if current_session else None
        
        if not sessions:
            st.markdown("*No conversations yet*")
            return
        
        # Group sessions by date for better organization
        grouped_sessions = self._group_sessions_by_date(sessions)
        
        for date_group, group_sessions in grouped_sessions.items():
            if date_group != "Today":  # Only show date headers for older sessions
                st.markdown(f"**{date_group}**")
            
            for session_meta in group_sessions:
                self._render_session_item(session_meta, current_session_id)
    
    def _render_session_item(self, session_meta: Dict, current_session_id: Optional[str]):
        """Render individual session item"""
        session_id = session_meta['id']
        session_name = session_meta['name']
        is_current = session_id == current_session_id
        
        # Create container for session item
        container = st.container()
        
        with container:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                # Session button with current session highlighting
                button_style = "sidebar_session_current" if is_current else "sidebar_session"
                
                if st.button(
                    session_name,
                    key=f"session_{session_id}",
                    help=self._get_session_tooltip(session_meta),
                    use_container_width=True
                ):
                    if not is_current:
                        self._switch_to_session(session_id)
            
            with col2:
                # Session options menu
                if st.button("⋮", key=f"menu_{session_id}", help="Session options"):
                    st.session_state[f'show_session_menu_{session_id}'] = True
                    st.rerun()
        
        # Session options menu (if open)
        if st.session_state.get(f'show_session_menu_{session_id}', False):
            self._render_session_menu(session_id, session_name)
    
    def _render_session_menu(self, session_id: str, session_name: str):
        """Render session options menu"""
        with st.expander(f"Options: {session_name[:20]}...", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✏️ Rename", key=f"rename_{session_id}"):
                    st.session_state[f'rename_session_{session_id}'] = True
                    st.session_state[f'show_session_menu_{session_id}'] = False
                    st.rerun()
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                    st.session_state[f'confirm_delete_{session_id}'] = True
                    st.session_state[f'show_session_menu_{session_id}'] = False
                    st.rerun()
            
            # Close menu button
            if st.button("✖️ Close", key=f"close_menu_{session_id}"):
                st.session_state[f'show_session_menu_{session_id}'] = False
                st.rerun()
        
        # Handle rename dialog
        if st.session_state.get(f'rename_session_{session_id}', False):
            self._render_rename_dialog(session_id, session_name)
        
        # Handle delete confirmation
        if st.session_state.get(f'confirm_delete_{session_id}', False):
            self._render_delete_confirmation(session_id, session_name)
    
    def _render_rename_dialog(self, session_id: str, current_name: str):
        """Render session rename dialog"""
        st.markdown("**Rename Session**")
        
        new_name = st.text_input(
            "New name:",
            value=current_name,
            key=f"new_name_{session_id}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Save", key=f"save_rename_{session_id}"):
                if new_name.strip():
                    if self.session_manager.rename_session(session_id, new_name.strip()):
                        st.success("Renamed successfully!")
                        st.session_state[f'rename_session_{session_id}'] = False
                        st.rerun()
                    else:
                        st.error("Failed to rename session")
                else:
                    st.error("Name cannot be empty")
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_rename_{session_id}"):
                st.session_state[f'rename_session_{session_id}'] = False
                st.rerun()
    
    def _render_delete_confirmation(self, session_id: str, session_name: str):
        """Render session delete confirmation dialog"""
        st.markdown("**Delete Session**")
        st.warning(f"Are you sure you want to delete '{session_name}'?")
        st.markdown("*This action cannot be undone.*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete", key=f"confirm_delete_yes_{session_id}"):
                if self.session_manager.delete_session(session_id):
                    st.success("Session deleted!")
                    st.session_state[f'confirm_delete_{session_id}'] = False
                    
                    # If we deleted the current session, create a new one
                    if (self.session_manager.current_session and 
                        self.session_manager.current_session.id == session_id):
                        self._create_new_session()
                    
                    st.rerun()
                else:
                    st.error("Failed to delete session")
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_delete_{session_id}"):
                st.session_state[f'confirm_delete_{session_id}'] = False
                st.rerun()
    
    def _group_sessions_by_date(self, sessions: List[Dict]) -> Dict[str, List[Dict]]:
        """Group sessions by date for better organization"""
        grouped = {
            "Today": [],
            "Yesterday": [],
            "This Week": [],
            "Older": []
        }
        
        now = datetime.now()
        today = now.date()
        
        for session in sessions:
            last_active = datetime.fromisoformat(session['last_active'])
            session_date = last_active.date()
            
            days_diff = (today - session_date).days
            
            if days_diff == 0:
                grouped["Today"].append(session)
            elif days_diff == 1:
                grouped["Yesterday"].append(session)
            elif days_diff <= 7:
                grouped["This Week"].append(session)
            else:
                grouped["Older"].append(session)
        
        # Remove empty groups
        return {k: v for k, v in grouped.items() if v}
    
    def _get_session_tooltip(self, session_meta: Dict) -> str:
        """Generate tooltip text for session"""
        parts = []
        
        # Message count
        msg_count = session_meta.get('message_count', 0)
        if msg_count > 0:
            parts.append(f"{msg_count} messages")
        
        # KB info
        kb_name = session_meta.get('knowledge_base_name')
        if kb_name:
            parts.append(f"KB: {kb_name}")
        
        # Document count
        doc_count = session_meta.get('document_count', 0)
        if doc_count > 0:
            parts.append(f"{doc_count} documents")
        
        # Last active
        last_active = datetime.fromisoformat(session_meta['last_active'])
        parts.append(f"Last active: {last_active.strftime('%m/%d %I:%M %p')}")
        
        return " • ".join(parts) if parts else "Empty session"
    
    def _create_new_session(self):
        """Create a new session and switch to it"""
        try:
            new_session = self.session_manager.create_session(
                name="New Session",
                auto_activate=True
            )
            
            # Clear any open management dialogs
            st.session_state.show_kb_management = False
            st.session_state.show_zotero_management = False
            st.session_state.show_settings = False
            
            logger.info(f"Created new session from sidebar: {new_session.id}")
            st.rerun()
            
        except Exception as e:
            logger.error(f"Failed to create new session: {e}")
            st.error("Failed to create new session")
    
    def _switch_to_session(self, session_id: str):
        """Switch to a different session"""
        try:
            if self.session_manager.switch_to_session(session_id):
                # Clear any open management dialogs
                st.session_state.show_kb_management = False
                st.session_state.show_zotero_management = False
                st.session_state.show_settings = False
                
                logger.info(f"Switched to session: {session_id}")
                st.rerun()
            else:
                st.error("Failed to switch session")
                
        except Exception as e:
            logger.error(f"Failed to switch to session {session_id}: {e}")
            st.error("Failed to switch session")


def render_sidebar_css():
    """Render CSS for sidebar styling"""
    st.markdown("""
    <style>
    /* Sidebar navigation button styling */
    div[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: auto !important;
        background-color: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        color: #374151 !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 0.75rem !important;
        margin-bottom: 0.5rem !important;
        transition: all 0.3s ease !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    
    /* Hover effects */
    div[data-testid="stSidebar"] .stButton > button:hover {
        background-color: #f1f5f9 !important;
        border-color: #667eea !important;
        transform: translateX(2px) !important;
    }
    
    /* Active session styling */
    div[data-testid="stSidebar"] .stButton > button[aria-pressed="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border-color: transparent !important;
        transform: translateX(2px) !important;
    }
    
    /* Management buttons styling */
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key*="sidebar_"]) button {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
        font-weight: 600 !important;
    }
    
    /* New session button */
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key="new_session"]) button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        font-size: 1.2rem !important;
        padding: 0.5rem !important;
    }
    
    /* Session options button */
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key*="menu_"]) button {
        background: transparent !important;
        border: 1px solid #d1d5db !important;
        color: #6b7280 !important;
        padding: 0.25rem !important;
        min-height: auto !important;
        height: 2rem !important;
    }
    
    /* Sidebar container styling */
    .css-1d391kg {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* Status text styling */
    div[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.9rem !important;
    }
    </style>
    """, unsafe_allow_html=True)