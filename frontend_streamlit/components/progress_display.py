#!/usr/bin/env python3
"""
Progress Display Component for Knowledge Base Creation.

Real-time progress tracking with visual feedback and status updates.

Location: frontend_streamlit/components/progress_display.py
"""

import streamlit as st
from typing import Optional, Dict, Any, Callable
import time
import threading

from src.utils.progress_tracker import (
    ProgressState, 
    OperationStatus,
    format_progress_message,
    format_duration
)

class ProgressDisplay:
    """
    Real-time progress display component for KB operations.
    
    Provides visual progress tracking with status updates, metrics,
    and error handling for knowledge base creation operations.
    """
    
    def __init__(self):
        """Initialize progress display component."""
        self.container = None
        self.progress_bar = None
        self.status_container = None
        self.metrics_container = None
        self.current_operation = None
    
    def setup_display(self, container=None) -> Dict[str, Any]:
        """
        Set up the progress display interface.
        
        Args:
            container: Streamlit container to render in (optional)
            
        Returns:
            Dictionary of display components for updates
        """
        if container:
            self.container = container
        else:
            self.container = st.container()
        
        with self.container:
            # Header
            st.markdown("### 🔄 Knowledge Base Creation Progress")
            
            # Progress bar
            self.progress_bar = st.progress(0.0, text="Initializing...")
            
            # Status container
            self.status_container = st.empty()
            
            # Metrics container (initially hidden)
            self.metrics_container = st.empty()
            
            # Details expander
            self.details_expander = st.expander("📋 Operation Details", expanded=False)
        
        return {
            'progress_bar': self.progress_bar,
            'status_container': self.status_container,
            'metrics_container': self.metrics_container,
            'details_container': self.details_expander
        }
    
    def update_progress(self, progress_state: ProgressState):
        """
        Update the progress display with new state.
        
        Args:
            progress_state: Current progress state
        """
        if not self.progress_bar or not self.status_container:
            return
        
        self.current_operation = progress_state
        
        # Update progress bar
        progress_value = progress_state.progress_percentage / 100.0
        progress_text = f"{progress_state.progress_percentage:.1f}% - {progress_state.current_step}"
        
        self.progress_bar.progress(progress_value, text=progress_text)
        
        # Update status
        self._update_status_display(progress_state)
        
        # Update metrics
        self._update_metrics_display(progress_state)
        
        # Update details
        self._update_details_display(progress_state)
    
    def show_completion(self, progress_state: ProgressState):
        """
        Show completion status and final results.
        
        Args:
            progress_state: Final progress state
        """
        if progress_state.status == OperationStatus.COMPLETED:
            self._show_success_completion(progress_state)
        elif progress_state.status == OperationStatus.FAILED:
            self._show_error_completion(progress_state)
        elif progress_state.status == OperationStatus.CANCELLED:
            self._show_cancelled_completion(progress_state)
    
    def clear_display(self):
        """Clear the progress display."""
        if self.container:
            self.container.empty()
        
        self.progress_bar = None
        self.status_container = None
        self.metrics_container = None
        self.current_operation = None
    
    def _update_status_display(self, progress_state: ProgressState):
        """Update the status display section."""
        status_icons = {
            OperationStatus.IN_PROGRESS: "🔄",
            OperationStatus.COMPLETED: "✅",
            OperationStatus.FAILED: "❌",
            OperationStatus.CANCELLED: "⏹️"
        }
        
        icon = status_icons.get(progress_state.status, "❓")
        
        # Calculate elapsed time
        elapsed = time.time() - progress_state.start_time
        elapsed_str = format_duration(elapsed)
        
        # Status message
        status_html = f"""
        <div style="background: #f8fafc; padding: 1rem; border-radius: 8px; border-left: 4px solid #3b82f6; margin: 1rem 0;">
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-size: 1.2rem; margin-right: 0.5rem;">{icon}</span>
                <strong>{progress_state.current_step}</strong>
            </div>
            <div style="font-size: 0.875rem; color: #6b7280;">
                Operation: {progress_state.operation_type} | KB: {progress_state.kb_name} | Elapsed: {elapsed_str}
            </div>
        </div>
        """
        
        self.status_container.markdown(status_html, unsafe_allow_html=True)
    
    def _update_metrics_display(self, progress_state: ProgressState):
        """Update the metrics display section."""
        # Only show metrics if we have meaningful data
        if (progress_state.sources_total > 0 or 
            progress_state.documents_total > 0 or 
            progress_state.documents_processed > 0):
            
            with self.metrics_container.container():
                st.markdown("#### 📊 Progress Metrics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if progress_state.sources_total > 0:
                        st.metric(
                            "Sources",
                            f"{progress_state.sources_completed}/{progress_state.sources_total}",
                            help="Sources processed vs total sources"
                        )
                
                with col2:
                    if progress_state.documents_total > 0:
                        st.metric(
                            "Documents",
                            f"{progress_state.documents_processed}/{progress_state.documents_total}",
                            help="Documents processed vs total expected"
                        )
                    else:
                        st.metric(
                            "Documents",
                            progress_state.documents_processed,
                            help="Documents processed so far"
                        )
                
                with col3:
                    progress_pct = progress_state.progress_percentage
                    st.metric(
                        "Progress",
                        f"{progress_pct:.1f}%",
                        help="Overall completion percentage"
                    )
                
                with col4:
                    elapsed = time.time() - progress_state.start_time
                    st.metric(
                        "Elapsed",
                        format_duration(elapsed),
                        help="Time since operation started"
                    )
    
    def _update_details_display(self, progress_state: ProgressState):
        """Update the details expander section."""
        with self.details_expander:
            # Operation info
            st.markdown("**Operation Information:**")
            info_data = {
                "Operation ID": progress_state.operation_id,
                "Type": progress_state.operation_type,
                "Knowledge Base": progress_state.kb_name,
                "Status": progress_state.status.value,
                "Started": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(progress_state.start_time))
            }
            
            for key, value in info_data.items():
                st.text(f"{key}: {value}")
            
            # Error information if applicable
            if progress_state.error_message:
                st.markdown("**Error Details:**")
                st.error(progress_state.error_message)
    
    def _show_success_completion(self, progress_state: ProgressState):
        """Show successful completion display."""
        # Clear progress bar
        if self.progress_bar:
            self.progress_bar.progress(1.0, text="✅ Completed successfully!")
        
        # Show success message
        duration = progress_state.end_time - progress_state.start_time if progress_state.end_time else 0
        duration_str = format_duration(duration)
        
        success_html = f"""
        <div style="background: #f0f9ff; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #10b981; margin: 1rem 0;">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 2rem; margin-right: 1rem;">🎉</span>
                <div>
                    <h3 style="margin: 0; color: #059669;">Knowledge Base Created Successfully!</h3>
                    <p style="margin: 0.25rem 0 0 0; color: #6b7280;">
                        Operation completed in {duration_str}
                    </p>
                </div>
            </div>
        </div>
        """
        
        self.status_container.markdown(success_html, unsafe_allow_html=True)
        
        # Show final metrics
        with self.metrics_container.container():
            st.markdown("#### 🏆 Final Results")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "📄 Documents Processed",
                    progress_state.documents_processed,
                    help="Total documents successfully processed"
                )
            
            with col2:
                st.metric(
                    "🎯 Sources Completed",
                    f"{progress_state.sources_completed}/{progress_state.sources_total}",
                    help="Sources successfully processed"
                )
            
            with col3:
                st.metric(
                    "⏱️ Processing Time",
                    duration_str,
                    help="Total time taken for operation"
                )
    
    def _show_error_completion(self, progress_state: ProgressState):
        """Show error completion display."""
        # Update progress bar to show error
        if self.progress_bar:
            self.progress_bar.progress(
                progress_state.progress_percentage / 100.0,
                text="❌ Operation failed"
            )
        
        # Show error message
        error_html = f"""
        <div style="background: #fef2f2; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #ef4444; margin: 1rem 0;">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 2rem; margin-right: 1rem;">❌</span>
                <div>
                    <h3 style="margin: 0; color: #dc2626;">Operation Failed</h3>
                    <p style="margin: 0.25rem 0 0 0; color: #6b7280;">
                        The knowledge base creation encountered an error
                    </p>
                </div>
            </div>
            
            <div style="background: white; padding: 1rem; border-radius: 4px; margin-top: 1rem;">
                <strong>Error:</strong> {progress_state.error_message or 'Unknown error occurred'}
            </div>
        </div>
        """
        
        self.status_container.markdown(error_html, unsafe_allow_html=True)
        
        # Show partial progress if any
        if progress_state.documents_processed > 0:
            with self.metrics_container.container():
                st.markdown("#### 📊 Progress Before Error")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Documents Processed",
                        progress_state.documents_processed,
                        help="Documents processed before error"
                    )
                
                with col2:
                    st.metric(
                        "Sources Completed",
                        f"{progress_state.sources_completed}/{progress_state.sources_total}",
                        help="Sources completed before error"
                    )
    
    def _show_cancelled_completion(self, progress_state: ProgressState):
        """Show cancelled completion display."""
        # Update progress bar
        if self.progress_bar:
            self.progress_bar.progress(
                progress_state.progress_percentage / 100.0,
                text="⏹️ Operation cancelled"
            )
        
        # Show cancellation message
        cancel_html = f"""
        <div style="background: #fffbeb; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 1rem 0;">
            <div style="display: flex; align-items: center; margin-bottom: 1rem;">
                <span style="font-size: 2rem; margin-right: 1rem;">⏹️</span>
                <div>
                    <h3 style="margin: 0; color: #d97706;">Operation Cancelled</h3>
                    <p style="margin: 0.25rem 0 0 0; color: #6b7280;">
                        The knowledge base creation was cancelled by user
                    </p>
                </div>
            </div>
        </div>
        """
        
        self.status_container.markdown(cancel_html, unsafe_allow_html=True)

