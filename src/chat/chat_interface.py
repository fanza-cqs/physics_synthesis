#!/usr/bin/env python3
"""
Chat interface for the Physics Literature Synthesis Pipeline.

Provides a clean interface for conversational AI interactions with
literature-aware context and conversation memory management.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import anthropic

from ..utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ChatMessage:
    """Container for a chat message."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[float] = None

@dataclass
class ChatResponse:
    """Container for a chat response with metadata."""
    content: str
    sources_used: List[str]
    processing_time: float
    context_chunks_used: int

class ChatInterface:
    """
    Basic chat interface for AI conversations.
    
    Handles conversation history, message formatting, and API interactions.
    """
    
    def __init__(self, 
                 anthropic_api_key: str,
                 model: str = "claude-3-5-sonnet-20241022",
                 max_tokens: int = 4000,
                 max_conversation_length: int = 20):
        """
        Initialize the chat interface.
        
        Args:
            anthropic_api_key: Anthropic API key
            model: Claude model to use
            max_tokens: Maximum tokens per response
            max_conversation_length: Max messages to keep in history
        """
        self.client = anthropic.Anthropic(api_key=anthropic_api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.max_conversation_length = max_conversation_length
        
        # Conversation storage
        self.conversation_history: List[ChatMessage] = []
        self.system_prompt = ""
        
        logger.info(f"Chat interface initialized with model: {model}")
    
    def set_system_prompt(self, system_prompt: str) -> None:
        """
        Set the system prompt for the conversation.
        
        Args:
            system_prompt: System prompt to guide AI behavior
        """
        self.system_prompt = system_prompt
        logger.debug("System prompt updated")
    
    def send_message(self, 
                    user_message: str,
                    temperature: float = 0.3,
                    include_history: bool = True) -> str:
        """
        Send a message and get AI response.
        
        Args:
            user_message: User's message
            temperature: AI creativity level (0.0-1.0)
            include_history: Whether to include conversation history
        
        Returns:
            AI response text
        """
        logger.debug(f"Sending message: {user_message[:50]}...")
        
        # Prepare messages for API
        messages = []
        
        # Include conversation history if requested
        if include_history:
            for msg in self.conversation_history:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=temperature,
                system=self.system_prompt if self.system_prompt else None,
                messages=messages
            )
            
            assistant_response = response.content[0].text
            
            # Update conversation history
            self.add_to_history("user", user_message)
            self.add_to_history("assistant", assistant_response)
            
            logger.debug(f"Received response: {assistant_response[:50]}...")
            return assistant_response
            
        except Exception as e:
            logger.error(f"Error calling Claude API: {e}")
            raise
    
    def add_to_history(self, role: str, content: str) -> None:
        """
        Add a message to conversation history.
        
        Args:
            role: 'user' or 'assistant'
            content: Message content
        """
        import time
        
        message = ChatMessage(
            role=role,
            content=content,
            timestamp=time.time()
        )
        
        self.conversation_history.append(message)
        
        # Trim history if it gets too long
        if len(self.conversation_history) > self.max_conversation_length:
            # Keep recent messages (remove oldest pairs)
            self.conversation_history = self.conversation_history[-self.max_conversation_length:]
        
        logger.debug(f"Added {role} message to history ({len(self.conversation_history)} total)")
    
    def get_conversation_history(self) -> List[ChatMessage]:
        """
        Get the current conversation history.
        
        Returns:
            List of ChatMessage objects
        """
        return self.conversation_history.copy()
    
    def clear_conversation(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []
        logger.info("Conversation history cleared")
    
    def get_conversation_summary(self) -> str:
        """
        Get a summary of the current conversation.
        
        Returns:
            String summary of conversation
        """
        if not self.conversation_history:
            return "No conversation yet."
        
        # Count exchanges (pairs of user/assistant messages)
        user_messages = [msg for msg in self.conversation_history if msg.role == "user"]
        exchanges = len(user_messages)
        
        # Get recent topics from user messages
        recent_topics = []
        for msg in reversed(user_messages[-3:]):  # Last 3 user messages
            topic = msg.content[:50].strip()
            if len(msg.content) > 50:
                topic += "..."
            recent_topics.append(topic)
        
        summary = f"Conversation: {exchanges} exchanges"
        if recent_topics:
            summary += f". Recent topics: {', '.join(reversed(recent_topics))}"
        
        return summary
    
    def export_conversation(self, format: str = "markdown") -> str:
        """
        Export conversation in specified format.
        
        Args:
            format: Export format ('markdown', 'text', 'json')
        
        Returns:
            Formatted conversation string
        """
        if not self.conversation_history:
            return "No conversation to export."
        
        if format == "markdown":
            lines = ["# Conversation Export\n\n"]
            for i, msg in enumerate(self.conversation_history):
                if msg.role == "user":
                    lines.append(f"## User Message {(i//2) + 1}\n\n{msg.content}\n\n")
                else:
                    lines.append(f"## Assistant Response {(i//2) + 1}\n\n{msg.content}\n\n")
            return "".join(lines)
        
        elif format == "text":
            lines = []
            for msg in self.conversation_history:
                prefix = "USER: " if msg.role == "user" else "ASSISTANT: "
                lines.append(f"{prefix}{msg.content}\n")
            return "\n".join(lines)
        
        elif format == "json":
            import json
            data = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
                for msg in self.conversation_history
            ]
            return json.dumps(data, indent=2)
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def get_last_response(self) -> Optional[str]:
        """
        Get the last assistant response.
        
        Returns:
            Last assistant message content or None
        """
        for msg in reversed(self.conversation_history):
            if msg.role == "assistant":
                return msg.content
        return None
    
    def get_conversation_length(self) -> int:
        """
        Get the number of messages in conversation.
        
        Returns:
            Number of messages in history
        """
        return len(self.conversation_history)
    
    def truncate_conversation(self, keep_last_n: int) -> None:
        """
        Truncate conversation to keep only last N messages.
        
        Args:
            keep_last_n: Number of recent messages to keep
        """
        if keep_last_n < len(self.conversation_history):
            self.conversation_history = self.conversation_history[-keep_last_n:]
            logger.info(f"Conversation truncated to {keep_last_n} messages")
    
    def remove_last_exchange(self) -> bool:
        """
        Remove the last user-assistant exchange.
        
        Returns:
            True if exchange was removed, False if not possible
        """
        if len(self.conversation_history) >= 2:
            # Check if last two messages form a complete exchange
            if (self.conversation_history[-2].role == "user" and 
                self.conversation_history[-1].role == "assistant"):
                
                self.conversation_history = self.conversation_history[:-2]
                logger.info("Removed last exchange from conversation")
                return True
        
        return False
    
    def get_context_for_search(self, max_chars: int = 500) -> str:
        """
        Get recent conversation context for search purposes.
        
        Args:
            max_chars: Maximum characters to include
        
        Returns:
            Recent conversation context as string
        """
        if not self.conversation_history:
            return ""
        
        # Get recent messages
        recent_messages = self.conversation_history[-4:]  # Last 2 exchanges
        context_parts = []
        total_chars = 0
        
        for msg in reversed(recent_messages):
            msg_text = msg.content[:200]  # Limit each message
            if total_chars + len(msg_text) > max_chars:
                break
            context_parts.append(msg_text)
            total_chars += len(msg_text)
        
        return " ".join(reversed(context_parts))