# src/ui/enhanced_sidebar.py
"""
Enhanced Sidebar component with full session integration
Replaces the basic sidebar with session-aware functionality
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..utils.zotero_utils import (
    retry_zotero_connection,
    get_zotero_status_display,
    is_zotero_working
)

from ..sessions import SessionManager
from ..sessions.session_integration import get_session_integration #get_session_integration_safe
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class Sidebar:
    """
    Enhanced sidebar component with full session integration
    Handles session management and navigation with proper state sync
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize enhanced sidebar component
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.integration = get_session_integration()
        #self.integration = get_session_integration_safe()

    
    def render(self):
        """Render the complete enhanced sidebar"""
        with st.sidebar:
            self._render_header()
            self._render_management_section()
            self._render_divider()
            self._render_sessions_section()
    
    def _render_header(self):
        """Render enhanced logo and title"""
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0 1.5rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 1.5rem;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem; animation: gentle-float 3s ease-in-out infinite;">🔬</div>
            <h3 style="margin: 0; color: #1f2937; font-weight: 700; font-size: 1.2rem;">Physics Research</h3>
            <p style="margin: 0; color: #6b7280; font-size: 0.8rem;">Literature Assistant</p>
        </div>
        
        <style>
        @keyframes gentle-float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-3px); }
        }
        </style>
        """, unsafe_allow_html=True)
    
    def _render_management_section(self):
        """Render enhanced management section"""
        st.markdown("### Management")
        
        # Knowledge Bases button
        if st.button("📚 Knowledge Bases", key="sidebar_kb", use_container_width=True):
            st.session_state.current_page = 'knowledge_bases'
            st.rerun()

        # Zotero Integration button (if available)
        if st.session_state.get('zotero_available', False):
            if st.button("🔗 Zotero Integration", key="sidebar_zotero", use_container_width=True):
                st.session_state.current_page = 'zotero'
                st.rerun()

        # Settings button
        if st.button("⚙️ Settings", key="sidebar_settings", use_container_width=True):
            st.session_state.current_page = 'settings'
            st.rerun()
        
        # Enhanced status indicators
        self._render_enhanced_status_indicators()
    

    def _render_enhanced_status_indicators(self):
        """Render enhanced status indicators with shared utility functions"""
        st.markdown("##### Status")
        
        config = st.session_state.get('config')
        if not config:
            st.error("❌ Config not loaded")
            return
        
        # API Keys status
        api_status = config.check_env_file()
        
        # Anthropic status
        if api_status.get('anthropic_api_key'):
            st.markdown("**Anthropic:** ✅")
        else:
            st.markdown("**Anthropic:** ❌")
            if st.button("🔧 Configure", key="config_anthropic", help="Configure Anthropic API"):
                st.session_state.current_page = 'settings'
                st.rerun()
        
        # Zotero status - CLEAN LOGIC using shared utilities
        status_text, display_class, is_working = get_zotero_status_display()
        
        if is_working:
            st.markdown(f"**Zotero:** {status_text}")
            
        elif display_class == "warning":  # Not configured
            st.markdown(f"**Zotero:** {status_text}")
            if st.button("🔧 Setup", key="setup_zotero", help="Setup Zotero integration"):
                st.session_state.current_page = 'settings'
                st.rerun()
                
        else:  # Error or other states
            st.markdown(f"**Zotero:** {status_text}")
            if st.button("🔄 Retry", key="retry_zotero", help="Retry Zotero connection"):
                with st.spinner("Retrying connection..."):
                    if retry_zotero_connection():
                        st.success("✅ Connection restored!")
                        st.rerun()
                    else:
                        st.error("❌ Retry failed")
        
        # Current session KB status
        current_session = self.session_manager.current_session
        if current_session and current_session.knowledge_base_name:
            kb_name = current_session.knowledge_base_name
            if len(kb_name) > 15:
                kb_display = kb_name[:12] + "..."
            else:
                kb_display = kb_name
            st.markdown(f"**KB:** ✅ {kb_display}")
        else:
            st.markdown("**KB:** ⚪ None")
        
        # Session stats
        if current_session:
            msg_count = len([m for m in current_session.messages if m.role == "user"])
            doc_count = len(current_session.documents)
            st.markdown(f"💬 {msg_count} msgs • 📄 {doc_count} docs")
        else:
            st.markdown("💬 0 msgs • 📄 0 docs")
    

    


    def _render_divider(self):
        """Render enhanced divider"""
        st.markdown("""
        <div style="margin: 1.5rem 0; border-bottom: 1px solid #e2e8f0;"></div>
        """, unsafe_allow_html=True)
    
    def _render_sessions_section(self):
        """Render enhanced sessions section"""
        # Section header with new session button
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown("### Conversations")
        
        with col2:
            if st.button("➕", key="new_session", help="New Session", use_container_width=True):
                self._create_new_session()
        
        # Sessions list with enhanced features
        self._render_enhanced_sessions_list()
    
    

    def _render_enhanced_sessions_list(self):
        """Render enhanced sessions list with clean UI and proper dividers"""

        # Don't show session list if we're in pending new conversation state
        if st.session_state.get('pending_new_session', False):
            st.markdown("*Start typing to create your conversation...*")
            st.markdown("✨ Your new chat will appear here after your first message")
            return
    
        # Get current session ID first
        current_session_id = None
        if self.session_manager.current_session:
            current_session_id = self.session_manager.current_session.id

        if self.integration is None:
            # Fallback: use session manager directly
            sessions = self.session_manager.list_sessions()
            st.info("Using basic session list (integration unavailable)")
        else:
            sessions = self.integration.get_session_list_for_ui()
        
        if not sessions:
            st.markdown("*No conversations yet*")
            st.markdown("Click **➕** to start your first conversation!")
            return
        
        # Group sessions by date for better organization
        grouped_sessions = self._group_sessions_by_date_enhanced(sessions)
        
        for date_group, group_sessions in grouped_sessions.items():
            # Show date headers for better organization
            if len(grouped_sessions) > 1 and date_group != "Today":
                st.markdown(f"**{date_group}**")
            
            # Filter and render sessions with proper dividers
            valid_sessions = []
            for session_meta in group_sessions:
                # Skip any sessions that might be named "New Session" with empty content
                # But print a debug statement
                if session_meta['name'] == "New Session" and session_meta.get('message_count', 0) == 0:
                    print("DEBUG: Empty <New Session> present!!")
                    continue  # Skip empty default sessions
                valid_sessions.append(session_meta)
            
            # Render valid sessions with dividers
            for i, session_meta in enumerate(valid_sessions):
                self._render_clean_session_item(session_meta, current_session_id, is_last=(i == len(valid_sessions) - 1))

    


    def _render_clean_session_item(self, session_meta: Dict, current_session_id: Optional[str], is_last: bool = False):
        """Render clean session item with title on top row, selectbox below, and divider"""
        session_id = session_meta['id']
        session_name = session_meta['name']
        is_current = session_id == current_session_id
        
        # Create a container for the session item
        with st.container():
            # Session title - full width on first row
            if is_current:
                # Current session - highlighted
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        color: white; padding: 0.6rem; border-radius: 6px; margin: 0.25rem 0;
                        font-weight: 600; font-size: 0.85rem;">
                    {session_name}
                </div>
                """, unsafe_allow_html=True)
            else:
                # Regular session - clickable button
                if st.button(
                    session_name,
                    key=f"session_{session_id}",
                    help=f"Switch to: {session_name}",
                    use_container_width=True
                ):
                    self._switch_to_session(session_id)
            
            # Selectbox for menu options - full width on second row
            menu_options = ["Options", "✏️ Rename", "📥 Download", "🗑️ Delete"]
            
            selected_option = st.selectbox(
                "Session Actions",  # No label
                menu_options,
                key=f"menu_select_{session_id}",
                index=0,  # Default to "Options"
                label_visibility="collapsed"  # Hide the label
            )
            
            # Handle the selected option
            if selected_option == "✏️ Rename":
                st.session_state[f'rename_session_{session_id}'] = True
                # Reset selectbox to default
                st.session_state[f"menu_select_{session_id}"] = "Options"
                st.rerun()
            elif selected_option == "📥 Download":
                self._export_session(session_id)
                # Reset selectbox to default
                st.session_state[f"menu_select_{session_id}"] = "Options"
                st.rerun()
            elif selected_option == "🗑️ Delete":
                st.session_state[f'confirm_delete_{session_id}'] = True
                # Reset selectbox to default
                st.session_state[f"menu_select_{session_id}"] = "Options"
                st.rerun()
            
            # Add horizontal divider after each session (except the last one)
            if not is_last:
                st.markdown("""
                <div style="border-bottom: 1px solid #e2e8f0; margin: 0.75rem 0 0.5rem 0;"></div>
                """, unsafe_allow_html=True)
        
        # Handle rename dialog
        if st.session_state.get(f'rename_session_{session_id}', False):
            self._render_simple_rename_dialog(session_id, session_name)
        
        # Handle delete confirmation
        if st.session_state.get(f'confirm_delete_{session_id}', False):
            self._render_simple_delete_confirmation(session_id, session_name)

    

    
    def _render_simple_rename_dialog(self, session_id: str, current_name: str):
        """Render simple rename dialog"""
        with st.container():
            st.markdown("**Rename Session**")
            
            new_name = st.text_input(
                "New name:",
                value=current_name,
                key=f"new_name_{session_id}",
                max_chars=100
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✅ Save", key=f"save_rename_{session_id}", use_container_width=True):
                    if new_name.strip() and new_name.strip() != current_name:
                        if self.integration.handle_session_rename(session_id, new_name.strip()):
                            st.success("✅ Renamed!")
                            st.session_state[f'rename_session_{session_id}'] = False
                            st.rerun()
                        else:
                            st.error("❌ Failed to rename")
                    elif not new_name.strip():
                        st.error("❌ Name cannot be empty")
                    else:
                        # No change
                        st.session_state[f'rename_session_{session_id}'] = False
                        st.rerun()
            
            with col2:
                if st.button("❌ Cancel", key=f"cancel_rename_{session_id}", use_container_width=True):
                    st.session_state[f'rename_session_{session_id}'] = False
                    st.rerun()

    
    def _render_simple_delete_confirmation(self, session_id: str, session_name: str):
        """Render simple delete confirmation"""
        with st.container():
            st.markdown("**Delete Session**")
            st.warning(f"Delete **'{session_name}'**?")
            st.markdown("*This action cannot be undone.*")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Red delete button
                st.markdown("""
                <style>
                div[data-testid="stButton"]:has(button[key*="confirm_delete_yes_"]) button {
                    background-color: #dc2626 !important;
                    color: white !important;
                    border: none !important;
                }
                div[data-testid="stButton"]:has(button[key*="confirm_delete_yes_"]) button:hover {
                    background-color: #b91c1c !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                if st.button("🗑️ Delete", key=f"confirm_delete_yes_{session_id}", use_container_width=True):
                    if self.integration.handle_session_delete(session_id):
                        st.success("✅ Deleted!")
                        st.session_state[f'confirm_delete_{session_id}'] = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete")
            
            with col2:
                if st.button("❌ Cancel", key=f"cancel_delete_{session_id}", use_container_width=True):
                    st.session_state[f'confirm_delete_{session_id}'] = False
                    st.rerun()
    
    
    
    def _group_sessions_by_date_enhanced(self, sessions: List[Dict]) -> Dict[str, List[Dict]]:
        """Enhanced session grouping by date with smart categories"""
        grouped = {
            "Today": [],
            "Yesterday": [],
            "This Week": [],
            "Last Week": [],
            "This Month": [],
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
            elif days_diff <= 14:
                grouped["Last Week"].append(session)
            elif days_diff <= 30:
                grouped["This Month"].append(session)
            else:
                grouped["Older"].append(session)
        
        # Remove empty groups and limit older sessions
        result = {}
        for k, v in grouped.items():
            if v:
                if k == "Older" and len(v) > 10:
                    # Limit older sessions to most recent 10
                    v = v[:10]
                    result[k] = v
                    # Add indicator for more sessions
                    result["More..."] = []
                else:
                    result[k] = v
        
        return result
    
    def _create_new_session(self):
        """Prepare for new conversation (ChatGPT/Claude style)"""
        try:
            if self.integration.prepare_new_conversation():
                # Navigate to chat page after preparing new conversation
                st.session_state.current_page = 'chat'
                logger.info("Prepared for new conversation and navigated to chat")
                st.rerun()
            else:
                st.error("❌ Failed to prepare new conversation")
                
        except Exception as e:
            logger.error(f"Failed to prepare new conversation: {e}")
            st.error("❌ Failed to prepare new conversation")
    
    def _switch_to_session(self, session_id: str):
        """Switch to different session with enhanced UX"""
        try:
            if self.integration.handle_session_switch(session_id):
                # Clear any open management dialogs
                st.session_state.show_kb_management = False
                st.session_state.show_zotero_management = False
                st.session_state.show_settings = False
                
                # Clear any open session menus
                for key in list(st.session_state.keys()):
                    if key.startswith('show_session_menu_'):
                        del st.session_state[key]
                
                logger.info(f"Switched to session: {session_id}")
                st.rerun()
            else:
                st.error("❌ Failed to switch session")
                
        except Exception as e:
            logger.error(f"Failed to switch to session {session_id}: {e}")
            st.error("❌ Failed to switch session")
    
    def _export_session(self, session_id: str):
        """Export session with enhanced options"""
        try:
            export_path = Path(f"/tmp/session_{session_id[:8]}_export.json")
            
            if self.session_manager.export_session(session_id, export_path):
                # Offer download
                with open(export_path, 'r') as f:
                    export_data = f.read()
                
                st.download_button(
                    label="📥 Download Export",
                    data=export_data,
                    file_name=f"session_export_{session_id[:8]}.json",
                    mime="application/json",
                    key=f"download_export_{session_id}"
                )
                
                st.success("✅ Export ready for download!")
            else:
                st.error("❌ Failed to export session")
                
        except Exception as e:
            logger.error(f"Failed to export session {session_id}: {e}")
            st.error("❌ Export failed")
    




def render_sidebar_css():
    """Render enhanced CSS for sidebar styling"""
    st.markdown("""
    <style>
    /* ... existing CSS ... */
    
    /* Compact selectbox styling for session menus */
    div[data-testid="stSidebar"] .stSelectbox > div > div {
        background: #f8fafc !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        min-height: 1.8rem !important;
        padding: 0.2rem 0.5rem !important;
        font-size: 0.8rem !important;
    }
    
    div[data-testid="stSidebar"] .stSelectbox > div > div:hover {
        background: #f1f5f9 !important;
        border-color: #cbd5e0 !important;
    }
    
    /* Style the selectbox text - smaller and centered */
    div[data-testid="stSidebar"] .stSelectbox > div > div > div {
        color: #6b7280 !important;
        font-size: 0.8rem !important;
        text-align: center !important;
        line-height: 1.2 !important;
    }
    
    /* Make selectbox dropdown options smaller too */
    div[data-testid="stSidebar"] .stSelectbox > div > div > div > div {
        font-size: 0.8rem !important;
        padding: 0.3rem 0.5rem !important;
    }
    
    /* Adjust session button styling to be more compact */
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key*="session_"]) button {
        padding: 0.6rem !important;
        font-size: 0.85rem !important;
        margin-bottom: 0.25rem !important;
    }
    
    /* ... rest of existing CSS ... */
    </style>
    """, unsafe_allow_html=True)