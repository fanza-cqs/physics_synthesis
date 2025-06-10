# src/ui/chat_interface.py
"""
Pure chat interface component for Physics Literature Synthesis Pipeline
Main chat area with KB selection, document upload, and conversation display
"""

import streamlit as st
from typing import List, Dict, Optional
from pathlib import Path
import time

from ..sessions import SessionManager
from ..chat import LiteratureAssistant
from ..core import list_knowledge_bases
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class ChatInterface:
    """
    Main chat interface component
    Handles the complete chat experience including context management
    """
    
    def __init__(self, session_manager: SessionManager):
        """
        Initialize chat interface
        
        Args:
            session_manager: Session manager instance
        """
        self.session_manager = session_manager
    
    def render(self):
        """Render the complete chat interface"""
        # Ensure we have a current session
        current_session = self.session_manager.get_or_create_default_session()
        
        # Render chat header with context controls
        self._render_chat_header(current_session)
        
        # Render conversation messages
        self._render_conversation(current_session)
        
        # Render suggested questions (if no messages)
        if not current_session.has_messages():
            self._render_suggested_questions()
        
        # Render chat input
        self._render_chat_input()
    
    def _render_chat_header(self, session):
        """Render chat header with session context and controls"""
        st.markdown("### 💬 Research Assistant")
        
        # Session context bar
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            # Knowledge Base selection
            self._render_kb_selector(session)
        
        with col2:
            # Document upload
            self._render_document_upload(session)
        
        with col3:
            # Chat settings
            self._render_chat_settings()
        
        # Current context display
        self._render_context_display(session)
    
    def _render_kb_selector(self, session):
        """Render knowledge base selector dropdown"""
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
            current_index = kb_names.index(current_kb) + 1  # +1 for "None" option
        else:
            current_index = 0  # "None" option
        
        # KB selector
        selected = st.selectbox(
            "Knowledge Base:",
            options,
            index=current_index,
            key="kb_selector",
            help="Choose a knowledge base or use pure chat mode"
        )
        
        # Handle KB change
        if selected == "None (Pure Chat)":
            new_kb = None
        else:
            new_kb = selected
        
        # Update session if KB changed
        if new_kb != current_kb:
            if self.session_manager.set_knowledge_base_for_current(new_kb):
                if new_kb:
                    st.success(f"✅ Switched to knowledge base: {new_kb}")
                else:
                    st.info("💬 Switched to pure chat mode")
                st.rerun()
            else:
                st.error("Failed to switch knowledge base")
    
    def _render_document_upload(self, session):
        """Render document upload interface"""
        uploaded_files = st.file_uploader(
            "Upload Documents:",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'md', 'tex'],
            key="chat_file_uploader",
            help="Upload documents to this conversation"
        )
        
        if uploaded_files:
            self._handle_document_upload(session, uploaded_files)
    
    def _render_chat_settings(self):
        """Render chat settings in expandable section"""
        with st.expander("⚙️", expanded=False):
            st.markdown("**Chat Settings**")
            
            # Temperature
            temperature = st.slider(
                "🌡️ Creativity",
                0.0, 1.0,
                value=st.session_state.get('chat_temperature', 0.3),
                step=0.1,
                help="Higher values make responses more creative"
            )
            
            # Max sources
            max_sources = st.slider(
                "📄 Max Sources",
                1, 20,
                value=st.session_state.get('chat_max_sources', 8),
                help="Maximum number of sources to use"
            )
            
            # Response style
            response_style = st.selectbox(
                "📝 Response Style",
                ["detailed", "concise", "technical"],
                index=0,
                help="Preferred response style"
            )
            
            # Update session settings if changed
            current_session = self.session_manager.current_session
            if current_session:
                settings_changed = (
                    temperature != current_session.settings.temperature or
                    max_sources != current_session.settings.max_sources or
                    response_style != current_session.settings.response_style
                )
                
                if settings_changed:
                    self.session_manager.update_current_session_settings(
                        temperature=temperature,
                        max_sources=max_sources,
                        response_style=response_style
                    )
                    
                    # Update global session state for immediate use
                    st.session_state.chat_temperature = temperature
                    st.session_state.chat_max_sources = max_sources
            
            # Clear conversation button
            if st.button("🗑️ Clear Conversation"):
                self._clear_current_conversation()
    
    def _render_context_display(self, session):
        """Display current session context"""
        context_parts = []
        
        # Session name
        if session.name != "New Session":
            context_parts.append(f"**Session:** {session.name}")
        
        # Knowledge base
        if session.knowledge_base_name:
            context_parts.append(f"**KB:** {session.knowledge_base_name}")
        else:
            context_parts.append("**Mode:** Pure Chat")
        
        # Documents
        if session.documents:
            doc_names = [doc.original_name for doc in session.documents]
            if len(doc_names) <= 3:
                docs_text = ", ".join(doc_names)
            else:
                docs_text = f"{', '.join(doc_names[:3])} and {len(doc_names) - 3} more"
            context_parts.append(f"**Documents:** {docs_text}")
        
        if context_parts:
            context_text = " • ".join(context_parts)
            st.info(context_text)
        
        # Document management (if documents exist)
        if session.documents:
            self._render_document_management(session)
    
    def _render_document_management(self, session):
        """Render document management interface"""
        with st.expander(f"📎 Manage Documents ({len(session.documents)})"):
            for doc in session.documents:
                col1, col2, col3 = st.columns([3, 1, 1])
                
                with col1:
                    st.markdown(f"📄 **{doc.original_name}**")
                    st.caption(f"Uploaded: {doc.upload_timestamp.strftime('%m/%d/%Y %I:%M %p')}")
                
                with col2:
                    file_size_mb = doc.file_size / (1024 * 1024)
                    st.caption(f"{file_size_mb:.2f} MB")
                
                with col3:
                    if st.button("🗑️", key=f"remove_doc_{doc.filename}", help="Remove document"):
                        if self.session_manager.remove_document_from_current(doc.filename):
                            st.success("Document removed!")
                            st.rerun()
                        else:
                            st.error("Failed to remove document")
    
    def _render_conversation(self, session):
        """Render the conversation messages"""
        messages = session.messages
        
        for message in messages:
            with st.chat_message(message.role):
                st.write(message.content)
                
                # Show sources for assistant messages
                if message.role == "assistant" and message.sources:
                    sources_text = ", ".join(message.sources[:3])
                    if len(message.sources) > 3:
                        sources_text += f" and {len(message.sources) - 3} more"
                    st.caption(f"📚 Sources: {sources_text}")
    
    def _render_suggested_questions(self):
        """Render suggested questions for empty sessions"""
        st.markdown("### 💡 Get started with these questions:")
        
        # Get session context for relevant suggestions
        current_session = self.session_manager.current_session
        suggestions = self._get_contextual_suggestions(current_session)
        
        # Display suggestions in columns
        cols = st.columns(2)
        for i, suggestion in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"❓ {suggestion}", key=f"suggestion_{i}"):
                    self._process_user_message(suggestion)
    
    def _render_chat_input(self):
        """Render chat input area"""
        # Chat input
        if prompt := st.chat_input("Ask about your research..."):
            self._process_user_message(prompt)
    
    def _get_contextual_suggestions(self, session) -> List[str]:
        """Get contextual suggestions based on session state"""
        base_suggestions = [
            "What papers do I have about quantum computing?",
            "Summarize the main themes in my research",
            "Help me write an introduction for my paper",
            "What are recent developments in my field?",
            "Who are the most cited authors in my collection?",
            "Find papers related to machine learning"
        ]
        
        # Customize based on context
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
                "Help me write a literature review"
            ]
        else:
            # Has KB but no uploaded docs
            return base_suggestions
    
    def _process_user_message(self, message: str):
        """Process a user message and get AI response"""
        current_session = self.session_manager.current_session
        if not current_session:
            st.error("No active session")
            return
        
        # Add user message to session
        if not self.session_manager.add_message_to_current("user", message):
            st.error("Failed to save user message")
            return
        
        # Display user message immediately
        with st.chat_message("user"):
            st.write(message)
        
        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
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
                    if not self.session_manager.add_message_to_current("assistant", response_content, sources):
                        st.error("Failed to save assistant response")
                    
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {str(e)}"
                    st.error(error_msg)
                    
                    # Add error message to session
                    self.session_manager.add_message_to_current("assistant", error_msg)
        
        # Rerun to update the conversation display
        st.rerun()
    
    def _get_ai_response(self, message: str, session) -> tuple[str, List[str]]:
        """
        Get AI response for a message
        
        Args:
            message: User message
            session: Current session
            
        Returns:
            Tuple of (response_content, sources_list)
        """
        config = st.session_state.get('config')
        if not config:
            raise RuntimeError("Configuration not available")
        
        if not config.anthropic_api_key:
            raise RuntimeError("Anthropic API key not configured")
        
        # Pure chat mode (no KB)
        if not session.knowledge_base_name:
            return self._get_pure_chat_response(message, session, config)
        
        # KB-assisted chat mode
        return self._get_kb_assisted_response(message, session, config)
    
    def _get_pure_chat_response(self, message: str, session, config) -> tuple[str, List[str]]:
        """Get response in pure chat mode (no knowledge base)"""
        try:
            import anthropic
            
            client = anthropic.Anthropic(api_key=config.anthropic_api_key)
            
            # Build conversation history for context
            messages = []
            for msg in session.messages[-10:]:  # Last 10 messages for context
                if msg.role in ["user", "assistant"]:
                    messages.append({
                        "role": msg.role,
                        "content": msg.content
                    })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Create response
            response = client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=session.settings.temperature,
                messages=messages,
                system="You are a helpful physics research assistant. Provide clear, accurate, and helpful responses about physics, research, and academic topics."
            )
            
            return response.content[0].text, []
            
        except Exception as e:
            logger.error(f"Pure chat response failed: {e}")
            raise RuntimeError(f"Failed to get AI response: {str(e)}")
    
    def _get_kb_assisted_response(self, message: str, session, config) -> tuple[str, List[str]]:
        """Get response with knowledge base assistance"""
        try:
            # Load knowledge base
            from ..core import load_knowledge_base
            
            kb = load_knowledge_base(session.knowledge_base_name, config.knowledge_bases_folder)
            if not kb:
                raise RuntimeError(f"Knowledge base '{session.knowledge_base_name}' not found")
            
            # Create literature assistant
            assistant = LiteratureAssistant(kb, config.anthropic_api_key, config.get_chat_config())
            
            # Get response
            response = assistant.ask(
                message,
                temperature=session.settings.temperature,
                max_context_chunks=session.settings.max_sources
            )
            
            return response.content, response.sources_used
            
        except Exception as e:
            logger.error(f"KB-assisted response failed: {e}")
            raise RuntimeError(f"Failed to get KB-assisted response: {str(e)}")
    
    def _handle_document_upload(self, session, uploaded_files):
        """Handle document upload for current session"""
        success_count = 0
        
        for uploaded_file in uploaded_files:
            try:
                # Save uploaded file temporarily
                temp_file = Path("/tmp") / uploaded_file.name
                with open(temp_file, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Add to session
                doc = self.session_manager.add_document_to_current(temp_file, uploaded_file.name)
                
                if doc:
                    success_count += 1
                    logger.info(f"Added document to session: {uploaded_file.name}")
                else:
                    st.error(f"Failed to add document: {uploaded_file.name}")
                
                # Clean up temp file
                if temp_file.exists():
                    temp_file.unlink()
                    
            except Exception as e:
                logger.error(f"Document upload failed for {uploaded_file.name}: {e}")
                st.error(f"Failed to upload {uploaded_file.name}: {str(e)}")
        
        if success_count > 0:
            st.success(f"✅ Added {success_count} document(s) to this conversation")
            st.rerun()
    
    def _clear_current_conversation(self):
        """Clear the current conversation"""
        current_session = self.session_manager.current_session
        if not current_session:
            return
        
        # Clear messages from session
        current_session.messages = []
        
        # Save session
        if self.session_manager.save_current_session():
            st.success("Conversation cleared!")
            st.rerun()
        else:
            st.error("Failed to clear conversation")


def render_chat_css():
    """Render CSS for chat interface styling"""
    st.markdown("""
    <style>
    /* Chat interface styling */
    .stChatMessage {
        margin-bottom: 1rem;
    }
    
    /* Chat input styling */
    .stChatInput > div {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        background: white;
    }
    
    .stChatInput > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Context display styling */
    .stInfo {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 1rem 0;
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        border: 2px dashed #667eea;
        border-radius: 10px;
        background: #f8fafc;
        padding: 1rem;
        text-align: center;
    }
    
    .stFileUploader > div:hover {
        border-color: #764ba2;
        background: #f1f5f9;
    }
    
    /* Suggestion buttons */
    .suggestion-button {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border: 1px solid #d1d5db;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.25rem 0;
        transition: all 0.3s ease;
        cursor: pointer;
        text-align: left;
        width: 100%;
    }
    
    .suggestion-button:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: transparent;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    /* Settings expander */
    .stExpander {
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        background: white;
    }
    
    .stExpander > div > div > div[data-testid="stExpanderHeader"] {
        background: #f8fafc;
        border-radius: 8px 8px 0 0;
    }
    
    /* Document management */
    .document-item {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.25rem 0;
    }
    
    /* Knowledge base selector */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e2e8f0;
    }
    
    .stSelectbox > div > div:focus-within {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Success/error messages */
    .stSuccess {
        background-color: #ecfdf5;
        border: 1px solid #10b981;
        color: #065f46;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    
    .stError {
        background-color: #fef2f2;
        border: 1px solid #ef4444;
        color: #991b1b;
        border-radius: 8px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)


class ChatState:
    """
    Helper class to manage chat-related session state
    """
    
    @staticmethod
    def initialize():
        """Initialize chat-related session state"""
        defaults = {
            'chat_temperature': 0.3,
            'chat_max_sources': 8,
            'show_kb_management': False,
            'show_zotero_management': False,
            'show_settings': False
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value
    
    @staticmethod
    def clear_management_dialogs():
        """Clear all management dialog states"""
        st.session_state.show_kb_management = False
        st.session_state.show_zotero_management = False
        st.session_state.show_settings = False