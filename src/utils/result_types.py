#!/usr/bin/env python3
"""
Standardized result types for consistent return values.

Provides common result objects to standardize function returns across the codebase.
This is additive - existing result handling continues to work.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time

@dataclass
class OperationResult:
    """Standard result object for operations."""
    success: bool
    message: str = ""
    data: Any = None
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def add_warning(self, warning: str):
        """Add a warning message."""
        self.warnings.append(warning)
    
    def add_metadata(self, key: str, value: Any):
        """Add metadata."""
        self.metadata[key] = value

@dataclass 
class ProcessingResult:
    """Result for document processing operations."""
    success: bool
    processed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_count(self) -> int:
        return self.processed_count + self.failed_count + self.skipped_count
    
    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.processed_count / self.total_count

@dataclass
class ValidationResult:
    """Result for validation operations."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    
    def add_error(self, error: str):
        """Add an error and mark as invalid."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning (doesn't affect validity)."""
        self.warnings.append(warning)

# Factory functions for common scenarios
def success_result(message: str = "Operation completed successfully", data: Any = None) -> OperationResult:
    """Create a success result."""
    return OperationResult(success=True, message=message, data=data)

def error_result(error: str, message: str = "Operation failed") -> OperationResult:
    """Create an error result."""
    return OperationResult(success=False, message=message, error=error)

def processing_success(processed_count: int, processing_time: float = 0.0) -> ProcessingResult:
    """Create a successful processing result."""
    return ProcessingResult(
        success=True,
        processed_count=processed_count,
        processing_time=processing_time
    )

def processing_failure(error: str, failed_count: int = 1) -> ProcessingResult:
    """Create a failed processing result."""
    return ProcessingResult(
        success=False,
        failed_count=failed_count,
        errors=[error]
    )

def valid_result() -> ValidationResult:
    """Create a valid result."""
    return ValidationResult(is_valid=True)

def invalid_result(error: str) -> ValidationResult:
    """Create an invalid result."""
    result = ValidationResult(is_valid=False)
    result.add_error(error)
    return result