# src/sessions/enhanced_session_manager.py
"""
Enhanced Session Manager with AI auto-naming and advanced features
Extends the basic session manager with intelligent naming and optimization
"""

import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor
import threading

from .session_manager import SessionManager
from .session import Session
from ..utils.auto_naming import AutoNamingService, SessionNameImprover
from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class EnhancedSessionManager(SessionManager):
    """
    Enhanced session manager with AI auto-naming and advanced features
    Extends base functionality with intelligent session management
    """
    
    def __init__(self, project_root: Path, anthropic_api_key: Optional[str] = None):
        """
        Initialize enhanced session manager
        
        Args:
            project_root: Root directory of the project
            anthropic_api_key: Anthropic API key for AI features
        """
        super().__init__(project_root)
        
        # AI auto-naming service
        self.auto_naming_service = None
        self.name_improver = None
        
        if anthropic_api_key:
            try:
                self.auto_naming_service = AutoNamingService(anthropic_api_key)
                self.name_improver = SessionNameImprover(self.auto_naming_service)
                logger.info("AI auto-naming service initialized")
            except Exception as e:
                logger.warning(f"Could not initialize auto-naming service: {e}")
        
        # Background improvement tracking
        self._improvement_queue = []
        self._improvement_thread = None
        self._improvement_lock = threading.Lock()
        
        # Session analytics
        self._session_analytics = {}
        
        logger.info(f"EnhancedSessionManager initialized with AI features: {self.auto_naming_service is not None}")
    
    def create_session(self, 
                      name: Optional[str] = None,
                      knowledge_base_name: Optional[str] = None,
                      auto_activate: bool = True,
                      auto_name: bool = True) -> Session:
        """
        Create a new session with enhanced auto-naming
        
        Args:
            name: Session name (auto-generated if None and auto_name=True)
            knowledge_base_name: Knowledge base to attach (optional)
            auto_activate: Whether to make this the current session
            auto_name: Whether to use auto-naming features
            
        Returns:
            Created session
        """
        # Generate intelligent name if requested and possible
        if not name and auto_name and self.auto_naming_service:
            name = self._generate_initial_name(knowledge_base_name)
        
        # Fallback to default naming
        if not name:
            name = "New Session"
        
        # Create session using parent method
        session = super().create_session(name, knowledge_base_name, auto_activate)
        
        # Mark as auto-named if we generated the name
        if auto_name and name != "New Session":
            session.auto_named = True
        
        # Initialize session analytics
        self._init_session_analytics(session.id)
        
        logger.info(f"Created enhanced session: {session.id} - '{session.name}'")
        return session
    
    def add_message_to_current(self, role: str, content: str, sources: List[str] = None) -> bool:
        """
        Enhanced message addition with auto-naming improvement
        
        Args:
            role: Message role ("user" or "assistant")
            content: Message content
            sources: List of source references (optional)
            
        Returns:
            True if message added successfully, False otherwise
        """
        # Add message using parent method
        success = super().add_message_to_current(role, content, sources)
        
        if success and self._current_session:
            # Handle auto-naming for first user message
            if role == "user" and len(self._current_session.messages) == 1:
                self._handle_first_message_naming(content)
            
            # Queue name improvement if needed
            if self.name_improver and self.name_improver.should_trigger_improvement(self._current_session):
                self._queue_name_improvement(self._current_session.id)
            
            # Update analytics
            self._update_session_analytics(self._current_session.id, role)
        
        return success
    
    def _generate_initial_name(self, knowledge_base_name: Optional[str]) -> str:
        """Generate initial session name based on context"""
        try:
            if knowledge_base_name:
                return f"{knowledge_base_name} Discussion"
            else:
                timestamp = datetime.now().strftime("%m/%d %H:%M")
                return f"Research Session - {timestamp}"
        except Exception as e:
            logger.error(f"Failed to generate initial name: {e}")
            return "New Session"
    
    def _handle_first_message_naming(self, content: str):
        """Handle naming when first message is added"""
        if not self.auto_naming_service or not self._current_session:
            return
        
        try:
            # Generate name from first message
            generated_name = self.auto_naming_service.generate_name_from_first_message(content)
            
            if generated_name and generated_name != "New Session":
                self._current_session.set_name(generated_name)
                self._current_session.auto_named = True
                self.save_current_session()
                logger.info(f"Auto-named session from first message: '{generated_name}'")
        
        except Exception as e:
            logger.error(f"Failed to handle first message naming: {e}")
    
    def _queue_name_improvement(self, session_id: str):
        """Queue session for name improvement"""
        with self._improvement_lock:
            if session_id not in self._improvement_queue:
                self._improvement_queue.append(session_id)
                logger.debug(f"Queued session {session_id} for name improvement")
        
        # Start improvement thread if not running
        if not self._improvement_thread or not self._improvement_thread.is_alive():
            self._improvement_thread = threading.Thread(
                target=self._process_improvement_queue,
                daemon=True
            )
            self._improvement_thread.start()
    
    def _process_improvement_queue(self):
        """Process queued name improvements in background"""
        while True:
            session_id = None
            
            with self._improvement_lock:
                if self._improvement_queue:
                    session_id = self._improvement_queue.pop(0)
            
            if not session_id:
                break
            
            try:
                self._improve_session_name_background(session_id)
            except Exception as e:
                logger.error(f"Failed to improve session name in background: {e}")
    
    def _improve_session_name_background(self, session_id: str):
        """Improve session name in background thread"""
        try:
            # Load session
            session = self.storage.load_session(session_id)
            if not session:
                return
            
            # Improve name
            improved_name = self.name_improver.improve_session_name(session)
            
            if improved_name:
                session.set_name(improved_name)
                session.auto_named = False  # Mark as improved, not auto-generated
                self.storage.save_session(session)
                
                # Update current session if it's the same
                if self._current_session and self._current_session.id == session_id:
                    self._current_session.set_name(improved_name)
                    self._current_session.auto_named = False
                
                logger.info(f"Background improved session name: {session_id} -> '{improved_name}'")
        
        except Exception as e:
            logger.error(f"Background name improvement failed for {session_id}: {e}")
    
    def force_improve_session_name(self, session_id: str) -> Optional[str]:
        """
        Force immediate session name improvement (synchronous)
        
        Args:
            session_id: ID of session to improve
            
        Returns:
            Improved name or None if improvement fails
        """
        if not self.name_improver:
            logger.warning("Name improver not available")
            return None
        
        try:
            # Load session if not current
            if self._current_session and self._current_session.id == session_id:
                session = self._current_session
            else:
                session = self.storage.load_session(session_id)
            
            if not session:
                logger.error(f"Session not found for improvement: {session_id}")
                return None
            
            # Force improvement
            improved_name = self.name_improver.improve_session_name(session)
            
            if improved_name:
                session.set_name(improved_name)
                session.auto_named = False
                self.storage.save_session(session)
                
                logger.info(f"Force improved session name: {session_id} -> '{improved_name}'")
                return improved_name
            
        except Exception as e:
            logger.error(f"Force name improvement failed for {session_id}: {e}")
        
        return None
    
    def _init_session_analytics(self, session_id: str):
        """Initialize analytics for a session"""
        self._session_analytics[session_id] = {
            'created_at': datetime.now(),
            'user_messages': 0,
            'assistant_messages': 0,
            'total_characters': 0,
            'kb_switches': 0,
            'document_uploads': 0,
            'last_activity': datetime.now()
        }
    
    def _update_session_analytics(self, session_id: str, message_role: str):
        """Update session analytics"""
        if session_id not in self._session_analytics:
            self._init_session_analytics(session_id)
        
        analytics = self._session_analytics[session_id]
        analytics['last_activity'] = datetime.now()
        
        if message_role == 'user':
            analytics['user_messages'] += 1
        elif message_role == 'assistant':
            analytics['assistant_messages'] += 1
    
    def get_session_analytics(self, session_id: str) -> Dict:
        """Get analytics for a session"""
        return self._session_analytics.get(session_id, {})
    
    def get_global_analytics(self) -> Dict:
        """Get global session analytics"""
        try:
            sessions = self.list_sessions()
            total_sessions = len(sessions)
            
            # Calculate aggregate stats
            total_messages = sum(s.get('message_count', 0) for s in sessions)
            total_documents = sum(s.get('document_count', 0) for s in sessions)
            
            # Active sessions (used in last 7 days)
            week_ago = datetime.now() - timedelta(days=7)
            active_sessions = [
                s for s in sessions 
                if datetime.fromisoformat(s['last_active']) > week_ago
            ]
            
            # Most used KBs
            kb_usage = {}
            for session in sessions:
                kb_name = session.get('knowledge_base_name')
                if kb_name:
                    kb_usage[kb_name] = kb_usage.get(kb_name, 0) + 1
            
            return {
                'total_sessions': total_sessions,
                'active_sessions': len(active_sessions),
                'total_messages': total_messages,
                'total_documents': total_documents,
                'most_used_kbs': sorted(kb_usage.items(), key=lambda x: x[1], reverse=True)[:5],
                'average_messages_per_session': total_messages / total_sessions if total_sessions > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get global analytics: {e}")
            return {}
    
    def cleanup_and_optimize(self) -> Dict[str, int]:
        """
        Perform cleanup and optimization tasks
        
        Returns:
            Dictionary with cleanup statistics
        """
        results = {
            'sessions_cleaned': 0,
            'sessions_optimized': 0,
            'errors': 0
        }
        
        try:
            # Clean up old empty sessions
            cleaned = self.cleanup_old_empty_sessions(24)
            results['sessions_cleaned'] = cleaned
            
            # Optimize session names
            sessions = self.list_sessions()
            for session_meta in sessions:
                try:
                    session_id = session_meta['id']
                    session = self.storage.load_session(session_id)
                    
                    if session and session.auto_named and session.name == "New Session":
                        # Try to improve generic names
                        if self.name_improver:
                            improved = self.force_improve_session_name(session_id)
                            if improved:
                                results['sessions_optimized'] += 1
                
                except Exception as e:
                    logger.error(f"Failed to optimize session {session_id}: {e}")
                    results['errors'] += 1
            
            logger.info(f"Cleanup completed: {results}")
            
        except Exception as e:
            logger.error(f"Cleanup and optimization failed: {e}")
            results['errors'] += 1
        
        return results
    
    def search_sessions(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search sessions by content
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching session metadata
        """
        try:
            query_lower = query.lower()
            all_sessions = self.list_sessions()
            matches = []
            
            for session_meta in all_sessions:
                score = 0
                
                # Search in session name
                if query_lower in session_meta['name'].lower():
                    score += 10
                
                # Search in KB name
                kb_name = session_meta.get('knowledge_base_name', '')
                if kb_name and query_lower in kb_name.lower():
                    score += 5
                
                # Load session to search messages (expensive, so only if needed)
                if score == 0:
                    try:
                        session = self.storage.load_session(session_meta['id'])
                        if session:
                            # Search in messages
                            for message in session.messages:
                                if query_lower in message.content.lower():
                                    score += 1
                                    break  # Don't count multiple matches in same session
                    except Exception:
                        continue  # Skip sessions that fail to load
                
                if score > 0:
                    session_meta['search_score'] = score
                    matches.append(session_meta)
            
            # Sort by score and limit
            matches.sort(key=lambda x: x['search_score'], reverse=True)
            return matches[:limit]
            
        except Exception as e:
            logger.error(f"Session search failed: {e}")
            return []
    
    def get_session_recommendations(self, current_session_id: Optional[str] = None) -> List[Dict]:
        """
        Get session recommendations based on current context
        
        Args:
            current_session_id: ID of current session for context
            
        Returns:
            List of recommended session metadata
        """
        try:
            all_sessions = self.list_sessions()
            current_session = None
            
            # Get current session context
            if current_session_id:
                current_session = self.storage.load_session(current_session_id)
            
            recommendations = []
            
            # Recommend sessions with same KB
            if current_session and current_session.knowledge_base_name:
                kb_sessions = [
                    s for s in all_sessions 
                    if (s.get('knowledge_base_name') == current_session.knowledge_base_name and 
                        s['id'] != current_session_id)
                ]
                for session in kb_sessions[:3]:
                    session['recommendation_reason'] = f"Same KB: {current_session.knowledge_base_name}"
                    recommendations.append(session)
            
            # Recommend recently active sessions
            week_ago = datetime.now() - timedelta(days=7)
            recent_sessions = [
                s for s in all_sessions[:5]  # Top 5 recent
                if (datetime.fromisoformat(s['last_active']) > week_ago and 
                    s['id'] != current_session_id and
                    s not in recommendations)
            ]
            for session in recent_sessions[:2]:
                session['recommendation_reason'] = "Recently active"
                recommendations.append(session)
            
            # Recommend sessions with documents
            doc_sessions = [
                s for s in all_sessions
                if (s.get('document_count', 0) > 0 and 
                    s['id'] != current_session_id and
                    s not in recommendations)
            ]
            for session in doc_sessions[:2]:
                session['recommendation_reason'] = f"{session['document_count']} documents"
                recommendations.append(session)
            
            return recommendations[:5]  # Limit to 5 recommendations
            
        except Exception as e:
            logger.error(f"Failed to get session recommendations: {e}")
            return []
    
    def export_session_advanced(self, session_id: str, export_format: str = "markdown") -> Optional[str]:
        """
        Advanced session export with multiple formats
        
        Args:
            session_id: ID of session to export
            export_format: Export format ("markdown", "json", "html")
            
        Returns:
            Export content or None if export fails
        """
        try:
            session = self.storage.load_session(session_id)
            if not session:
                return None
            
            if export_format == "markdown":
                return self._export_to_markdown(session)
            elif export_format == "json":
                return self._export_to_json(session)
            elif export_format == "html":
                return self._export_to_html(session)
            else:
                logger.error(f"Unsupported export format: {export_format}")
                return None
                
        except Exception as e:
            logger.error(f"Advanced export failed for {session_id}: {e}")
            return None
    
    def _export_to_markdown(self, session: Session) -> str:
        """Export session to Markdown format"""
        lines = [
            f"# {session.name}",
            f"**Session ID:** {session.id}",
            f"**Created:** {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Last Active:** {session.last_active.strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]
        
        # Add context info
        if session.knowledge_base_name:
            lines.append(f"**Knowledge Base:** {session.knowledge_base_name}")
        
        if session.documents:
            lines.append(f"**Documents:** {len(session.documents)}")
            for doc in session.documents:
                lines.append(f"  - {doc.original_name}")
        
        lines.extend(["", "---", "", "## Conversation", ""])
        
        # Add messages
        for i, message in enumerate(session.messages):
            if message.role == "system":
                continue
                
            role_icon = "👤" if message.role == "user" else "🤖"
            lines.extend([
                f"### {role_icon} {message.role.title()}",
                f"*{message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*",
                "",
                message.content
            ])
            
            if message.role == "assistant" and message.sources:
                lines.extend(["", "**Sources:**"])
                for source in message.sources:
                    lines.append(f"- {source}")
            
            lines.extend(["", "---", ""])
        
        return "\n".join(lines)
    
    def _export_to_json(self, session: Session) -> str:
        """Export session to JSON format"""
        import json
        
        export_data = session.to_dict()
        export_data['exported_at'] = datetime.now().isoformat()
        export_data['export_format'] = 'json'
        
        return json.dumps(export_data, indent=2, ensure_ascii=False)
    
    def _export_to_html(self, session: Session) -> str:
        """Export session to HTML format"""
        html_lines = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            f"    <title>{session.name}</title>",
            "    <meta charset='utf-8'>",
            "    <style>",
            "        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }",
            "        .message { margin: 20px 0; padding: 15px; border-radius: 8px; }",
            "        .user { background: #e3f2fd; border-left: 4px solid #2196f3; }",
            "        .assistant { background: #f3e5f5; border-left: 4px solid #9c27b0; }",
            "        .timestamp { color: #666; font-size: 0.9em; }",
            "        .sources { margin-top: 10px; font-size: 0.9em; color: #444; }",
            "    </style>",
            "</head>",
            "<body>",
            f"    <h1>{session.name}</h1>",
            f"    <p><strong>Created:</strong> {session.created_at.strftime('%Y-%m-%d %H:%M:%S')}</p>"
        ]
        
        if session.knowledge_base_name:
            html_lines.append(f"    <p><strong>Knowledge Base:</strong> {session.knowledge_base_name}</p>")
        
        if session.documents:
            html_lines.append(f"    <p><strong>Documents:</strong> {len(session.documents)}</p>")
        
        html_lines.append("    <hr>")
        
        # Add messages
        for message in session.messages:
            if message.role == "system":
                continue
                
            css_class = "user" if message.role == "user" else "assistant"
            role_name = "You" if message.role == "user" else "Assistant"
            
            html_lines.extend([
                f"    <div class='message {css_class}'>",
                f"        <strong>{role_name}</strong>",
                f"        <div class='timestamp'>{message.timestamp.strftime('%Y-%m-%d %H:%M:%S')}</div>",
                f"        <p>{message.content.replace(chr(10), '<br>')}</p>"
            ])
            
            if message.role == "assistant" and message.sources:
                html_lines.append("        <div class='sources'><strong>Sources:</strong>")
                for source in message.sources:
                    html_lines.append(f"            <br>• {source}")
                html_lines.append("        </div>")
            
            html_lines.append("    </div>")
        
        html_lines.extend(["</body>", "</html>"])
        return "\n".join(html_lines)
    
    def batch_operations(self, operation: str, session_ids: List[str], **kwargs) -> Dict[str, any]:
        """
        Perform batch operations on multiple sessions
        
        Args:
            operation: Operation to perform ("delete", "export", "improve_names")
            session_ids: List of session IDs to operate on
            **kwargs: Additional operation parameters
            
        Returns:
            Dictionary with operation results
        """
        results = {
            'successful': [],
            'failed': [],
            'total': len(session_ids)
        }
        
        try:
            for session_id in session_ids:
                try:
                    if operation == "delete":
                        success = self.delete_session(session_id)
                        if success:
                            results['successful'].append(session_id)
                        else:
                            results['failed'].append(session_id)
                    
                    elif operation == "export":
                        export_format = kwargs.get('format', 'markdown')
                        content = self.export_session_advanced(session_id, export_format)
                        if content:
                            results['successful'].append({
                                'session_id': session_id,
                                'content': content
                            })
                        else:
                            results['failed'].append(session_id)
                    
                    elif operation == "improve_names":
                        improved_name = self.force_improve_session_name(session_id)
                        if improved_name:
                            results['successful'].append({
                                'session_id': session_id,
                                'new_name': improved_name
                            })
                        else:
                            results['failed'].append(session_id)
                    
                    else:
                        logger.error(f"Unknown batch operation: {operation}")
                        results['failed'].append(session_id)
                
                except Exception as e:
                    logger.error(f"Batch operation {operation} failed for {session_id}: {e}")
                    results['failed'].append(session_id)
            
            logger.info(f"Batch operation {operation} completed: {len(results['successful'])} successful, {len(results['failed'])} failed")
            
        except Exception as e:
            logger.error(f"Batch operation {operation} failed: {e}")
        
        return results
    
    def get_usage_statistics(self, days: int = 30) -> Dict[str, any]:
        """
        Get detailed usage statistics
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with usage statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            sessions = self.list_sessions()
            
            # Filter sessions within date range
            recent_sessions = [
                s for s in sessions
                if datetime.fromisoformat(s['last_active']) > cutoff_date
            ]
            
            # Calculate statistics
            total_messages = sum(s.get('message_count', 0) for s in recent_sessions)
            total_documents = sum(s.get('document_count', 0) for s in recent_sessions)
            
            # KB usage
            kb_usage = {}
            for session in recent_sessions:
                kb_name = session.get('knowledge_base_name')
                if kb_name:
                    if kb_name not in kb_usage:
                        kb_usage[kb_name] = {'sessions': 0, 'messages': 0}
                    kb_usage[kb_name]['sessions'] += 1
                    kb_usage[kb_name]['messages'] += session.get('message_count', 0)
            
            # Daily activity
            daily_activity = {}
            for session in recent_sessions:
                date_str = datetime.fromisoformat(session['last_active']).strftime('%Y-%m-%d')
                if date_str not in daily_activity:
                    daily_activity[date_str] = {'sessions': 0, 'messages': 0}
                daily_activity[date_str]['sessions'] += 1
                daily_activity[date_str]['messages'] += session.get('message_count', 0)
            
            return {
                'period_days': days,
                'total_sessions': len(recent_sessions),
                'total_messages': total_messages,
                'total_documents': total_documents,
                'average_messages_per_session': total_messages / len(recent_sessions) if recent_sessions else 0,
                'kb_usage': dict(sorted(kb_usage.items(), key=lambda x: x[1]['sessions'], reverse=True)),
                'daily_activity': daily_activity,
                'most_active_day': max(daily_activity.items(), key=lambda x: x[1]['sessions']) if daily_activity else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get usage statistics: {e}")
            return {}
    
    def __del__(self):
        """Cleanup when manager is destroyed"""
        try:
            # Wait for improvement thread to finish
            if self._improvement_thread and self._improvement_thread.is_alive():
                self._improvement_thread.join(timeout=1)
        except Exception:
            pass  # Ignore cleanup errors