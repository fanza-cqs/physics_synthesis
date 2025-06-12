#!/usr/bin/env python3
"""
Frontend Integration Module for Unified KB Creation System.

Integrates the orchestrator with the Streamlit frontend components.

Location: frontend_streamlit/integration/kb_integration.py
"""

import streamlit as st
from typing import Optional, Dict, Any, Callable
import time
import asyncio
from pathlib import Path

from config.settings import PipelineConfig
from src.core import (
    KnowledgeBaseOrchestrator,
    KBOperation,
    SourceSelection,
    list_knowledge_bases
)
from src.utils.progress_tracker import (
    ProgressManager,
    create_operation_id,
    ProgressState,
    OperationStatus
)
from src.utils.kb_validation import (
    validate_kb_name,
    validate_source_selection,
    validate_existing_kb,
    generate_summary_text
)

class KBCreationIntegration:
    """
    Integration layer between frontend components and backend orchestrator.
    
    Handles the complete KB creation workflow with progress tracking,
    error handling, and user feedback.
    """
    
    def __init__(self):
        """Initialize the KB creation integration."""
        self.config = st.session_state.get('config')
        if not self.config:
            raise ValueError("Configuration not available in session state")
        
        self.orchestrator = KnowledgeBaseOrchestrator(self.config)
        self.progress_manager = ProgressManager.get_instance()
        
        # UI components placeholders
        self.progress_container = None
        self.status_container = None
        self.result_container = None
    
    def setup_ui_containers(self):
        """Set up UI containers for progress tracking."""
        self.progress_container = st.empty()
        self.status_container = st.empty()
        self.result_container = st.empty()
        
        return {
            'progress': self.progress_container,
            'status': self.status_container,
            'result': self.result_container
        }
    
    def validate_inputs(self,
                       operation: KBOperation,
                       kb_name: str,
                       existing_kb_name: Optional[str],
                       source_selection: SourceSelection) -> tuple[bool, list]:
        """
        Validate all inputs for KB creation.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate KB name
        name_validation = validate_kb_name(kb_name)
        if not name_validation.is_valid:
            errors.extend(name_validation.error_messages)
        
        # Validate source selection
        source_validation = validate_source_selection(source_selection)
        if not source_validation.is_valid:
            errors.extend(source_validation.error_messages)
        
        # Validate existing KB if needed
        if operation in [KBOperation.REPLACE_EXISTING, KBOperation.ADD_TO_EXISTING]:
            if not existing_kb_name:
                errors.append("Existing KB name required for this operation")
            else:
                existing_validation = validate_existing_kb(
                    existing_kb_name, 
                    self.config.knowledge_bases_folder
                )
                if not existing_validation.is_valid:
                    errors.extend(existing_validation.error_messages)
        
        # Check for name conflicts
        if operation == KBOperation.CREATE_NEW:
            available_kbs = list_knowledge_bases(self.config.knowledge_bases_folder)
            existing_names = [kb['name'] for kb in available_kbs]
            if kb_name in existing_names:
                errors.append(f"Knowledge base '{kb_name}' already exists")
        
        return len(errors) == 0, errors
    
    def run_preprocessing_preview(self, source_selection: SourceSelection) -> Optional[Dict]:
        """
        Run preprocessing and return results for user confirmation.
        
        Returns:
            Dictionary with preprocessing results or None if failed
        """
        try:
            with st.spinner("🔍 Scanning selected sources..."):
                preprocessing = self.orchestrator.preprocess_sources(source_selection)
            
            if preprocessing.has_valid_sources:
                # Store results in session state
                st.session_state.preprocessing_results = {
                    'summary': preprocessing,
                    'timestamp': time.time(),
                    'source_selection': source_selection
                }
                
                return {
                    'success': True,
                    'summary': preprocessing,
                    'summary_text': generate_summary_text(preprocessing)
                }
            else:
                return {
                    'success': False,
                    'errors': preprocessing.error_messages
                }
                
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Preprocessing error: {str(e)}"]
            }
    
    def run_kb_creation(self,
                       operation: KBOperation,
                       kb_name: str,
                       existing_kb_name: Optional[str],
                       source_selection: SourceSelection) -> Dict[str, Any]:
        """
        Run the complete KB creation process with progress tracking.
        
        Returns:
            Dictionary with operation results
        """
        # Validate inputs first
        is_valid, errors = self.validate_inputs(
            operation, kb_name, existing_kb_name, source_selection
        )
        
        if not is_valid:
            return {
                'success': False,
                'errors': errors
            }
        
        # Create operation ID
        operation_id = create_operation_id(kb_name, operation.value)
        
        # Set up progress tracking
        containers = self.setup_ui_containers()
        
        # Initialize progress state in session
        progress_state = self.progress_manager.start_operation(
            operation_id=operation_id,
            kb_name=kb_name,
            operation_type=operation.value,
            sources_total=self._count_selected_sources(source_selection)
        )
        
        st.session_state.current_progress_state = progress_state
        
        # Set up progress callback
        def progress_callback(message: str, percentage: float):
            self._update_progress_display(message, percentage, containers)
        
        self.orchestrator.set_progress_callback(progress_callback)
        
        try:
            # Show initial progress
            self._show_progress_start(containers, operation, kb_name)
            
            # Run the orchestration
            result = self.orchestrator.create_knowledge_base(
                kb_name=kb_name,
                source_selection=source_selection,
                operation=operation,
                existing_kb_name=existing_kb_name
            )
            
            # Complete progress tracking
            if result.success:
                self.progress_manager.complete_operation(success=True)
                self._show_success_result(containers, result)
            else:
                error_msg = "; ".join(result.error_messages)
                self.progress_manager.complete_operation(
                    success=False, 
                    error_message=error_msg
                )
                self._show_error_result(containers, result)
            
            return {
                'success': result.success,
                'result': result,
                'operation_id': operation_id
            }
            
        except Exception as e:
            # Handle unexpected errors
            self.progress_manager.complete_operation(
                success=False,
                error_message=str(e)
            )
            
            self._show_exception_result(containers, e)
            
            return {
                'success': False,
                'errors': [f"Unexpected error: {str(e)}"],
                'operation_id': operation_id
            }
    
    def _count_selected_sources(self, source_selection: SourceSelection) -> int:
        """Count number of selected sources."""
        count = 0
        if source_selection.use_local_folders:
            count += 1
        if source_selection.use_zotero:
            count += 1
        if source_selection.use_custom_folder:
            count += 1
        return count
    
    def _update_progress_display(self, message: str, percentage: float, containers: Dict):
        """Update the progress display."""
        # Update progress bar
        with containers['progress']:
            st.progress(percentage / 100.0, text=f"{percentage:.1f}% - {message}")
        
        # Update status
        with containers['status']:
            status_html = f"""
            <div style="background: #f0f9ff; padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 0.5rem 0;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">🔄</span>
                    <strong>{message}</strong>
                </div>
                <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">
                    Progress: {percentage:.1f}%
                </div>
            </div>
            """
            st.markdown(status_html, unsafe_allow_html=True)
    
    def _show_progress_start(self, containers: Dict, operation: KBOperation, kb_name: str):
        """Show initial progress state."""
        with containers['status']:
            start_html = f"""
            <div style="background: #fffbeb; padding: 1rem; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 0.5rem 0;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.2rem; margin-right: 0.5rem;">🚀</span>
                    <strong>Starting {operation.value.replace('_', ' ').title()}</strong>
                </div>
                <div style="font-size: 0.875rem; color: #6b7280; margin-top: 0.25rem;">
                    Knowledge Base: {kb_name}
                </div>
            </div>
            """
            st.markdown(start_html, unsafe_allow_html=True)
    
    def _show_success_result(self, containers: Dict, result):
        """Show successful completion result."""
        # Clear progress
        containers['progress'].empty()
        
        # Show success status
        with containers['status']:
            success_html = f"""
            <div style="background: #f0f9ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #10b981; margin: 1rem 0;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="font-size: 2rem; margin-right: 1rem;">🎉</span>
                    <div>
                        <h3 style="margin: 0; color: #059669;">Knowledge Base Created Successfully!</h3>
                        <p style="margin: 0.25rem 0 0 0; color: #6b7280;">
                            Processing completed in {result.processing_time:.1f} seconds
                        </p>
                    </div>
                </div>
            </div>
            """
            st.markdown(success_html, unsafe_allow_html=True)
        
        # Show detailed results
        with containers['result']:
            st.markdown("### 🏆 Creation Results")
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 Documents", result.total_documents)
            
            with col2:
                st.metric("🧩 Chunks", result.total_chunks)
            
            with col3:
                st.metric("⏱️ Time", f"{result.processing_time:.1f}s")
            
            # Details
            st.info(f"**Knowledge Base:** `{result.kb_name}`")
            if result.kb_path:
                st.info(f"**Location:** `{result.kb_path}`")
            
            if result.sources_processed:
                st.success(f"**Sources processed:** {', '.join(result.sources_processed)}")
            
            if result.sources_failed:
                st.warning(f"**Sources failed:** {', '.join(result.sources_failed)}")
            
            if result.is_partial:
                st.warning("⚠️ **Partial creation:** Some sources failed, but KB was created with available data")
            
            # Action buttons
            st.markdown("### ⚡ Next Steps")
            
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("🔄 Use in Session", key="use_new_kb_success"):
                    st.session_state.current_kb = result.kb_name
                    st.success(f"✅ Now using KB: {result.kb_name}")
                    st.rerun()
            
            with action_col2:
                if st.button("📚 View Details", key="view_new_kb_details"):
                    st.session_state.show_kb_details = result.kb_name
                    st.info("💡 Go to **Browse & Manage** tab to view detailed information")
            
            with action_col3:
                if st.button("🆕 Create Another", key="create_another_kb"):
                    # Clear session state for new creation
                    for key in list(st.session_state.keys()):
                        if key.startswith(('kb_name', 'use_', 'include_', 'zotero_', 'custom_')):
                            del st.session_state[key]
                    st.rerun()
    
    def _show_error_result(self, containers: Dict, result):
        """Show error completion result."""
        # Clear progress
        containers['progress'].empty()
        
        # Show error status
        with containers['status']:
            error_html = f"""
            <div style="background: #fef2f2; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ef4444; margin: 1rem 0;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="font-size: 2rem; margin-right: 1rem;">❌</span>
                    <div>
                        <h3 style="margin: 0; color: #dc2626;">Knowledge Base Creation Failed</h3>
                        <p style="margin: 0.25rem 0 0 0; color: #6b7280;">
                            The operation encountered errors and could not complete
                        </p>
                    </div>
                </div>
            </div>
            """
            st.markdown(error_html, unsafe_allow_html=True)
        
        # Show error details
        with containers['result']:
            st.markdown("### ❌ Error Details")
            
            for error in result.error_messages:
                st.error(f"• {error}")
            
            # Show partial progress if any
            if result.total_documents > 0 or result.sources_processed:
                st.markdown("### 📊 Progress Before Error")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if result.total_documents > 0:
                        st.metric("Documents Processed", result.total_documents)
                
                with col2:
                    if result.sources_processed:
                        st.metric("Sources Completed", len(result.sources_processed))
                
                if result.sources_processed:
                    st.info(f"**Completed sources:** {', '.join(result.sources_processed)}")
            
            # Recovery suggestions
            st.markdown("### 💡 Suggested Actions")
            
            suggestions = []
            
            # Analyze errors for suggestions
            error_text = ' '.join(result.error_messages).lower()
            
            if 'zotero' in error_text:
                suggestions.append("🔗 Check Zotero connection and API credentials")
            
            if 'folder' in error_text or 'directory' in error_text:
                suggestions.append("📁 Verify folder paths and permissions")
            
            if 'permission' in error_text:
                suggestions.append("🔐 Check file and folder permissions")
            
            if not suggestions:
                suggestions.append("🔄 Try again with fewer sources")
                suggestions.append("📋 Check the logs for more detailed error information")
            
            for suggestion in suggestions:
                st.info(suggestion)
            
            # Retry button
            if st.button("🔄 Try Again", key="retry_kb_creation"):
                # Clear error state but keep form data
                if 'current_progress_state' in st.session_state:
                    del st.session_state['current_progress_state']
                st.rerun()
    
    def _show_exception_result(self, containers: Dict, exception: Exception):
        """Show unexpected exception result."""
        # Clear progress
        containers['progress'].empty()
        
        # Show exception status
        with containers['status']:
            exception_html = f"""
            <div style="background: #fef2f2; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ef4444; margin: 1rem 0;">
                <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                    <span style="font-size: 2rem; margin-right: 1rem;">💥</span>
                    <div>
                        <h3 style="margin: 0; color: #dc2626;">Unexpected Error</h3>
                        <p style="margin: 0.25rem 0 0 0; color: #6b7280;">
                            An unexpected error occurred during processing
                        </p>
                    </div>
                </div>
            </div>
            """
            st.markdown(exception_html, unsafe_allow_html=True)
        
        # Show exception details
        with containers['result']:
            st.markdown("### 💥 Exception Details")
            
            st.error(f"**Error Type:** {type(exception).__name__}")
            st.error(f"**Error Message:** {str(exception)}")
            
            # Show technical details in expander
            with st.expander("🔧 Technical Details", expanded=False):
                import traceback
                tb_str = traceback.format_exc()
                st.code(tb_str, language="python")
            
            st.markdown("### 💡 Troubleshooting")
            st.info("🔄 Try refreshing the page and attempting the operation again")
            st.info("📋 If the problem persists, check the application logs")
            st.info("🐛 Consider reporting this as a bug if it continues to occur")

def create_kb_creation_workflow():
    """
    Create a complete KB creation workflow component.
    
    This function can be called from the main KB management page
    to render the unified creation interface.
    """
    try:
        integration = KBCreationIntegration()
        
        # Store integration in session state for access by components
        st.session_state.kb_integration = integration
        
        return integration
        
    except Exception as e:
        st.error(f"❌ Failed to initialize KB creation workflow: {e}")
        return None

def handle_kb_creation_callback(
    operation: KBOperation,
    kb_name: str,
    existing_kb_name: Optional[str],
    source_selection: SourceSelection
) -> bool:
    """
    Handle KB creation callback from unified interface.
    
    This function is called when user confirms KB creation.
    
    Returns:
        True if creation was successful, False otherwise
    """
    integration = st.session_state.get('kb_integration')
    
    if not integration:
        st.error("❌ KB integration not available")
        return False
    
    # Run the creation process
    result = integration.run_kb_creation(
        operation=operation,
        kb_name=kb_name,
        existing_kb_name=existing_kb_name,
        source_selection=source_selection
    )
    
    return result['success']

def handle_preprocessing_callback(source_selection: SourceSelection) -> Optional[Dict]:
    """
    Handle preprocessing callback from unified interface.
    
    Returns:
        Preprocessing results dictionary or None if failed
    """
    integration = st.session_state.get('kb_integration')
    
    if not integration:
        st.error("❌ KB integration not available")
        return None
    
    return integration.run_preprocessing_preview(source_selection)

# CSS for integration components
def render_integration_css():
    """Render CSS for integration components."""
    st.markdown("""
    <style>
    /* Integration specific styles */
    .integration-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    }
    
    .progress-section {
        background: #f8fafc;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border: 1px solid #e2e8f0;
    }
    
    .status-update {
        animation: slideInFromLeft 0.3s ease-out;
        margin: 0.5rem 0;
    }
    
    @keyframes slideInFromLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .result-section {
        background: #f9fafb;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid #e5e7eb;
    }
    
    .success-celebration {
        animation: celebrationBounce 0.6s ease-out;
    }
    
    @keyframes celebrationBounce {
        0%, 20%, 50%, 80%, 100% {
            transform: translateY(0);
        }
        40% {
            transform: translateY(-10px);
        }
        60% {
            transform: translateY(-5px);
        }
    }
    
    .error-section {
        background: #fef2f2;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #ef4444;
    }
    
    .suggestion-item {
        background: white;
        padding: 0.75rem;
        margin: 0.5rem 0;
        border-radius: 4px;
        border-left: 3px solid #3b82f6;
    }
    
    /* Action buttons styling */
    .action-button-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .action-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        border: none;
        cursor: pointer;
        text-align: center;
        transition: transform 0.2s ease;
    }
    
    .action-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    
    /* Metrics styling */
    .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        border: 1px solid #e5e7eb;
        transition: transform 0.2s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 0.25rem;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #6b7280;
    }
    </style>
    """, unsafe_allow_html=True)