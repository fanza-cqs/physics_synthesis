# src/utils/auto_naming.py
"""
AI-powered auto-naming system for Physics Literature Synthesis Pipeline
Generates intelligent session names based on conversation content
"""

import logging
from typing import List, Optional
from datetime import datetime

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class AutoNamingService:
    """
    AI-powered service for generating intelligent session names
    Uses conversation context to create meaningful, descriptive names
    """
    
    def __init__(self, anthropic_api_key: str):
        """
        Initialize auto-naming service
        
        Args:
            anthropic_api_key: Anthropic API key for AI naming
        """
        self.anthropic_api_key = anthropic_api_key
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of Anthropic client"""
        if self._client is None:
            try:
                import anthropic
                self._client = anthropic.Anthropic(api_key=self.anthropic_api_key)
            except ImportError:
                logger.error("Anthropic package not available for auto-naming")
                return None
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                return None
        return self._client
    
    def generate_name_from_first_message(self, message: str) -> str:
        """
        Generate session name from first user message
        Simple truncation with smart word boundaries
        
        Args:
            message: First user message
            
        Returns:
            Generated session name
        """
        try:
            # Clean the message
            cleaned = message.strip().replace('\n', ' ').replace('\r', ' ')
            
            # Remove common question words at the start
            question_starters = [
                "what is", "what are", "how do", "how does", "can you", 
                "could you", "would you", "please", "help me", "tell me about",
                "explain", "describe", "show me"
            ]
            
            cleaned_lower = cleaned.lower()
            for starter in question_starters:
                if cleaned_lower.startswith(starter):
                    cleaned = cleaned[len(starter):].strip()
                    break
            
            # Capitalize first letter
            if cleaned:
                cleaned = cleaned[0].upper() + cleaned[1:]
            
            # Truncate at word boundaries
            if len(cleaned) <= 50:
                return cleaned if cleaned else "New Session"
            
            # Find good truncation point
            truncated = cleaned[:47]
            last_space = truncated.rfind(' ')
            
            if last_space > 30:  # Don't truncate too early
                return truncated[:last_space] + "..."
            else:
                return truncated + "..."
                
        except Exception as e:
            logger.error(f"Error generating name from first message: {e}")
            return "New Session"
    
    def generate_intelligent_name(self, messages: List[dict], 
                                knowledge_base_name: Optional[str] = None,
                                document_names: List[str] = None) -> Optional[str]:
        """
        Generate intelligent session name using AI based on conversation content
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            knowledge_base_name: Name of knowledge base if any
            document_names: List of uploaded document names
            
        Returns:
            Generated session name or None if generation fails
        """
        if not self.client:
            logger.warning("Anthropic client not available for intelligent naming")
            return None
        
        try:
            # Build context for naming
            context_parts = []
            
            # Add KB context
            if knowledge_base_name:
                context_parts.append(f"Knowledge Base: {knowledge_base_name}")
            
            # Add document context
            if document_names:
                doc_list = ", ".join(document_names[:3])
                if len(document_names) > 3:
                    doc_list += f" and {len(document_names) - 3} more"
                context_parts.append(f"Documents: {doc_list}")
            
            # Prepare conversation summary
            user_messages = [msg['content'] for msg in messages if msg['role'] == 'user']
            assistant_messages = [msg['content'] for msg in messages if msg['role'] == 'assistant']
            
            # Build prompt for AI naming
            conversation_text = self._build_conversation_summary(user_messages, assistant_messages)
            context_text = "; ".join(context_parts) if context_parts else "No additional context"
            
            prompt = f"""Based on this physics research conversation, generate a concise, descriptive session name (2-6 words max):

Context: {context_text}

Conversation summary:
{conversation_text}

Generate a session name that captures the main topic or research question. Examples of good names:
- "Quantum entanglement analysis"
- "Literature review help" 
- "Machine learning in physics"
- "Research proposal draft"

