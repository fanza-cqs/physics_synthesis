#!/usr/bin/env python3
"""
Common exception classes for the Scientific Assistant.

Provides standardized error handling across the application.
This is additive - existing error handling continues to work.
"""

class ScientificAssistantError(Exception):
    """Base exception for Scientific Assistant errors."""
    pass

class DocumentProcessingError(ScientificAssistantError):
    """Error during document processing operations."""
    
    def __init__(self, message: str, file_path: str = None, original_error: Exception = None):
        super().__init__(message)
        self.file_path = file_path
        self.original_error = original_error

class KnowledgeBaseError(ScientificAssistantError):
    """Error during knowledge base operations."""
    
    def __init__(self, message: str, kb_name: str = None, operation: str = None):
        super().__init__(message)
        self.kb_name = kb_name
        self.operation = operation

class ZoteroIntegrationError(ScientificAssistantError):
    """Error during Zotero integration operations."""
    
    def __init__(self, message: str, item_key: str = None, operation: str = None):
        super().__init__(message)
        self.item_key = item_key
        self.operation = operation

class ConfigurationError(ScientificAssistantError):
    """Error in configuration or setup."""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message)
        self.config_key = config_key

class APIError(ScientificAssistantError):
    """Error during external API calls."""
    
    def __init__(self, message: str, api_name: str = None, status_code: int = None):
        super().__init__(message)
        self.api_name = api_name
        self.status_code = status_code