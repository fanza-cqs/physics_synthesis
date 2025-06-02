#!/usr/bin/env python3
"""
Configuration settings for the Physics Literature Synthesis Pipeline.

This module centralizes all configuration parameters, making it easy to
modify behavior without changing code throughout the application.
"""

import os
from pathlib import Path
from typing import Dict, Any

class PipelineConfig:
    """Central configuration for the physics literature synthesis pipeline."""
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """
        Initialize configuration with optional overrides.
        
        Args:
            config_dict: Optional dictionary to override default settings
        """
        # Base project paths
        self.project_root = Path.cwd()
        self.documents_root = self.project_root / "documents"
        
        # Document folders
        self.biblio_folder = self.documents_root / "biblio"
        self.literature_folder = self.documents_root / "literature"
        self.your_work_folder = self.documents_root / "your_work"
        self.current_drafts_folder = self.documents_root / "current_drafts"
        
        # Cache and output
        self.cache_file = self.project_root / "physics_knowledge_base.pkl"
        self.reports_folder = self.project_root / "reports"
        
        # API Configuration
        # API Configuration
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # Download settings
        self.download_delay = 1.2  # Seconds between arXiv requests
        self.max_retries = 3
        self.timeout_seconds = 30
        
        # Processing settings
        self.chunk_size = 1000  # Words per text chunk
        self.chunk_overlap = 200  # Word overlap between chunks
        self.embedding_model = "all-MiniLM-L6-v2"
        
        # Search settings
        self.title_similarity_threshold = 0.6
        self.abstract_similarity_threshold = 0.5
        self.high_confidence_threshold = 0.9
        
        # Chat settings
        self.default_temperature = 0.3
        self.max_context_chunks = 8
        self.max_conversation_history = 20
        self.claude_model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4000
        
        # File extensions to process
        self.supported_extensions = {'.pdf', '.tex', '.txt'}
        
        # Apply any overrides
        if config_dict:
            self._apply_overrides(config_dict)
        
        # Ensure directories exist
        self._create_directories()
    
    def _apply_overrides(self, config_dict: Dict[str, Any]):
        """Apply configuration overrides from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _create_directories(self):
        """Create necessary directories if they don't exist."""
        directories = [
            self.documents_root,
            self.biblio_folder,
            self.literature_folder,
            self.your_work_folder,
            self.current_drafts_folder,
            self.reports_folder
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def validate_api_keys(self) -> bool:
        """
        Validate that required API keys are available.
        
        Returns:
            bool: True if all required API keys are present
        """
        if not self.anthropic_api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. Please set as environment variable "
                "or pass in config_dict."
            )
        return True
    
    def get_arxiv_config(self) -> Dict[str, Any]:
        """Get configuration specific to arXiv downloading."""
        return {
            'delay': self.download_delay,
            'max_retries': self.max_retries,
            'timeout': self.timeout_seconds,
            'title_threshold': self.title_similarity_threshold,
            'abstract_threshold': self.abstract_similarity_threshold,
            'high_confidence_threshold': self.high_confidence_threshold,
            'google_api_key': self.google_api_key,
            'google_search_engine_id': self.google_search_engine_id
        }
    
    def get_embedding_config(self) -> Dict[str, Any]:
        """Get configuration specific to embeddings."""
        return {
            'model_name': self.embedding_model,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap
        }
    
    def get_chat_config(self) -> Dict[str, Any]:
        """Get configuration specific to chat interface."""
        return {
            'model': self.claude_model,
            'max_tokens': self.max_tokens,
            'default_temperature': self.default_temperature,
            'max_context_chunks': self.max_context_chunks,
            'max_history': self.max_conversation_history
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        return f"""Physics Pipeline Configuration:
  Project Root: {self.project_root}
  Literature Folder: {self.literature_folder}
  Cache File: {self.cache_file}
  Embedding Model: {self.embedding_model}
  Claude Model: {self.claude_model}
  API Keys: {'✓' if self.anthropic_api_key else '✗'} Anthropic
"""

# Default configuration instance
default_config = PipelineConfig()