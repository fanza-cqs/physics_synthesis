# src/ui/chat_interface.py
"""
Unified Chat Interface for Physics Literature Synthesis Pipeline
Combines the best features from both interfaces with optimized architecture
"""

import streamlit as st
from typing import List, Tuple, Optional
import time
from pathlib import Path

from ..sessions import SessionManager
from ..sessions.session_integration import get_session_integration
from ..chat import LiteratureAssistant
from ..core import list_knowledge_bases
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ChatInterface:
    """
    Unified chat interface with session integration and modern UI patterns
    """
    
    def __init__(self, session_manager: SessionManager):
        self.session_manager = session_manager
        self.integration = get_session_integration()
    
    def render(self):
        """Render the complete chat interface"""
        # Ensure current session exists
        current_session = self._ensure_current_session()
        
        # Simple header with context
        self._render_header(current_session)
        
        # Conversation area
        self._render_conversation(current_session)
        
        # Suggested questions for empty sessions
        if not current_session.has_messages():
            self._render_suggested_questions()
        
        # Integrated bottom bar (sticky chat input + controls)
        self._render_integrated_bottom_bar()
        
        # Handle UI updates and auto-save
        self._handle_ui_updates()
    
    def _ensure_current_session(self):
        """Ensure we have a current session, using integration if available"""
        if self.integration:
            return self.integration.ensure_current_session()
        else:
            # Fallback to direct session manager
            return self.session_manager.get_or_create_default_session()
    
    def _render_header(self, session):
        """Render simple header with context info"""
        if session.name != "New Session":
            st.markdown(f"### 💬 {session.name}")
        else:
            st.markdown("### 💬 Research Assistant")
        
        # Compact context display
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
            st.info(" • ".join(context_parts))
    
    def _render_conversation(self, session):
        """Render conversation messages"""
        for i, message in enumerate(session.messages):
            if message.role == "system":
                continue  # Skip system messages in main display
                
            with st.chat_message(message.role):
                st.write(message.content)
                
                # Show sources for assistant messages
                if message.role == "assistant" and message.sources:
                    sources_text = ", ".join(message.sources[:3])
                    if len(message.sources) > 3:
                        sources_text += f" and {len(message.sources) - 3} more"
                    st.caption(f"📚 Sources: {sources_text}")
                
                # Show timestamp for older messages
                if i < len(session.messages) - 2:
                    st.caption(f"🕐 {message.timestamp.strftime('%I:%M %p')}")
    
    def _render_suggested_questions(self):
        """Render contextual suggested questions"""
        st.markdown("### 💡 Get started with these questions:")
        
        current_session = self.session_manager.current_session
        suggestions = self._get_contextual_suggestions(current_session)
        
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"❓ {suggestion}", key=f"suggestion_{i}"):
                    self._process_user_message(suggestion)
    
    def _render_integrated_bottom_bar(self):
        """Render integrated bottom bar with chat input + controls"""
        session_id = st.session_state.get('current_session_id', 'default')
        current_session = self.session_manager.current_session
        
        # Create integrated bottom container
        st.markdown('<div class="integrated-bottom-bar">', unsafe_allow_html=True)
        
        # Layout: chat input + control buttons
        col_input, col_controls = st.columns([4, 1])
        
        with col_input:
            if prompt := st.chat_input("Ask about your research...", key=f"chat_input_{session_id}"):
                self._process_user_message(prompt)
        
        with col_controls:
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            
            with btn_col1:
                if st.button("🧠", key="kb_btn", help="Switch Knowledge Base"):
                    st.session_state.active_modal = "kb"
                    st.rerun()
            
            with btn_col2:
                if st.button("📎", key="upload_btn", help="Upload Documents"):
                    st.session_state.active_modal = "upload"
                    st.rerun()
            
            with btn_col3:
                if st.button("⚙️", key="settings_btn", help="Chat Settings"):
                    st.session_state.active_modal = "settings"
                    st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle modals
        self._handle_modals(current_session)
    
    # Modern Modal System using @st.dialog
    @st.dialog("🧠 Switch Knowledge Base")
    def _render_kb_modal(self, session):
        """Render KB selection modal"""
        config = st.session_state.get('config')
        if not config:
            st.error("Configuration not loaded")
            return
        
        available_kbs = list_knowledge_bases(config.knowledge_bases_folder)
        kb_names = [kb['name'] if isinstance(kb, dict) else kb for kb in available_kbs]
        options = ["None (Pure Chat)"] + kb_names
        
        current_kb = session.knowledge_base_name
        current_index = kb_names.index(current_kb) + 1 if current_kb and current_kb in kb_names else 0
        
        selected = st.selectbox("Choose Knowledge Base:", options, index=current_index)
        
        if current_kb:
            st.info(f"Current KB: {current_kb}")
        else:
            st.info("Current Mode: Pure Chat")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Apply", type="primary", use_container_width=True):
                new_kb = None if selected == "None (Pure Chat)" else selected
                if self._handle_kb_change(new_kb):
                    st.success(f"✅ Switched to: {new_kb or 'Pure Chat'}")
                    st.session_state.active_modal = None
                    st.rerun()
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.active_modal = None
                st.rerun()
    
    @st.dialog("📎 Upload Documents")
    def _render_upload_modal(self, session):
        """Render document upload modal"""
        uploaded_files = st.file_uploader(
            "Choose files to upload:",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'tex']
        )
        
        if uploaded_files:
            st.info(f"Ready to upload {len(uploaded_files)} file(s)")
        
        # Show current documents
        if session.documents:
            st.markdown("**Current Documents:**")
            for i, doc in enumerate(session.documents):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.text(f"📄 {doc.original_name}")
                with col2:
                    if st.button("🗑️", key=f"remove_{i}", help="Remove"):
                        self._handle_document_removal(doc.filename)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📤 Upload", type="primary", use_container_width=True, disabled=not uploaded_files):
                if uploaded_files and self._handle_document_upload(uploaded_files):
                    st.session_state.active_modal = None
                    st.rerun()
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.active_modal = None
                st.rerun()
    
    @st.dialog("⚙️ Chat Settings")
    def _render_settings_modal(self, session):
        """Render chat settings modal"""
        st.markdown("Adjust your chat preferences:")
        
        temperature = st.slider("🌡️ Creativity Level", 0.0, 1.0, value=session.settings.temperature, step=0.1)
        max_sources = st.slider("📄 Maximum Sources", 1, 20, value=session.settings.max_sources)
        
        style_options = ["detailed", "concise", "technical"]
        current_style_index = style_options.index(session.settings.response_style) if session.settings.response_style in style_options else 0
        response_style = st.selectbox("📝 Response Style", style_options, index=current_style_index)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Apply", type="primary", use_container_width=True):
                self.session_manager.update_current_session_settings(
                    temperature=temperature,
                    max_sources=max_sources,
                    response_style=response_style
                )
                st.session_state.active_modal = None
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear Chat", type="secondary", use_container_width=True):
                if self._handle_clear_conversation():
                    st.session_state.active_modal = None
                    st.rerun()
        
        with col3:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.active_modal = None
                st.rerun()
    
    def _handle_modals(self, session):
        """Handle modal display based on active_modal state"""
        active_modal = st.session_state.get('active_modal')
        
        if active_modal == "kb":
            self._render_kb_modal(session)
        elif active_modal == "upload":
            self._render_upload_modal(session)
        elif active_modal == "settings":
            self._render_settings_modal(session)
    
    def _get_contextual_suggestions(self, session) -> List[str]:
        """Get contextual suggestions based on session state"""
        if not session.knowledge_base_name:
            return [
                "Explain quantum entanglement in simple terms",
                "What are the key principles of machine learning?",
                "Help me understand statistical mechanics",
                "Explain the difference between classical and quantum computing",
                "What are the main branches of physics?",
                "Help me write a research proposal outline"
            ]
        elif session.documents:
            return [
                "Summarize the uploaded documents",
                "What are the key findings in these papers?",
                "Compare the methodologies in my documents",
                "Help me find connections between these papers",
                "What questions do these papers raise?",
                "Help me write a literature review based on these documents"
            ]
        else:
            return [
                "What papers do I have about quantum computing?",
                "Summarize the main themes in my research",
                "Who are the most cited authors in my collection?",
                "Help me write an introduction for my paper",
                "What are recent developments in my field?",
                "Find papers related to machine learning"
            ]
    
    def _process_user_message(self, message: str):
        """Process user message with integrated session handling"""
        # Add user message
        if self.integration:
            if not self.integration.handle_message_add("user", message):
                st.error("Failed to save message")
                return
        else:
            if not self.session_manager.add_message_to_current("user", message):
                st.error("Failed to save message")
                return
        
        # Display user message
        with st.chat_message("user"):
            st.write(message)
        
        # Get and display AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    current_session = self.session_manager.current_session
                    response_content, sources = self._get_ai_response(message, current_session)
                    
                    st.write(response_content)
                    
                    if sources:
                        sources_text = ", ".join(sources[:3])
                        if len(sources) > 3:
                            sources_text += f" and {len(sources) - 3} more"
                        st.caption(f"📚 Sources: {sources_text}")
                    
                    # Add assistant response
                    if self.integration:
                        self.integration.handle_message_add("assistant", response_content, sources)
                    else:
                        self.session_manager.add_message_to_current("assistant", response_content, sources)
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    
                    if self.integration:
                        self.integration.handle_message_add("assistant", error_msg)
                    else:
                        self.session_manager.add_message_to_current("assistant", error_msg)
        
        st.rerun()
    
    def _get_ai_response(self, message: str, session) -> Tuple[str, List[str]]:
        """Get AI response with proper error handling"""
        config = st.session_state.get('config')
        if not config or not config.anthropic_api_key:
            raise RuntimeError("Anthropic API key not configured")
        
        if not session.knowledge_base_name:
            return self._get_pure_chat_response(message, session, config)
        else:
            return self._get_kb_assisted_response(message, session, config)
    
    def _get_pure_chat_response(self, message: str, session, config) -> Tuple[str, List[str]]:
        """Get response in pure chat mode"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            
            # Build conversation context
            messages = []
            for msg in session.messages[-10:]:  # Last 10 for context
                if msg.role in ["user", "assistant"]:
                    messages.append({"role": msg.role, "content": msg.content})
            
            messages.append({"role": "user", "content": message})
            
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=session.settings.temperature,
                messages=messages,
                system="You are a helpful physics research assistant with expertise in theoretical and experimental physics, mathematics, and scientific research methodology."
            )
            
            return response.content[0].text, []
            
        except Exception as e:
            logger.error(f"Pure chat response failed: {e}")
            raise RuntimeError(f"Failed to get AI response: {str(e)}")
    
    def _get_kb_assisted_response(self, message: str, session, config) -> Tuple[str, List[str]]:
        """Get response with knowledge base assistance"""
        try:
            from ..core import load_knowledge_base
            
            kb = load_knowledge_base(session.knowledge_base_name, config.knowledge_bases_folder)
            if not kb:
                raise RuntimeError(f"Knowledge base '{session.knowledge_base_name}' not found")
            
            assistant = LiteratureAssistant(kb, config.anthropic_api_key, config.get_chat_config())
            response = assistant.ask(
                message,
                temperature=session.settings.temperature,
                max_context_chunks=session.settings.max_sources
            )
            
            return response.content, response.sources_used
            
        except Exception as e:
            logger.error(f"KB-assisted response failed: {e}")
            raise RuntimeError(f"Failed to get KB-assisted response: {str(e)}")
    
    # Handler methods
    def _handle_kb_change(self, new_kb: Optional[str]) -> bool:
        """Handle knowledge base change"""
        if self.integration:
            return self.integration.handle_kb_change(new_kb)
        else:
            return self.session_manager.set_knowledge_base_for_current(new_kb)
    
    def _handle_document_upload(self, uploaded_files) -> bool:
        """Handle document upload"""
        if self.integration:
            uploaded_names = self.integration.handle_document_upload(uploaded_files)
            return bool(uploaded_names)
        else:
            # Fallback implementation
            success_count = 0
            for file in uploaded_files:
                temp_path = Path("/tmp") / file.name
                with open(temp_path, "wb") as f:
                    f.write(file.getbuffer())
                
                if self.session_manager.add_document_to_current(temp_path, file.name):
                    success_count += 1
                
                if temp_path.exists():
                    temp_path.unlink()
            
            return success_count > 0
    
    def _handle_document_removal(self, filename: str) -> bool:
        """Handle document removal"""
        return self.session_manager.remove_document_from_current(filename)
    
    def _handle_clear_conversation(self) -> bool:
        """Handle conversation clearing"""
        if self.integration:
            return self.integration.handle_clear_conversation()
        else:
            current_session = self.session_manager.current_session
            if current_session:
                current_session.messages = []
                return self.session_manager.save_current_session()
            return False
    
    def _handle_ui_updates(self):
        """Handle UI updates and auto-save"""
        # Show feedback messages
        for msg_type in ['show_success_message', 'show_error_message', 'show_info_message']:
            if st.session_state.get(msg_type):
                getattr(st, msg_type.split('_')[1])(st.session_state[msg_type])
                del st.session_state[msg_type]
        
        # Auto-save periodically
        current_session = self.session_manager.current_session
        if current_session and self.integration:
            last_save = st.session_state.get('last_session_save', 0)
            current_time = time.time()
            
            if current_time - last_save > 30:  # Every 30 seconds
                self.integration.sync_session_to_streamlit(current_session)  # ← Fixed line
                self.session_manager.save_current_session()
                st.session_state.last_session_save = current_time


def render_chat_css():
    """Render optimized CSS for the chat interface"""
    st.markdown("""
    <style>
    /* Integrated Bottom Bar */
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
    
    .integrated-bottom-bar .stChatInput > div {
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }
    
    .integrated-bottom-bar .stChatInput > div:focus-within {
        border-color: #667eea !important;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2) !important;
    }
    
    .integrated-bottom-bar .stButton > button {
        width: 48px !important;
        height: 48px !important;
        border-radius: 12px !important;
        border: 2px solid #e2e8f0 !important;
        font-size: 1.3rem !important;
        transition: all 0.3s ease !important;
        background: white !important;
    }
    
    .integrated-bottom-bar .stButton > button:hover {
        transform: translateY(-2px) scale(1.05) !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.15) !important;
        border-color: #667eea !important;
    }
    
    /* Main content spacing for sticky bar */
    .main .block-container {
        padding-bottom: 120px;
    }
    
    /* Chat messages */
    .stChatMessage {
        margin-bottom: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Context info */
    .stInfo {
        background: linear-gradient(135deg, #e0f2fe 0%, #b3e5fc 100%);
        border: 1px solid #0288d1;
        color: #01579b;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Suggestion buttons */
    .stButton > button[key*="suggestion_"] {
        background: white;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem;
        transition: all 0.3s ease;
        text-align: left;
        width: 100%;
    }
    
    .stButton > button[key*="suggestion_"]:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
        transform: translateY(-2px);
    }
    
    /* Modal styling */
    div[data-testid="stModal"] {
        background: rgba(0, 0, 0, 0.5) !important;
        backdrop-filter: blur(4px) !important;
    }
    
    div[data-testid="stModal"] > div {
        background: white !important;
        border-radius: 16px !important;
        padding: 2rem !important;
        max-width: 500px !important;
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3) !important;
        animation: modalSlideIn 0.3s ease-out !important;
    }
    
    @keyframes modalSlideIn {
        from { opacity: 0; transform: scale(0.9) translateY(-20px); }
        to { opacity: 1; transform: scale(1) translateY(0); }
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .integrated-bottom-bar { padding: 0.75rem; }
        .integrated-bottom-bar .stButton > button { width: 42px !important; height: 42px !important; }
        .main .block-container { padding-bottom: 100px; }
    }
    </style>
    """, unsafe_allow_html=True)

def render_enhanced_chat_css():
    """Compatibility alias for render_chat_css"""
    render_chat_css()

# Compatibility class for existing imports
class EnhancedChatInterface(ChatInterface):
    """Compatibility alias for enhanced chat interface"""
    pass