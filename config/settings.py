#!/usr/bin/env python3
"""
Configuration settings for the Physics Literature Synthesis Pipeline.

This module centralizes all configuration parameters, making it easy to
modify behavior without changing code throughout the application.
"""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

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
        
        # NEW: Manual references folder
        self.manual_references_folder = self.documents_root / "manual_references"
        
        # Cache and output
        self.cache_file = self.project_root / "physics_knowledge_base.pkl"
        self.reports_folder = self.project_root / "reports"
        
        # API Configuration - Now loaded from .env file
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # Download settings - with .env overrides
        self.download_delay = float(os.getenv("DOWNLOAD_DELAY", "1.2"))
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        self.timeout_seconds = int(os.getenv("TIMEOUT_SECONDS", "30"))
        
        # Processing settings - with .env overrides
        self.chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
        self.chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
        self.embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Search settings
        self.title_similarity_threshold = float(os.getenv("TITLE_SIMILARITY_THRESHOLD", "0.6"))
        self.abstract_similarity_threshold = float(os.getenv("ABSTRACT_SIMILARITY_THRESHOLD", "0.5"))
        self.high_confidence_threshold = float(os.getenv("HIGH_CONFIDENCE_THRESHOLD", "0.9"))
        
        # Chat settings - with .env overrides
        self.default_temperature = float(os.getenv("DEFAULT_TEMPERATURE", "0.3"))
        self.max_context_chunks = int(os.getenv("MAX_CONTEXT_CHUNKS", "8"))
        self.max_conversation_history = int(os.getenv("MAX_CONVERSATION_HISTORY", "20"))
        self.claude_model = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
        self.max_tokens = int(os.getenv("MAX_TOKENS", "4000"))
        
        # File extensions to process
        self.supported_extensions = {'.pdf', '.tex', '.txt'}
        
        # Apply any overrides from config_dict
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
            self.manual_references_folder,  # NEW: Create manual references folder
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
                "ANTHROPIC_API_KEY not found. Please set it in your .env file "
                "or pass in config_dict."
            )
        return True
    
    def check_env_file(self) -> Dict[str, bool]:
        """
        Check which API keys are configured.
        
        Returns:
            Dictionary showing which keys are set
        """
        return {
            'anthropic_api_key': bool(self.anthropic_api_key),
            'google_api_key': bool(self.google_api_key),
            'google_search_engine_id': bool(self.google_search_engine_id),
            'google_search_enabled': bool(self.google_api_key and self.google_search_engine_id)
        }
    
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
    
    def get_document_folders(self) -> Dict[str, Path]:
        """Get all document folders with their source types."""
        return {
            'literature': self.literature_folder,
            'your_work': self.your_work_folder,
            'current_drafts': self.current_drafts_folder,
            'manual_references': self.manual_references_folder  # NEW
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        api_status = self.check_env_file()
        return f"""Physics Pipeline Configuration:
  Project Root: {self.project_root}
  
  Document Folders:
    Literature: {self.literature_folder}
    Your Work: {self.your_work_folder}
    Current Drafts: {self.current_drafts_folder}
    Manual References: {self.manual_references_folder}
  
  Cache File: {self.cache_file}
  Embedding Model: {self.embedding_model}
  Claude Model: {self.claude_model}
  
  API Keys Status:
    ✓ Anthropic: {'Configured' if api_status['anthropic_api_key'] else 'Missing'}
    {'✓' if api_status['google_api_key'] else '✗'} Google API: {'Configured' if api_status['google_api_key'] else 'Missing'}
    {'✓' if api_status['google_search_engine_id'] else '✗'} Google Search Engine: {'Configured' if api_status['google_search_engine_id'] else 'Missing'}
    {'✓' if api_status['google_search_enabled'] else '✗'} Google Search: {'Enabled' if api_status['google_search_enabled'] else 'Disabled'}
"""

# Default configuration instance
default_config = PipelineConfig()