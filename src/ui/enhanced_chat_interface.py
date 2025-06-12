# src/ui/enhanced_chat_interface.py
"""
Enhanced Chat Interface with full session integration
Replaces the basic chat interface with session-aware functionality
"""

import streamlit as st
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import time

from ..sessions import SessionManager
from ..sessions.session_integration import get_session_integration #_safe
from ..chat import LiteratureAssistant
from ..core import list_knowledge_bases
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class EnhancedChatInterface:
    """
    Enhanced chat interface with full session integration
    Handles all chat functionality with proper session management
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize enhanced chat interface
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
        self.integration = get_session_integration()
        #self.integration = get_session_integration_safe()

    
 

    # Update your main render method to use the integrated bottom bar:
    def render(self):
        """Render the complete enhanced chat interface with integrated bottom bar"""
        if self.integration is None:
            st.error("Session integration not available - using basic mode")
            current_session = self.session_manager.current_session
            if not current_session:
                current_session = self.session_manager.create_session("New Session", auto_activate=True)
        else:
            current_session = self.integration.ensure_current_session()
            self.integration.sync_session_to_streamlit(current_session)
        
        # Simple header - just title and context
        self._render_simple_header(current_session)
        
        # Conversation area
        self._render_conversation(current_session)
        
        # Suggested questions (if no messages)
        if not current_session.has_messages():
            self._render_suggested_questions(current_session)
        
        # Integrated bottom bar with chat input + controls
        self._render_integrated_bottom_bar()
        
        # Handle UI updates
        self._handle_ui_updates()





    def _handle_modal_display(self, session):
        """Handle modal display based on session state - FIXED to only show one dialog at a time"""
        
        # Only show ONE dialog at a time - check in priority order
        if st.session_state.get('show_kb_modal', False):
            self._render_kb_modal_dialog(session)
        elif st.session_state.get('show_upload_modal', False):
            self._render_upload_modal_dialog(session)
        elif st.session_state.get('show_settings_modal', False):
            self._render_settings_modal_dialog(session)
        # If none are set to True, no dialog is shown


    @st.dialog("🧠 Switch Knowledge Base")
    def _render_kb_modal_dialog(self, session):
        """Render knowledge base modal using Streamlit's dialog"""
        
        config = st.session_state.get('config')
        if not config:
            st.error("Configuration not loaded")
            return
        
        # Get available knowledge bases
        available_kbs = list_knowledge_bases(config.knowledge_bases_folder)
        kb_names = [kb['name'] if isinstance(kb, dict) else kb for kb in available_kbs]
        
        # Add "None" option for pure LLM chat
        options = ["None (Pure Chat)"] + kb_names
        
        # Find current selection
        current_kb = session.knowledge_base_name
        if current_kb and current_kb in kb_names:
            current_index = kb_names.index(current_kb) + 1
        else:
            current_index = 0
        
        # KB selector
        selected = st.selectbox(
            "Choose Knowledge Base:",
            options,
            index=current_index,
            key="dialog_kb_selector"
        )
        
        # Show current KB info
        if current_kb:
            st.info(f"Current KB: {current_kb}")
        else:
            st.info("Current Mode: Pure Chat")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Apply", key="apply_kb_dialog", type="primary", use_container_width=True):
                new_kb = None if selected == "None (Pure Chat)" else selected
                
                if new_kb != current_kb:
                    if self.integration.handle_kb_change(new_kb):
                        if new_kb:
                            st.success(f"✅ Switched to: {new_kb}")
                            self.integration.handle_message_add("system", f"📚 Now using knowledge base: {new_kb}")
                        else:
                            st.success("✅ Switched to pure chat mode")
                            self.integration.handle_message_add("system", "💬 Now in pure chat mode")
                        
                        # Clear the modal state
                        st.session_state.active_modal = None
                        st.rerun()
                    else:
                        st.error("❌ Failed to switch KB")
                else:
                    st.info("No change needed")
        
        with col2:
            if st.button("❌ Cancel", key="cancel_kb_dialog", use_container_width=True):
                # Clear the modal state
                st.session_state.active_modal = None
                st.rerun()




    @st.dialog("📎 Upload Documents")
    def _render_upload_modal_dialog(self, session):
        """Render document upload modal using Streamlit's dialog"""
        
        uploaded_files = st.file_uploader(
            "Choose files to upload:",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'tex'],
            key="dialog_file_uploader"
        )
        
        if uploaded_files:
            st.info(f"Ready to upload {len(uploaded_files)} file(s)")
            
            for file in uploaded_files:
                st.text(f"📄 {file.name} ({file.size / 1024:.1f} KB)")
        
        # Show current documents
        if session.documents:
            st.markdown("**Current Documents:**")
            for i, doc in enumerate(session.documents):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"📄 {doc.original_name}")
                    st.caption(f"Size: {doc.file_size / 1024:.1f} KB")
                with col2:
                    if st.button("🗑️", key=f"dialog_remove_{i}", help="Remove"):
                        if self.session_manager.remove_document_from_current(doc.filename):
                            st.success("✅ Removed!")
                            self.integration.handle_message_add("system", f"📎 Removed: {doc.original_name}")
                            st.rerun()
        
        col1, col2 = st.columns(2)
        
        with col1:
            upload_disabled = not uploaded_files
            if st.button("📤 Upload", key="upload_dialog_files", type="primary", use_container_width=True, disabled=upload_disabled):
                if uploaded_files:
                    uploaded_names = self.integration.handle_document_upload(uploaded_files)
                    
                    if uploaded_names:
                        st.success(f"✅ Added {len(uploaded_names)} document(s)")
                        doc_list = ", ".join(uploaded_names)
                        self.integration.handle_message_add("system", f"📎 Added documents: {doc_list}")
                        # Clear the modal state
                        st.session_state.active_modal = None
                        st.rerun()
                    else:
                        st.error("❌ Upload failed")
        
        with col2:
            if st.button("❌ Cancel", key="cancel_upload_dialog", use_container_width=True):
                # Clear the modal state
                st.session_state.active_modal = None
                st.rerun()


    



    @st.dialog("⚙️ Chat Settings")
    def _render_settings_modal_dialog(self, session):
        """Render chat settings modal using Streamlit's dialog"""
        
        st.markdown("Adjust your chat preferences:")
        
        # Temperature
        temperature = st.slider(
            "🌡️ Creativity Level",
            0.0, 1.0,
            value=session.settings.temperature,
            step=0.1,
            key="dialog_temperature",
            help="Higher values make responses more creative and varied"
        )
        
        # Max sources
        max_sources = st.slider(
            "📄 Maximum Sources",
            1, 20,
            value=session.settings.max_sources,
            key="dialog_max_sources",
            help="Maximum number of knowledge base sources to use per response"
        )
        
        # Response style
        style_options = ["detailed", "concise", "technical"]
        current_style_index = style_options.index(session.settings.response_style) if session.settings.response_style in style_options else 0
        
        response_style = st.selectbox(
            "📝 Response Style",
            style_options,
            index=current_style_index,
            key="dialog_response_style",
            help="Preferred style for AI responses"
        )
        
        # Show current settings
        st.markdown("**Current Settings:**")
        st.info(f"Temperature: {session.settings.temperature} | Max Sources: {session.settings.max_sources} | Style: {session.settings.response_style}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("✅ Apply", key="apply_settings_dialog", type="primary", use_container_width=True):
                self.session_manager.update_current_session_settings(
                    temperature=temperature,
                    max_sources=max_sources,
                    response_style=response_style
                )
                st.success("✅ Settings updated!")
                # Clear the modal state
                st.session_state.active_modal = None
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Chat", key="clear_chat_dialog", type="secondary", use_container_width=True):
                if self.integration.handle_clear_conversation():
                    st.success("✅ Chat cleared!")
                    # Clear the modal state
                    st.session_state.active_modal = None
                    st.rerun()
                else:
                    st.error("❌ Failed to clear chat")
        
        with col3:
            if st.button("❌ Cancel", key="cancel_settings_dialog", use_container_width=True):
                # Clear the modal state
                st.session_state.active_modal = None
                st.rerun()




    def _render_simple_header(self, session):
        """Render simple header with just title and context"""
        if session.name != "New Session":
            st.markdown(f"### 💬 {session.name}")
        else:
            st.markdown("### 💬 Research Assistant")
        
        # Show current context in a compact way
        context_parts = []
        
        if session.knowledge_base_name:
            context_parts.append(f"**KB:** {session.knowledge_base_name}")
        else:
            context_parts.append("**Mode:** Pure Chat")
        
        if session.documents:
            context_parts.append(f"**Docs:** {len(session.documents)}")
        
        user_messages = len([m for m in session.messages if m.role == "user"])
        if user_messages > 0:
            context_parts.append(f"**Messages:** {user_messages}")
        
        if context_parts:
            context_text = " • ".join(context_parts)
            st.info(context_text)

    def _render_integrated_bottom_bar(self):
        """Render integrated bottom bar with chat input and control buttons - IMPROVED"""
        session_id = st.session_state.get('current_session_id', 'default')
        current_session = self.session_manager.current_session
        
        # Create the integrated bottom container
        st.markdown('<div class="integrated-bottom-bar">', unsafe_allow_html=True)
        
        # Use columns for layout: chat input + control buttons
        col_input, col_controls = st.columns([4, 1])
        
        with col_input:
            # The chat input (Streamlit will make this sticky)
            if prompt := st.chat_input("Ask about your research...", key=f"integrated_chat_input_{session_id}"):
                self._process_user_message(prompt)
        
        with col_controls:
            # Control buttons in a row
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if st.button("🧠", key="integrated_kb_btn", help="Switch Knowledge Base"):
                    st.session_state.active_modal = "kb"
                    st.rerun()
            
            with btn_col2:
                if st.button("📎", key="integrated_upload_btn", help="Upload Documents"):
                    st.session_state.active_modal = "upload" 
                    st.rerun()
            
            with btn_col3:
                if st.button("⚙️", key="integrated_settings_btn", help="Chat Settings"):
                    st.session_state.active_modal = "settings"
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle modals - IMPROVED approach
        self._handle_single_modal_display(current_session)


    def _handle_single_modal_display(self, session):
        """Handle single modal display based on active_modal state"""
        
        active_modal = st.session_state.get('active_modal', None)
        
        if active_modal == "kb":
            self._render_kb_modal_dialog(session)
        elif active_modal == "upload":
            self._render_upload_modal_dialog(session)
        elif active_modal == "settings":
            self._render_settings_modal_dialog(session)




    
    def _render_chat_header(self, session):
        """Render minimal chat header - just title and context"""
        # Simple title
        if session.name != "New Session":
            st.markdown(f"### 💬 {session.name}")
        else:
            st.markdown("### 💬 Research Assistant")
        
        # Just show current context - no controls
        self._render_minimal_context(session)
    



    def _render_kb_selector(self, session):
        """Render enhanced knowledge base selector"""
        config = st.session_state.get('config')
        if not config:
            st.warning("⚠️ Configuration not loaded")
            return
        
        # Get available knowledge bases
        available_kbs = list_knowledge_bases(config.knowledge_bases_folder)
        kb_names = [kb['name'] if isinstance(kb, dict) else kb for kb in available_kbs]
        
        # Add "None" option for pure LLM chat
        options = ["None (Pure Chat)"] + kb_names
        
        # Find current selection
        current_kb = session.knowledge_base_name
        if current_kb and current_kb in kb_names:
            current_index = kb_names.index(current_kb) + 1
        else:
            current_index = 0
        
        # KB selector with change detection
        selected = st.selectbox(
            "Knowledge Base:",
            options,
            index=current_index,
            key=f"kb_selector_{session.id}",
            help="Choose a knowledge base or use pure chat mode"
        )
        
        # Handle KB change
        new_kb = None if selected == "None (Pure Chat)" else selected
        
        if new_kb != current_kb:
            if self.integration.handle_kb_change(new_kb):
                if new_kb:
                    st.success(f"✅ Switched to knowledge base: {new_kb}")
                    # Add system message about KB change
                    self.integration.handle_message_add(
                        "system", 
                        f"📚 Now using knowledge base: {new_kb}"
                    )
                else:
                    st.info("💬 Switched to pure chat mode")
                    # Add system message about pure chat
                    self.integration.handle_message_add(
                        "system", 
                        "💬 Now in pure chat mode (no knowledge base)"
                    )
                st.rerun()
            else:
                st.error("Failed to switch knowledge base")
    
    def _render_document_upload(self):
        """Render enhanced document upload interface"""
        uploaded_files = st.file_uploader(
            "Upload Documents:",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'tex'],
            key=f"doc_uploader_{st.session_state.get('current_session_id', 'default')}",
            help="Upload documents to this conversation"
        )
        
        if uploaded_files:
            uploaded_names = self.integration.handle_document_upload(uploaded_files)
            
            if uploaded_names:
                st.success(f"✅ Added {len(uploaded_names)} document(s) to conversation")
                
                # Add system message about document upload
                doc_list = ", ".join(uploaded_names)
                self.integration.handle_message_add(
                    "system",
                    f"📎 Added documents: {doc_list}"
                )
                
                st.rerun()
            else:
                st.error("Failed to upload documents")
    
    def _render_chat_settings(self, session):
        """Render enhanced chat settings"""
        with st.expander("⚙️", expanded=False):
            st.markdown("**Chat Settings**")
            
            # Temperature with session sync
            temperature = st.slider(
                "🌡️ Creativity",
                0.0, 1.0,
                value=session.settings.temperature,
                step=0.1,
                key=f"temperature_{session.id}",
                help="Higher values make responses more creative"
            )
            
            # Max sources with session sync
            max_sources = st.slider(
                "📄 Max Sources",
                1, 20,
                value=session.settings.max_sources,
                key=f"max_sources_{session.id}",
                help="Maximum number of sources to use"
            )
            
            # Response style
            style_options = ["detailed", "concise", "technical"]
            current_style_index = style_options.index(session.settings.response_style) if session.settings.response_style in style_options else 0
            
            response_style = st.selectbox(
                "📝 Response Style",
                style_options,
                index=current_style_index,
                key=f"style_{session.id}",
                help="Preferred response style"
            )
            
            # Update session settings if changed
            if (temperature != session.settings.temperature or
                max_sources != session.settings.max_sources or
                response_style != session.settings.response_style):
                
                self.session_manager.update_current_session_settings(
                    temperature=temperature,
                    max_sources=max_sources,
                    response_style=response_style
                )
                
                # Update Streamlit state
                st.session_state.chat_temperature = temperature
                st.session_state.chat_max_sources = max_sources
            
            # Action buttons
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🗑️ Clear Chat", key=f"clear_{session.id}"):
                    if self.integration.handle_clear_conversation():
                        st.success("Conversation cleared!")
                        st.rerun()
                    else:
                        st.error("Failed to clear conversation")
            
            with col2:
                if st.button("📤 Export", key=f"chat_export_{session.id}"):
                    self._export_conversation(session)
    
    def _render_session_context(self, session):
        """Render enhanced session context display"""
        context_parts = []
        
        # Knowledge base info
        if session.knowledge_base_name:
            context_parts.append(f"**KB:** {session.knowledge_base_name}")
        else:
            context_parts.append("**Mode:** Pure Chat")
        
        # Document count
        if session.documents:
            context_parts.append(f"**Documents:** {len(session.documents)}")
        
        # Message count
        if session.messages:
            user_messages = len([m for m in session.messages if m.role == "user"])
            context_parts.append(f"**Messages:** {user_messages}")
        
        if context_parts:
            context_text = " • ".join(context_parts)
            st.info(context_text)
        
        # Document management (if documents exist)
        if session.documents:
            self._render_document_management(session)
    
    def _render_document_management(self, session):
        """Render enhanced document management"""
        with st.expander(f"📎 Manage Documents ({len(session.documents)})", expanded=False):
            for doc in session.documents:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"📄 **{doc.original_name}**")
                    st.caption(f"Uploaded: {doc.upload_timestamp.strftime('%m/%d/%Y %I:%M %p')}")
                
                with col2:
                    file_size_mb = doc.file_size / (1024 * 1024)
                    st.caption(f"{file_size_mb:.2f} MB")
                    st.caption(doc.file_type.upper())
                
                with col3:
                    if st.button("🗑️", key=f"remove_doc_{doc.filename}", help="Remove document"):
                        if self.session_manager.remove_document_from_current(doc.filename):
                            st.success("Document removed!")
                            
                            # Add system message about document removal
                            self.integration.handle_message_add(
                                "system",
                                f"📎 Removed document: {doc.original_name}"
                            )
                            
                            st.rerun()
                        else:
                            st.error("Failed to remove document")
    
    def _render_conversation(self, session):
        """Render enhanced conversation with proper message handling"""
        messages = session.messages
        
        for i, message in enumerate(messages):
            # Skip system messages in main display (they're shown as notifications)
            if message.role == "system":
                continue
                
            with st.chat_message(message.role):
                st.write(message.content)
                
                # Show sources for assistant messages
                if message.role == "assistant" and message.sources:
                    sources_text = ", ".join(message.sources[:3])
                    if len(message.sources) > 3:
                        sources_text += f" and {len(message.sources) - 3} more"
                    st.caption(f"📚 Sources: {sources_text}")
                
                # Show timestamp for older messages
                if i < len(messages) - 2:  # Not one of the last 2 messages
                    st.caption(f"🕐 {message.timestamp.strftime('%I:%M %p')}")
    
    def _render_suggested_questions(self, session):
        """Render contextual suggested questions"""
        st.markdown("### 💡 Get started with these questions:")
        
        suggestions = self._get_contextual_suggestions(session)
        
        # Display suggestions in columns
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"❓ {suggestion}", key=f"suggestion_{session.id}_{i}"):
                    self._process_user_message(suggestion)
    
    def _render_minimal_context(self, session):
        """Show minimal context info"""
        context_parts = []
        
        # Knowledge base info
        if session.knowledge_base_name:
            context_parts.append(f"**KB:** {session.knowledge_base_name}")
        else:
            context_parts.append("**Mode:** Pure Chat")
        
        # Document and message count
        if session.documents:
            context_parts.append(f"**Docs:** {len(session.documents)}")
        
        user_messages = len([m for m in session.messages if m.role == "user"])
        if user_messages > 0:
            context_parts.append(f"**Messages:** {user_messages}")
        
        if context_parts:
            context_text = " • ".join(context_parts)
            st.info(context_text)

    


    def _render_chat_input(self):
        """Render enhanced chat input with inline controls"""
        # Create columns for the input area
        col1, col2 = st.columns([4, 1])
        
        with col1:
            # Main chat input
            session_id = st.session_state.get('current_session_id', 'default')
            prompt = st.chat_input("Ask about your research...", key=f"chat_input_{session_id}")
            
            if prompt:
                self._process_user_message(prompt)
        
        with col2:
            # Inline control buttons
            self._render_inline_controls()


    def _render_inline_controls(self):
        """Render inline control buttons next to chat input"""
        # Get current session for context
        current_session = self.session_manager.current_session
        
        # Knowledge Base Quick Switcher
        with st.popover("🧠", help="Switch Knowledge Base"):
            self._render_kb_quick_switcher(current_session)
        
        # Document Upload
        with st.popover("📎", help="Upload Documents"):
            self._render_document_quick_upload(current_session)
        
        # Settings
        with st.popover("⚙️", help="Chat Settings"):
            self._render_chat_quick_settings(current_session)


    def _render_chat_quick_settings(self, session):
        """Quick chat settings in popover"""
        st.markdown("**Chat Settings**")
        
        # Temperature
        temperature = st.slider(
            "🌡️ Creativity",
            0.0, 1.0,
            value=session.settings.temperature,
            step=0.1,
            key=f"quick_temp_{session.id}"
        )
        
        # Max sources
        max_sources = st.slider(
            "📄 Max Sources",
            1, 20,
            value=session.settings.max_sources,
            key=f"quick_sources_{session.id}"
        )
        
        # Response style
        style_options = ["detailed", "concise", "technical"]
        current_style_index = style_options.index(session.settings.response_style) if session.settings.response_style in style_options else 0
        
        response_style = st.selectbox(
            "📝 Style",
            style_options,
            index=current_style_index,
            key=f"quick_style_{session.id}"
        )
        
        # Apply settings
        if st.button("✅ Apply Settings", key=f"apply_settings_{session.id}", use_container_width=True):
            self.session_manager.update_current_session_settings(
                temperature=temperature,
                max_sources=max_sources,
                response_style=response_style
            )
            st.success("✅ Settings updated!")
            st.rerun()
        
        # Clear conversation
        st.markdown("---")
        if st.button("🗑️ Clear Chat", key=f"quick_clear_{session.id}", type="secondary", use_container_width=True):
            if self.integration.handle_clear_conversation():
                st.success("✅ Chat cleared!")
                st.rerun()



    def _render_document_quick_upload(self, session):
        """Quick document upload in popover"""
        st.markdown("**Upload Documents**")
        
        uploaded_files = st.file_uploader(
            "Choose files:",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'tex'],
            key=f"quick_uploader_{session.id}",
            label_visibility="collapsed"
        )
        
        if uploaded_files:
            if st.button("📤 Upload", key=f"quick_upload_{session.id}", use_container_width=True):
                uploaded_names = self.integration.handle_document_upload(uploaded_files)
                
                if uploaded_names:
                    st.success(f"✅ Added {len(uploaded_names)} document(s)")
                    doc_list = ", ".join(uploaded_names)
                    self.integration.handle_message_add("system", f"📎 Added documents: {doc_list}")
                    st.rerun()
                else:
                    st.error("❌ Upload failed")
        
        # Show current documents
        if session.documents:
            st.markdown("**Current Documents:**")
            for doc in session.documents[-3:]:  # Show last 3
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"📄 {doc.original_name}")
                with col2:
                    if st.button("🗑️", key=f"quick_remove_{doc.filename}", help="Remove"):
                        if self.session_manager.remove_document_from_current(doc.filename):
                            st.success("✅ Removed!")
                            self.integration.handle_message_add("system", f"📎 Removed: {doc.original_name}")
                            st.rerun()
            
            if len(session.documents) > 3:
                st.caption(f"... and {len(session.documents) - 3} more")



    def _render_kb_quick_switcher(self, session):
        """Quick KB switcher in popover"""
        st.markdown("**Switch Knowledge Base**")
        
        config = st.session_state.get('config')
        if not config:
            st.warning("⚠️ Configuration not loaded")
            return
        
        # Get available knowledge bases
        available_kbs = list_knowledge_bases(config.knowledge_bases_folder)
        kb_names = [kb['name'] if isinstance(kb, dict) else kb for kb in available_kbs]
        
        # Add "None" option for pure LLM chat
        options = ["None (Pure Chat)"] + kb_names
        
        # Find current selection
        current_kb = session.knowledge_base_name
        if current_kb and current_kb in kb_names:
            current_index = kb_names.index(current_kb) + 1
        else:
            current_index = 0
        
        # KB selector
        selected = st.selectbox(
            "Choose KB:",
            options,
            index=current_index,
            key=f"kb_quick_selector_{session.id}",
            label_visibility="collapsed"
        )
        
        # Apply button
        if st.button("✅ Apply KB Change", key=f"apply_kb_{session.id}", use_container_width=True):
            new_kb = None if selected == "None (Pure Chat)" else selected
            
            if new_kb != current_kb:
                if self.integration.handle_kb_change(new_kb):
                    if new_kb:
                        st.success(f"✅ Switched to: {new_kb}")
                        self.integration.handle_message_add("system", f"📚 Now using knowledge base: {new_kb}")
                    else:
                        st.success("✅ Switched to pure chat mode")
                        self.integration.handle_message_add("system", "💬 Now in pure chat mode")
                    st.rerun()
                else:
                    st.error("❌ Failed to switch KB")


    
    def _get_contextual_suggestions(self, session) -> List[str]:
        """Get enhanced contextual suggestions"""
        if not session.knowledge_base_name:
            # Pure chat mode suggestions
            return [
                "Explain quantum entanglement in simple terms",
                "What are the key principles of machine learning?",
                "Help me understand statistical mechanics",
                "Explain the difference between classical and quantum computing",
                "What are the main branches of physics?",
                "Help me write a research proposal outline"
            ]
        elif session.documents:
            # Has uploaded documents
            return [
                "Summarize the uploaded documents",
                "What are the key findings in these papers?",
                "Compare the methodologies in my documents",
                "Help me find connections between these papers",
                "What questions do these papers raise?",
                "Help me write a literature review based on these documents"
            ]
        else:
            # Has KB but no uploaded docs
            return [
                "What papers do I have about quantum computing?",
                "Summarize the main themes in my research",
                "Who are the most cited authors in my collection?",
                "Help me write an introduction for my paper",
                "What are recent developments in my field?",
                "Find papers related to machine learning"
            ]
    
    def _process_user_message(self, message: str):
        """Process user message with enhanced session handling"""
        # Add user message to session
        if not self.integration.handle_message_add("user", message):
            st.error("Failed to save message")
            return
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(message)
        
        # Get and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    current_session = self.session_manager.current_session
                    response_content, sources = self._get_ai_response(message, current_session)
                    
                    # Display response
                    st.write(response_content)
                    
                    # Display sources if any
                    if sources:
                        sources_text = ", ".join(sources[:3])
                        if len(sources) > 3:
                            sources_text += f" and {len(sources) - 3} more"
                        st.caption(f"📚 Sources: {sources_text}")
                    
                    # Add assistant message to session
                    if not self.integration.handle_message_add("assistant", response_content, sources):
                        st.error("Failed to save response")
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    
                    # Add error message to session
                    self.integration.handle_message_add("assistant", error_msg)
        
        # Rerun to update the conversation display
        st.rerun()
    
    def _get_ai_response(self, message: str, session) -> Tuple[str, List[str]]:
        """Get AI response with enhanced error handling"""
        config = st.session_state.get('config')
        if not config:
            raise RuntimeError("Configuration not available")
        
        if not config.anthropic_api_key:
            raise RuntimeError("Anthropic API key not configured. Please add it in Settings.")
        
        # Pure chat mode (no KB)
        if not session.knowledge_base_name:
            return self._get_pure_chat_response(message, session, config)
        
        # KB-assisted chat mode
        return self._get_kb_assisted_response(message, session, config)
    
    def _get_pure_chat_response(self, message: str, session, config) -> Tuple[str, List[str]]:
        """Get response in pure chat mode with conversation context"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            
            # Build conversation history for context (last 10 messages)
            messages = []
            recent_messages = [m for m in session.messages[-20:] if m.role in ["user", "assistant"]]
            
            for msg in recent_messages:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Enhanced system prompt for physics research
            system_prompt = """You are a helpful physics research assistant with expertise in theoretical and experimental physics, mathematics, and scientific research methodology. 

