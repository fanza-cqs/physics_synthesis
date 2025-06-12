#!/usr/bin/env python3
"""
Progress tracking utility for Knowledge Base operations.

Location: src/utils/progress_tracker.py
"""

import time
import json
from pathlib import Path
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, asdict
from enum import Enum

from .logging_config import get_logger

logger = get_logger(__name__)

class OperationStatus(Enum):
    """Status of KB operation."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ProgressState:
    """Current state of a KB operation."""
    operation_id: str
    kb_name: str
    operation_type: str
    status: OperationStatus
    current_step: str
    progress_percentage: float
    start_time: float
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    sources_total: int = 0
    sources_completed: int = 0
    documents_processed: int = 0
    documents_total: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProgressState':
        """Create from dictionary."""
        data['status'] = OperationStatus(data['status'])
        return cls(**data)

class ProgressTracker:
    """
    Tracks progress of knowledge base operations with file persistence.
    
    Provides real-time progress updates and survives application crashes.
    """
    
    def __init__(self, storage_dir: Path = None):
        """
        Initialize progress tracker.
        
        Args:
            storage_dir: Directory to store progress files
        """
        self.storage_dir = storage_dir or Path("progress")
        self.storage_dir.mkdir(exist_ok=True)
        
        self.current_operation: Optional[ProgressState] = None
        self.callbacks: list[Callable[[ProgressState], None]] = []
        
        logger.info(f"Progress tracker initialized with storage: {self.storage_dir}")
    
    def add_callback(self, callback: Callable[[ProgressState], None]):
        """Add a callback function to be called on progress updates."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ProgressState], None]):
        """Remove a callback function."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def start_operation(self, 
                       operation_id: str,
                       kb_name: str,
                       operation_type: str,
                       sources_total: int = 0,
                       documents_total: int = 0) -> ProgressState:
        """
        Start tracking a new operation.
        
        Args:
            operation_id: Unique identifier for the operation
            kb_name: Name of the knowledge base
            operation_type: Type of operation (create/update/etc.)
            sources_total: Total number of sources to process
            documents_total: Total number of documents expected
            
        Returns:
            ProgressState for the new operation
        """
        self.current_operation = ProgressState(
            operation_id=operation_id,
            kb_name=kb_name,
            operation_type=operation_type,
            status=OperationStatus.IN_PROGRESS,
            current_step="Starting...",
            progress_percentage=0.0,
            start_time=time.time(),
            sources_total=sources_total,
            documents_total=documents_total
        )
        
        self._save_progress()
        self._notify_callbacks()
        
        logger.info(f"Started tracking operation: {operation_id} for KB: {kb_name}")
        return self.current_operation
    
    def update_progress(self, 
                       step: str,
                       progress_percentage: float,
                       sources_completed: int = None,
                       documents_processed: int = None):
        """
        Update progress of current operation.
        
        Args:
            step: Current step description
            progress_percentage: Progress as percentage (0-100)
            sources_completed: Number of sources completed
            documents_processed: Number of documents processed
        """
        if not self.current_operation:
            logger.warning("Attempted to update progress with no active operation")
            return
        
        self.current_operation.current_step = step
        self.current_operation.progress_percentage = min(100.0, max(0.0, progress_percentage))
        
        if sources_completed is not None:
            self.current_operation.sources_completed = sources_completed
        
        if documents_processed is not None:
            self.current_operation.documents_processed = documents_processed
        
        self._save_progress()
        self._notify_callbacks()
        
        logger.debug(f"Progress update: {progress_percentage:.1f}% - {step}")
    
    def complete_operation(self, success: bool = True, error_message: str = None):
        """
        Mark current operation as completed.
        
        Args:
            success: Whether operation completed successfully
            error_message: Error message if operation failed
        """
        if not self.current_operation:
            logger.warning("Attempted to complete operation with no active operation")
            return
        
        self.current_operation.end_time = time.time()
        self.current_operation.progress_percentage = 100.0 if success else self.current_operation.progress_percentage
        self.current_operation.status = OperationStatus.COMPLETED if success else OperationStatus.FAILED
        
        if error_message:
            self.current_operation.error_message = error_message
        
        if success:
            self.current_operation.current_step = "Operation completed successfully"
        else:
            self.current_operation.current_step = f"Operation failed: {error_message or 'Unknown error'}"
        
        self._save_progress()
        self._notify_callbacks()
        
        operation_time = self.current_operation.end_time - self.current_operation.start_time
        logger.info(f"Operation {self.current_operation.operation_id} completed in {operation_time:.1f}s")
        
        # Keep reference for final callbacks, then clear
        completed_operation = self.current_operation
        self.current_operation = None
        
        return completed_operation
    
    def cancel_operation(self, reason: str = "Cancelled by user"):
        """
        Cancel the current operation.
        
        Args:
            reason: Reason for cancellation
        """
        if not self.current_operation:
            logger.warning("Attempted to cancel operation with no active operation")
            return
        
        self.current_operation.status = OperationStatus.CANCELLED
        self.current_operation.current_step = f"Cancelled: {reason}"
        self.current_operation.error_message = reason
        self.current_operation.end_time = time.time()
        
        self._save_progress()
        self._notify_callbacks()
        
        logger.info(f"Operation {self.current_operation.operation_id} cancelled: {reason}")
        
        cancelled_operation = self.current_operation
        self.current_operation = None
        
        return cancelled_operation
    
    def get_current_progress(self) -> Optional[ProgressState]:
        """Get current operation progress."""
        return self.current_operation
    
    def load_operation(self, operation_id: str) -> Optional[ProgressState]:
        """
        Load a previously saved operation.
        
        Args:
            operation_id: ID of operation to load
            
        Returns:
            ProgressState if found, None otherwise
        """
        progress_file = self.storage_dir / f"{operation_id}.json"
        
        if not progress_file.exists():
            return None
        
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
            
            progress_state = ProgressState.from_dict(data)
            
            # If operation was in progress when saved, mark as failed
            if progress_state.status == OperationStatus.IN_PROGRESS:
                progress_state.status = OperationStatus.FAILED
                progress_state.error_message = "Operation interrupted"
            
            return progress_state
            
        except Exception as e:
            logger.error(f"Error loading operation {operation_id}: {e}")
            return None
    
    def list_recent_operations(self, limit: int = 10) -> list[ProgressState]:
        """
        List recent operations.
        
        Args:
            limit: Maximum number of operations to return
            
        Returns:
            List of recent ProgressState objects
        """
        operations = []
        
        try:
            progress_files = list(self.storage_dir.glob("*.json"))
            progress_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for progress_file in progress_files[:limit]:
                operation_id = progress_file.stem
                operation = self.load_operation(operation_id)
                if operation:
                    operations.append(operation)
        
        except Exception as e:
            logger.error(f"Error listing recent operations: {e}")
        
        return operations
    
    def cleanup_old_operations(self, max_age_days: int = 30):
        """
        Clean up old operation files.
        
        Args:
            max_age_days: Maximum age of files to keep
        """
        try:
            cutoff_time = time.time() - (max_age_days * 24 * 60 * 60)
            
            for progress_file in self.storage_dir.glob("*.json"):
                if progress_file.stat().st_mtime < cutoff_time:
                    progress_file.unlink()
                    logger.debug(f"Cleaned up old progress file: {progress_file}")
        
        except Exception as e:
            logger.error(f"Error cleaning up old operations: {e}")
    
    def _save_progress(self):
        """Save current progress to file."""
        if not self.current_operation:
            return
        
        progress_file = self.storage_dir / f"{self.current_operation.operation_id}.json"
        
        try:
            with open(progress_file, 'w') as f:
                json.dump(self.current_operation.to_dict(), f, indent=2)
        
        except Exception as e:
            logger.error(f"Error saving progress: {e}")
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of progress update."""
        if not self.current_operation:
            return
        
        for callback in self.callbacks:
            try:
                callback(self.current_operation)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