def create_progress_callback(progress_display: ProgressDisplay) -> Callable[[str, float], None]:
    """
    Create a progress callback function for the orchestrator.
    
    Args:
        progress_display: ProgressDisplay instance to update
        
    Returns:
        Callback function that updates the display
    """
    def callback(message: str, percentage: float):
        # Create a minimal progress state for display
        # Note: In a real implementation, this would get the full state
        # from the progress tracker
        if hasattr(st.session_state, 'current_progress_state'):
            progress_state = st.session_state.current_progress_state
            progress_state.current_step = message
            progress_state.progress_percentage = percentage
            progress_display.update_progress(progress_state)
    
    return callback

def render_progress_display_css():
    """Render CSS for progress display component."""
    st.markdown("""
    <style>
    /* Progress display specific styles */
    .progress-container {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        margin: 1rem 0;
    }
    
    .status-display {
        background: #f8fafc;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
        border-left: 4px solid #3b82f6;
    }
    
    .status-display.success {
        background: #f0f9ff;
        border-left-color: #10b981;
    }
    
    .status-display.error {
        background: #fef2f2;
        border-left-color: #ef4444;
    }
    
    .status-display.warning {
        background: #fffbeb;
        border-left-color: #f59e0b;
    }
    
    /* Metrics styling */
    .progress-metrics {
        background: #f9fafb;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .metric-card {
        background: white;
        border-radius: 6px;
        padding: 0.75rem;
        border: 1px solid #e5e7eb;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1f2937;
    }
    
    .metric-label {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.25rem;
    }
    
    /* Progress bar customization */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #3b82f6 0%, #1d4ed8 100%);
        border-radius: 4px;
    }
    
    /* Animation for status updates */
    .status-update {
        animation: slideIn 0.3s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Completion celebration */
    .completion-success {
        animation: celebrationPulse 0.6s ease-out;
    }
    
    @keyframes celebrationPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    /* Error state styling */
    .error-details {
        background: white;
        border-radius: 4px;
        padding: 1rem;
        margin-top: 1rem;
        border: 1px solid #fecaca;
        font-family: monospace;
        font-size: 0.875rem;
    }
    
    /* Details expander styling */
    .operation-details {
        background: #f9fafb;
        border-radius: 6px;
        padding: 0.75rem;
        margin: 0.5rem 0;
    }
    
    .detail-item {
        display: flex;
        justify-content: space-between;
        margin: 0.25rem 0;
        padding: 0.25rem 0;
        border-bottom: 1px solid #e5e7eb;
    }
    
    .detail-label {
        font-weight: 500;
        color: #374151;
    }
    
    .detail-value {
        color: #6b7280;
        font-family: monospace;
        font-size: 0.875rem;
    }
    </style>
    """, unsafe_allow_html=True)