You provide clear, accurate, and insightful responses about:
- Physics concepts at all levels (undergraduate to research-level)
- Research methodology and scientific writing
- Mathematical foundations of physics
- Current developments in physics research
- Academic and career guidance for physicists

Maintain a professional yet approachable tone. When explaining complex concepts, provide intuitive explanations alongside technical details. Always cite relevant principles, equations, or phenomena when appropriate."""
            
            # Create response
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=session.settings.temperature,
                messages=messages,
                system=system_prompt
            )
            
            return response.content[0].text, []
            
        except Exception as e:
            logger.error(f"Pure chat response failed: {e}")
            raise RuntimeError(f"Failed to get AI response: {str(e)}")
    
    def _get_kb_assisted_response(self, message: str, session, config) -> Tuple[str, List[str]]:
        """Get response with knowledge base assistance"""
        try:
            # Load knowledge base
            from ..core import load_knowledge_base
            
            kb = load_knowledge_base(session.knowledge_base_name, config.knowledge_bases_folder)
            if not kb:
                raise RuntimeError(f"Knowledge base '{session.knowledge_base_name}' not found or corrupted")
            
            # Create literature assistant
            assistant = LiteratureAssistant(kb, config.anthropic_api_key, config.get_chat_config())
            
            # Get response with session settings
            response = assistant.ask(
                message,
                temperature=session.settings.temperature,
                max_context_chunks=session.settings.max_sources
            )
            
            return response.content, response.sources_used
            
        except Exception as e:
            logger.error(f"KB-assisted response failed: {e}")
            raise RuntimeError(f"Failed to get KB-assisted response: {str(e)}")
    
    def _export_conversation(self, session):
        """Export conversation to downloadable format"""
        try:
            # Create export content
            export_lines = [
                f"# Conversation Export: {session.name}",
                f"**Session ID:** {session.id}",
                f"**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
                f"**Knowledge Base:** {session.knowledge_base_name or 'None (Pure Chat)'}",
                f"**Documents:** {len(session.documents)}",
                "",
                "## Conversation",
                ""
            ]
            
            # Add messages
            for message in session.messages:
                if message.role == "system":
                    continue
                    
                role_icon = "👤" if message.role == "user" else "🤖"
                export_lines.append(f"### {role_icon} {message.role.title()}")
                export_lines.append(f"*{message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*")
                export_lines.append("")
                export_lines.append(message.content)
                
                if message.role == "assistant" and message.sources:
                    export_lines.append("")
                    export_lines.append("**Sources:**")
                    for source in message.sources:
                        export_lines.append(f"- {source}")
                
                export_lines.append("")
                export_lines.append("---")
                export_lines.append("")
            
            # Add document info if any
            if session.documents:
                export_lines.extend([
                    "## Documents in this Conversation",
                    ""
                ])
                
                for doc in session.documents:
                    export_lines.extend([
                        f"- **{doc.original_name}**",
                        f"  - Size: {doc.file_size / (1024*1024):.2f} MB",
                        f"  - Type: {doc.file_type}",
                        f"  - Uploaded: {doc.upload_timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                        ""
                    ])
            
            export_content = "\n".join(export_lines)
            
            # Offer download
            st.download_button(
                label="📥 Download Conversation",
                data=export_content,
                file_name=f"{session.name.replace(' ', '_')}_{session.id[:8]}.md",
                mime="text/markdown",
                help="Download conversation as Markdown file"
            )
            
        except Exception as e:
            logger.error(f"Failed to export conversation: {e}")
            st.error("Failed to export conversation")
    
    def _handle_ui_updates(self):
        """Handle any pending UI updates or notifications"""
        # Handle success messages from session operations
        if st.session_state.get('show_kb_change_success'):
            st.success(st.session_state.show_kb_change_success)
            del st.session_state.show_kb_change_success
        
        if st.session_state.get('show_doc_upload_success'):
            st.success(st.session_state.show_doc_upload_success)
            del st.session_state.show_doc_upload_success
        
        # Handle error messages
        if st.session_state.get('show_error_message'):
            st.error(st.session_state.show_error_message)
            del st.session_state.show_error_message
        
        # Auto-save session periodically
        current_session = self.session_manager.current_session
        if current_session:
            # Sync any pending Streamlit state changes
            self.integration.sync_streamlit_to_session(current_session)
            
            # Save if there have been recent changes
            last_save = st.session_state.get('last_session_save', 0)
            current_time = time.time()
            
            if current_time - last_save > 30:  # Auto-save every 30 seconds
                self.session_manager.save_current_session()
                st.session_state.last_session_save = current_time


# Replace your render_enhanced_chat_css() with this:

# Replace your render_enhanced_chat_css() with this:

def render_enhanced_chat_css():
    """Render enhanced CSS for integrated bottom bar with chat input + controls"""
    st.markdown("""
    <style>
    /* INTEGRATED BOTTOM BAR - Force sticky positioning */
    
    .integrated-bottom-bar {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        z-index: 1000 !important;
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(8px) !important;
        padding: 1rem !important;
        border-top: 2px solid #e2e8f0 !important;
        box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1) !important;
        border-radius: 16px 16px 0 0 !important;
    }
    
    /* Override Streamlit's default chat input positioning */
    .integrated-bottom-bar .stChatInput {
        position: relative !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Style the chat input within our container */
    .integrated-bottom-bar .stChatInput > div {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        background: white !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        transition: all 0.3s ease !important;
        margin: 0 !important;
    }
    
    .integrated-bottom-bar .stChatInput > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2) !important;
        transform: translateY(-1px) !important;
    }
    
    /* Style the control buttons */
    .integrated-bottom-bar .stButton > button {
        width: 48px !important;
        height: 48px !important;
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        font-size: 1.3rem !important;
        padding: 0 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.3s ease !important;
        margin: 0 !important;
        min-width: 48px !important;
        background: white !important;
        color: #6b7280 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    }
    
    .integrated-bottom-bar .stButton > button:hover {
        transform: translateY(-2px) scale(1.05) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
        border-color: #667eea !important;
    }
    
    /* Individual button colors on hover */
    .integrated-bottom-bar div[data-testid="column"]:nth-child(1) .stButton > button:hover {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        color: white !important;
        border-color: #10b981 !important;
    }
    
    .integrated-bottom-bar div[data-testid="column"]:nth-child(2) .stButton > button:hover {
        background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%) !important;
        color: white !important;
        border-color: #f59e0b !important;
    }
    
    .integrated-bottom-bar div[data-testid="column"]:nth-child(3) .stButton > button:hover {
        background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%) !important;
        color: white !important;
        border-color: #6b7280 !important;
    }
    
    /* Ensure proper spacing between input and buttons */
    .integrated-bottom-bar div[data-testid="column"] {
        padding: 0 0.25rem !important;
    }
    
    .integrated-bottom-bar div[data-testid="column"]:first-child {
        padding-right: 1rem !important;
    }
    
    /* Make sure buttons align vertically with input */
    .integrated-bottom-bar div[data-testid="column"]:last-child {
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 0.5rem;
    }
    
    /* Adjust main content to account for sticky bottom bar */
    .main .block-container {
        padding-bottom: 120px; /* Space for the sticky bar */
    }
    
    /* DIALOG STYLING (same as before) */
    div[data-testid="stModal"] {
        background: rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(4px) !important;
    }
    
    div[data-testid="stModal"] > div {
        background: white !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        max-width: 500px !important;
        width: 90vw !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
        animation: modalSlideIn 0.3s ease-out !important;
    }
    
    @keyframes modalSlideIn {
        from {
            opacity: 0;
            transform: scale(0.9) translateY(-20px);
        }
        to {
            opacity: 1;
            transform: scale(1) translateY(0);
        }
    }
    
    /* Dialog buttons */
    div[data-testid="stModal"] .stButton > button {
        border-radius: 8px !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        padding: 0.6rem 1.2rem !important;
    }
    
    div[data-testid="stModal"] .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
    }
    
    div[data-testid="stModal"] .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #5a67d8 0%, #6b46c1 100%) !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* ENHANCED CHAT STYLING */
    .stChatMessage {
        margin-bottom: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stChatMessage[data-testid="user"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .stChatMessage[data-testid="assistant"] {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 1px solid #d1d5db;
    }
    
    /* Context display */
    .stInfo {
        background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
        border: 1px solid #0288d1;
        color: #01579b;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Suggestion buttons */
    .suggestion-button {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
        text-align: left;
        width: 100%;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    .suggestion-button:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
        border: 1px solid #10b981;
        color: #065f46;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .stError {
        background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        border: 1px solid #ef4444;
        color: #991b1b;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .integrated-bottom-bar {
            padding: 0.75rem;
        }
        
        .integrated-bottom-bar .stButton > button {
            width: 42px !important;
            height: 42px !important;
            font-size: 1.1rem !important;
        }
        
        .main .block-container {
            padding-bottom: 100px;
        }
        
        div[data-testid="stModal"] > div {
            padding: 1.5rem !important;
            margin: 1rem !important;
        }
    }
    
    /* Animation for the bottom bar */
    .integrated-bottom-bar {
        animation: slideUpIn 0.3s ease-out;
    }
    
    @keyframes slideUpIn {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    </style>
    """, unsafe_allow_html=True)