class ProgressManager:
    """
    Singleton progress manager for global access.
    """
    _instance = None
    _tracker = None
    
    @classmethod
    def get_instance(cls, storage_dir: Path = None) -> ProgressTracker:
        """Get singleton progress tracker instance."""
        if cls._instance is None:
            cls._instance = ProgressTracker(storage_dir)
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance (for testing)."""
        cls._instance = None

def create_operation_id(kb_name: str, operation_type: str) -> str:
    """
    Create a unique operation ID.
    
    Args:
        kb_name: Knowledge base name
        operation_type: Type of operation
        
    Returns:
        Unique operation ID
    """
    timestamp = str(int(time.time()))
    return f"{operation_type}_{kb_name}_{timestamp}"

def format_duration(seconds: float) -> str:
    """
    Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"

def format_progress_message(progress_state: ProgressState) -> str:
    """
    Format progress state into human-readable message.
    
    Args:
        progress_state: Current progress state
        
    Returns:
        Formatted progress message
    """
    status_emoji = {
        OperationStatus.IN_PROGRESS: "🔄",
        OperationStatus.COMPLETED: "✅",
        OperationStatus.FAILED: "❌",
        OperationStatus.CANCELLED: "⏹️",
        OperationStatus.NOT_STARTED: "⏳"
    }
    
    emoji = status_emoji.get(progress_state.status, "❓")
    
    message = f"{emoji} {progress_state.current_step}"
    
    if progress_state.status == OperationStatus.IN_PROGRESS:
        message += f" ({progress_state.progress_percentage:.1f}%)"
        
        if progress_state.sources_total > 0:
            message += f" - Sources: {progress_state.sources_completed}/{progress_state.sources_total}"
        
        if progress_state.documents_total > 0:
            message += f" - Docs: {progress_state.documents_processed}/{progress_state.documents_total}"
    
    elif progress_state.status in [OperationStatus.COMPLETED, OperationStatus.FAILED] and progress_state.end_time:
        duration = progress_state.end_time - progress_state.start_time
        message += f" ({format_duration(duration)})"
    
    return message