# src/utils/__init__.py
"""Utility modules for the Physics Literature Synthesis Pipeline."""

from .logging_config import setup_logging, get_logger
from .file_utils import (
    ensure_directory_exists, 
    clean_filename, 
    extract_arxiv_id_from_url,
    safe_file_read,
    count_words_in_text
)
from .file_operations import (
    get_file_info,
    validate_file_for_processing,
    safe_create_directory,
    count_files_by_extension,
    calculate_file_hash,
    handle_file_operation_safely
)

# Add these imports
from .exceptions import (
    ScientificAssistantError,
    DocumentProcessingError,
    KnowledgeBaseError,
    ZoteroIntegrationError,
    ConfigurationError,
    APIError
)
from .result_types import (
    OperationResult,
    ProcessingResult,
    ValidationResult,
    success_result,
    error_result,
    processing_success,
    processing_failure,
    valid_result,
    invalid_result
)

__all__ = [
    'setup_logging', 
    'get_logger',
    'ensure_directory_exists',
    'clean_filename',
    'extract_arxiv_id_from_url', 
    'safe_file_read',
    'count_words_in_text',
    # New file operations
    'get_file_info',
    'validate_file_for_processing',
    'safe_create_directory',
    'count_files_by_extension',
    'calculate_file_hash',
    'handle_file_operation_safely',
    # Exception classes
    'ScientificAssistantError',
    'DocumentProcessingError',
    'KnowledgeBaseError',
    'ZoteroIntegrationError',
    'ConfigurationError',
    'APIError',
    # Result types
    'OperationResult',
    'ProcessingResult',
    'ValidationResult',
    'success_result',
    'error_result',
    'processing_success',
    'processing_failure',
    'valid_result',
    'invalid_result',
]