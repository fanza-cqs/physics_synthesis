# src/ui/enhanced_sidebar.py
"""
Enhanced Sidebar component with full session integration
Replaces the basic sidebar with session-aware functionality
"""

import streamlit as st
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path

from ..sessions import SessionManager
from ..sessions.session_integration import get_session_integration #get_session_integration_safe
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class EnhancedSidebar:
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
        
        # Enhanced status indicators
        self._render_enhanced_status_indicators()
    
    def _render_enhanced_status_indicators(self):
        """Render enhanced status indicators with detailed info"""
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
                st.session_state.show_settings = True
                st.rerun()
        
        # Zotero status
        zotero_status = st.session_state.get('zotero_status', 'unknown')
        if zotero_status == 'connected':
            collections_count = len(st.session_state.get('zotero_collections', []))
            st.markdown(f"**Zotero:** ✅ ({collections_count})")
        elif zotero_status == 'not_configured':
            st.markdown("**Zotero:** ⚙️")
            if st.button("🔧 Setup", key="setup_zotero", help="Setup Zotero integration"):
                st.session_state.show_settings = True
                st.rerun()
        else:
            st.markdown("**Zotero:** ❌")
        
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
            if msg_count > 0 or doc_count > 0:
                st.caption(f"💬 {msg_count} msgs • 📄 {doc_count} docs")
    
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
        """Render enhanced sessions list with better UI"""
        print(f"🔍 DEBUG: _render_enhanced_sessions_list called")
        print(f"🔍 DEBUG: self.integration = {self.integration}")

        # Get current session ID first
        current_session_id = None
        if self.session_manager.current_session:
            current_session_id = self.session_manager.current_session.id

        if self.integration is None:
            print("🔍 DEBUG: Integration is None!")
            # Fallback: use session manager directly
            sessions = self.session_manager.list_sessions()
            st.info("Using basic session list (integration unavailable)")
        else:
            sessions = self.integration.get_session_list_for_ui()
        print(f"🔍 DEBUG: Got {len(sessions)} sessions")
            #current_session = self.session_manager.current_session
            #current_session_id = current_session.id if current_session else None
        
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
            
            for session_meta in group_sessions:
                self._render_enhanced_session_item(session_meta, current_session_id)
    
    def _render_enhanced_session_item(self, session_meta: Dict, current_session_id: Optional[str]):
        """Render enhanced session item with better UX"""
        session_id = session_meta['id']
        session_name = session_meta['name']
        is_current = session_id == current_session_id
        
        # Create container for session item with enhanced styling
        container = st.container()
        
        with container:
            # Session button with enhanced styling
            button_key = f"session_{session_id}"
            button_label = self._format_session_label(session_meta)
            
            # Use different styling for current session
            if is_current:
                # Current session - highlighted
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           color: white; padding: 0.75rem; border-radius: 8px; margin: 0.25rem 0;
                           border-left: 4px solid #4338ca;">
                    <div style="font-weight: 600; font-size: 0.9rem;">{session_name}</div>
                    <div style="font-size: 0.7rem; opacity: 0.9;">{session_meta['context_summary']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                # Regular session - clickable
                if st.button(
                    button_label,
                    key=button_key,
                    help=self._get_enhanced_session_tooltip(session_meta),
                    use_container_width=True
                ):
                    self._switch_to_session(session_id)
            
            # Session options (three dots menu)
            if st.button("⋮", key=f"menu_{session_id}", help="Session options"):
                st.session_state[f'show_session_menu_{session_id}'] = True
                st.rerun()
        
        # Session options menu (if open)
        if st.session_state.get(f'show_session_menu_{session_id}', False):
            self._render_enhanced_session_menu(session_id, session_name, session_meta)
    
    def _render_enhanced_session_menu(self, session_id: str, session_name: str, session_meta: Dict):
        """Render enhanced session options menu"""
        with st.expander(f"⚙️ {session_name[:20]}...", expanded=True):
            # Session info
            st.markdown(f"**Created:** {session_meta['last_active_formatted']}")
            st.markdown(f"**Messages:** {session_meta.get('message_count', 0)}")
            st.markdown(f"**Documents:** {session_meta.get('document_count', 0)}")
            
            if session_meta.get('knowledge_base_name'):
                st.markdown(f"**KB:** {session_meta['knowledge_base_name']}")
            
            st.markdown("---")
            
            # Actions
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✏️ Rename", key=f"rename_{session_id}"):
                    st.session_state[f'rename_session_{session_id}'] = True
                    st.session_state[f'show_session_menu_{session_id}'] = False
                    st.rerun()
                
                if st.button("📤 Export", key=f"export_{session_id}"):
                    self._export_session(session_id)
            
            with col2:
                if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                    st.session_state[f'confirm_delete_{session_id}'] = True
                    st.session_state[f'show_session_menu_{session_id}'] = False
                    st.rerun()
                
                if st.button("📋 Duplicate", key=f"duplicate_{session_id}"):
                    self._duplicate_session(session_id)
            
            # Close menu button
            if st.button("✖️ Close", key=f"close_menu_{session_id}"):
                st.session_state[f'show_session_menu_{session_id}'] = False
                st.rerun()
        
        # Handle rename dialog
        if st.session_state.get(f'rename_session_{session_id}', False):
            self._render_enhanced_rename_dialog(session_id, session_name)
        
        # Handle delete confirmation
        if st.session_state.get(f'confirm_delete_{session_id}', False):
            self._render_enhanced_delete_confirmation(session_id, session_name, session_meta)
    
    def _render_enhanced_rename_dialog(self, session_id: str, current_name: str):
        """Render enhanced session rename dialog"""
        st.markdown("**Rename Session**")
        
        new_name = st.text_input(
            "New name:",
            value=current_name,
            key=f"new_name_{session_id}",
            max_chars=100
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Save", key=f"save_rename_{session_id}"):
                if new_name.strip() and new_name.strip() != current_name:
                    if self.integration.handle_session_rename(session_id, new_name.strip()):
                        st.success("✅ Renamed successfully!")
                        st.session_state[f'rename_session_{session_id}'] = False
                        st.rerun()
                    else:
                        st.error("❌ Failed to rename session")
                elif not new_name.strip():
                    st.error("❌ Name cannot be empty")
                else:
                    # No change
                    st.session_state[f'rename_session_{session_id}'] = False
                    st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_rename_{session_id}"):
                st.session_state[f'rename_session_{session_id}'] = False
                st.rerun()
    
    def _render_enhanced_delete_confirmation(self, session_id: str, session_name: str, session_meta: Dict):
        """Render enhanced session delete confirmation"""
        st.markdown("**Delete Session**")
        st.warning(f"Are you sure you want to delete **'{session_name}'**?")
        
        # Show what will be lost
        items_to_delete = []
        if session_meta.get('message_count', 0) > 0:
            items_to_delete.append(f"{session_meta['message_count']} messages")
        if session_meta.get('document_count', 0) > 0:
            items_to_delete.append(f"{session_meta['document_count']} documents")
        
        if items_to_delete:
            st.markdown(f"**This will delete:** {', '.join(items_to_delete)}")
        
        st.markdown("*This action cannot be undone.*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Delete", key=f"confirm_delete_yes_{session_id}"):
                if self.integration.handle_session_delete(session_id):
                    st.success("✅ Session deleted!")
                    st.session_state[f'confirm_delete_{session_id}'] = False
                    st.rerun()
                else:
                    st.error("❌ Failed to delete session")
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_delete_{session_id}"):
                st.session_state[f'confirm_delete_{session_id}'] = False
                st.rerun()
    
    def _format_session_label(self, session_meta: Dict) -> str:
        """Format session label for button display"""
        name = session_meta['name']
        
        # Truncate long names
        if len(name) > 25:
            name = name[:22] + "..."
        
        return name
    
    def _get_enhanced_session_tooltip(self, session_meta: Dict) -> str:
        """Generate enhanced tooltip for session"""
        parts = []
        
        # Last active
        parts.append(f"Last active: {session_meta['last_active_formatted']}")
        
        # Message count
        msg_count = session_meta.get('message_count', 0)
        if msg_count > 0:
            parts.append(f"{msg_count} messages")
        
        # KB info
        kb_name = session_meta.get('knowledge_base_name')
        if kb_name:
            parts.append(f"KB: {kb_name}")
        else:
            parts.append("Pure chat mode")
        
        # Document count
        doc_count = session_meta.get('document_count', 0)
        if doc_count > 0:
            parts.append(f"{doc_count} documents")
        
        return " • ".join(parts)
    
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
        """Create new session with enhanced UX"""
        try:
            new_session = self.integration.handle_new_session()
            
            if new_session:
                # Clear any open management dialogs
                st.session_state.show_kb_management = False
                st.session_state.show_zotero_management = False
                st.session_state.show_settings = False
                
                logger.info(f"Created new session from sidebar: {new_session.id}")
                st.rerun()
            else:
                st.error("❌ Failed to create new session")
                
        except Exception as e:
            logger.error(f"Failed to create new session: {e}")
            st.error("❌ Failed to create new session")
    
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
    
    def _duplicate_session(self, session_id: str):
        """Duplicate session with enhanced UX"""
        try:
            # Load the session to duplicate
            session_to_duplicate = self.session_manager.storage.load_session(session_id)
            
            if session_to_duplicate:
                # Create new session with similar properties
                new_session = self.session_manager.create_session(
                    name=f"Copy of {session_to_duplicate.name}",
                    knowledge_base_name=session_to_duplicate.knowledge_base_name,
                    auto_activate=False
                )
                
                # Copy settings
                new_session.settings = session_to_duplicate.settings
                
                # Note: We don't copy messages or documents for privacy/storage reasons
                # Add a welcome message explaining this is a copy
                new_session.add_message(
                    "system",
                    f"📋 This is a copy of '{session_to_duplicate.name}'. "
                    f"The knowledge base and settings have been copied, but messages and documents start fresh."
                )
                
                # Save the new session
                self.session_manager.storage.save_session(new_session)
                
                st.success(f"✅ Created copy: {new_session.name}")
                
                # Close menu
                st.session_state[f'show_session_menu_{session_id}'] = False
                st.rerun()
            else:
                st.error("❌ Failed to load session for duplication")
                
        except Exception as e:
            logger.error(f"Failed to duplicate session {session_id}: {e}")
            st.error("❌ Duplication failed")


def render_enhanced_sidebar_css():
    """Render enhanced CSS for sidebar styling"""
    st.markdown("""
    <style>
    /* Enhanced sidebar styling */
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%) !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    
    /* Enhanced navigation buttons */
    div[data-testid="stSidebar"] .stButton > button {
        width: 100% !important;
        height: auto !important;
        background: white !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        color: #374151 !important;
        font-weight: 500 !important;
        text-align: left !important;
        padding: 0.75rem !important;
        margin-bottom: 0.5rem !important;
        transition: all 0.3s ease !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    /* Enhanced hover effects */
    div[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
        border-color: #667eea !important;
        transform: translateX(4px) translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15) !important;
    }
    
    /* Management buttons special styling */
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key*="sidebar_"]) button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
    }
    
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key*="sidebar_"]) button:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
        transform: translateX(4px) translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(102, 126, 234, 0.3) !important;
    }
    
    /* New session button */
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key="new_session"]) button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border: none !important;
        font-size: 1.2rem !important;
        padding: 0.5rem !important;
        font-weight: 700 !important;
    }
    
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key="new_session"]) button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        transform: translateX(2px) translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(16, 185, 129, 0.3) !important;
    }
    
    /* Session options button */
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key*="menu_"]) button {
        background: transparent !important;
        border: 1px solid #d1d5db !important;
        color: #6b7280 !important;
        padding: 0.25rem !important;
        min-height: auto !important;
        height: 2rem !important;
        border-radius: 6px !important;
    }
    
    div[data-testid="stSidebar"] .stButton[data-baseweb="button"]:has(button[key*="menu_"]) button:hover {
        background: #f3f4f6 !important;
        color: #374151 !important;
        border-color: #9ca3af !important;
    }
    
    /* Status indicators */
    div[data-testid="stSidebar"] .stMarkdown h5 {
        color: #6b7280 !important;
        font-size: 0.875rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        margin-bottom: 0.5rem !important;
    }
    
    div[data-testid="stSidebar"] .stMarkdown p {
        margin-bottom: 0.25rem !important;
        font-size: 0.875rem !important;
        line-height: 1.25 !important;
    }
    
    /* Session date group headers */
    div[data-testid="stSidebar"] .stMarkdown h4 {
        color: #4b5563 !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        margin: 1rem 0 0.5rem 0 !important;
        padding-left: 0.5rem !important;
        border-left: 2px solid #e2e8f0 !important;
    }
    
    /* Enhanced expandability */
    div[data-testid="stSidebar"] .stExpander {
        border: 1px solid #e2e8f0 !important;
        border-radius: 8px !important;
        background: white !important;
        margin: 0.25rem 0 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05) !important;
    }
    
    div[data-testid="stSidebar"] .stExpander > div > div > div[data-testid="stExpanderHeader"] {
        background: #f8fafc !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 0.5rem !important;
        font-size: 0.875rem !important;
        font-weight: 500 !important;
    }
    
    div[data-testid="stSidebar"] .stExpander > div > div > div[data-testid="stExpanderContent"] {
        background: white !important;
        border-radius: 0 0 8px 8px !important;
        padding: 0.75rem !important;
    }
    
    /* Enhanced scrollbar for sidebar */
    div[data-testid="stSidebar"]::-webkit-scrollbar {
        width: 8px;
    }
    
    div[data-testid="stSidebar"]::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 4px;
    }
    
    div[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #cbd5e0 0%, #a0aec0 100%);
        border-radius: 4px;
    }
    
    div[data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #a0aec0 0%, #718096 100%);
    }
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        div[data-testid="stSidebar"] .stButton > button {
            padding: 0.5rem !important;
            font-size: 0.875rem !important;
        }
        
        div[data-testid="stSidebar"] .stMarkdown p {
            font-size: 0.8rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)