Session name:"""

            # Call AI for naming
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",  # Use faster model for naming
                max_tokens=20,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract and clean the name
            generated_name = response.content[0].text.strip()
            cleaned_name = self._clean_generated_name(generated_name)
            
            logger.info(f"Generated intelligent session name: '{cleaned_name}'")
            return cleaned_name
            
        except Exception as e:
            logger.error(f"Failed to generate intelligent session name: {e}")
            return None
    
    def _build_conversation_summary(self, user_messages: List[str], 
                                  assistant_messages: List[str]) -> str:
        """Build a concise conversation summary for naming"""
        summary_parts = []
        
        # Add first user message (most important)
        if user_messages:
            first_msg = user_messages[0][:200]  # Truncate long messages
            summary_parts.append(f"Initial question: {first_msg}")
        
        # Add key topics from user messages
        if len(user_messages) > 1:
            key_topics = self._extract_key_topics(user_messages[1:])
            if key_topics:
                summary_parts.append(f"Topics discussed: {key_topics}")
        
        # Add assistant response themes if available
        if assistant_messages:
            response_themes = self._extract_response_themes(assistant_messages)
            if response_themes:
                summary_parts.append(f"Assistant helped with: {response_themes}")
        
        return "\n".join(summary_parts)
    
    def _extract_key_topics(self, messages: List[str]) -> str:
        """Extract key topics from user messages"""
        # Simple keyword extraction for physics topics
        physics_keywords = [
            "quantum", "classical", "relativity", "mechanics", "thermodynamics",
            "electromagnetism", "optics", "nuclear", "particle", "astronomy",
            "cosmology", "condensed matter", "statistical", "computational",
            "experimental", "theoretical", "research", "paper", "literature",
            "review", "analysis", "simulation", "data", "experiment"
        ]
        
        found_topics = set()
        for message in messages[:5]:  # Only check first 5 additional messages
            message_lower = message.lower()
            for keyword in physics_keywords:
                if keyword in message_lower:
                    found_topics.add(keyword)
        
        return ", ".join(sorted(found_topics)[:5])  # Max 5 topics
    
    def _extract_response_themes(self, messages: List[str]) -> str:
        """Extract themes from assistant responses"""
        # Look for common assistance patterns
        help_patterns = [
            ("explanation", ["explain", "understand", "concept"]),
            ("writing help", ["write", "draft", "compose", "structure"]),
            ("research guidance", ["research", "investigate", "explore", "find"]),
            ("data analysis", ["analyze", "data", "results", "statistics"]),
            ("literature review", ["literature", "papers", "sources", "citations"])
        ]
        
        found_themes = []
        combined_text = " ".join(messages[:3]).lower()  # First 3 responses
        
        for theme, patterns in help_patterns:
            if any(pattern in combined_text for pattern in patterns):
                found_themes.append(theme)
        
        return ", ".join(found_themes[:3])  # Max 3 themes
    
    def _clean_generated_name(self, name: str) -> str:
        """Clean and validate generated session name"""
        # Remove quotes and extra formatting
        cleaned = name.strip().strip('"').strip("'").strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            "session name:", "name:", "title:", "session:", 
            "conversation:", "discussion:", "chat:"
        ]
        
        cleaned_lower = cleaned.lower()
        for prefix in prefixes_to_remove:
            if cleaned_lower.startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Ensure reasonable length
        if len(cleaned) > 60:
            cleaned = cleaned[:57] + "..."
        
        # Capitalize properly
        if cleaned:
            # Title case for most words, but preserve physics terms
            words = cleaned.split()
            title_words = []
            
            physics_terms = {
                "ai", "ml", "qm", "qft", "gtr", "sr", "qed", "qcd", 
                "pdf", "doi", "arxiv", "api", "kb", "ui", "ux"
            }
            
            for word in words:
                if word.lower() in physics_terms:
                    title_words.append(word.upper())
                elif len(word) > 3:
                    title_words.append(word.capitalize())
                else:
                    title_words.append(word.lower())
            
            cleaned = " ".join(title_words)
        
        # Fallback if cleaning resulted in empty string
        return cleaned if cleaned else "Research Session"
    
    def should_improve_name(self, session_name: str, message_count: int) -> bool:
        """
        Determine if session name should be improved with AI
        
        Args:
            session_name: Current session name
            message_count: Number of messages in session
            
        Returns:
            True if name should be improved
        """
        # Don't improve if user has manually renamed
        if not session_name.endswith("..."):
            return False
        
        # Don't improve if it's still "New Session"
        if session_name == "New Session":
            return False
        
        # Improve after 3-5 messages when conversation has developed
        return 3 <= message_count <= 5
    
    def get_fallback_name(self, knowledge_base_name: Optional[str] = None,
                         document_count: int = 0) -> str:
        """
        Get fallback session name when AI naming fails
        
        Args:
            knowledge_base_name: Name of KB if any
            document_count: Number of documents
            
        Returns:
            Fallback session name
        """
        timestamp = datetime.now().strftime("%m/%d %H:%M")
        
        if knowledge_base_name:
            return f"{knowledge_base_name} - {timestamp}"
        elif document_count > 0:
            return f"Document Analysis - {timestamp}"
        else:
            return f"Research Session - {timestamp}"


def get_auto_naming_service(anthropic_api_key: str) -> AutoNamingService:
    """
    Get auto-naming service instance
    
    Args:
        anthropic_api_key: Anthropic API key
        
    Returns:
        AutoNamingService instance
    """
    return AutoNamingService(anthropic_api_key)


class SessionNameImprover:
    """
    Background service for improving session names as conversations develop
    """
    
    def __init__(self, auto_naming_service: AutoNamingService):
        """
        Initialize session name improver
        
        Args:
            auto_naming_service: Auto-naming service instance
        """
        self.auto_naming_service = auto_naming_service
    
    def should_trigger_improvement(self, session) -> bool:
        """
        Check if session name should be improved
        
        Args:
            session: Session object
            
        Returns:
            True if improvement should be triggered
        """
        # Only improve auto-generated names
        if not session.auto_named:
            return False
        
        # Don't improve if already improved
        if hasattr(session, '_name_improved') and session._name_improved:
            return False
        
        # Trigger after meaningful conversation
        user_message_count = len([m for m in session.messages if m.role == 'user'])
        return self.auto_naming_service.should_improve_name(session.name, user_message_count)
    
    def improve_session_name(self, session) -> Optional[str]:
        """
        Improve session name based on conversation development
        
        Args:
            session: Session object to improve name for
            
        Returns:
            Improved name or None if improvement fails
        """
        try:
            # Build message list for AI
            messages = [
                {'role': msg.role, 'content': msg.content}
                for msg in session.messages
                if msg.role in ['user', 'assistant']
            ]
            
            # Get document names
            document_names = [doc.original_name for doc in session.documents]
            
            # Generate improved name
            improved_name = self.auto_naming_service.generate_intelligent_name(
                messages, 
                session.knowledge_base_name,
                document_names
            )
            
            if improved_name:
                # Mark as improved to prevent repeated attempts
                session._name_improved = True
                logger.info(f"Improved session name from '{session.name}' to '{improved_name}'")
                return improved_name
            else:
                # Use fallback if AI naming fails
                fallback = self.auto_naming_service.get_fallback_name(
                    session.knowledge_base_name,
                    len(session.documents)
                )
                session._name_improved = True
                logger.info(f"Used fallback name: '{fallback}'")
                return fallback
                
        except Exception as e:
            logger.error(f"Failed to improve session name: {e}")
            return None