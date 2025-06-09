#!/usr/bin/env python3
"""
Enhanced Configuration settings for the Physics Literature Synthesis Pipeline.

This module centralizes all configuration parameters, including Zotero integration
and the new multiple knowledge base support.

Location: config/settings.py
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
load_dotenv(Path(__file__).parent.parent / ".env")

@dataclass
class KnowledgeBaseConfig:
    """Configuration for a specific knowledge base."""
    name: str
    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    description: str = ""

class PipelineConfig:
    """Enhanced central configuration for the physics literature synthesis pipeline."""
    
    def __init__(self, config_dict: Dict[str, Any] = None):
        """
        Initialize configuration with optional overrides.
        
        Args:
            config_dict: Optional dictionary to override default settings
        """
        # Base project paths
        self.project_root = Path(__file__).parent.parent  # Go up from config/ to project root
        self.documents_root = self.project_root / "documents"
        
        # Document folders
        self.biblio_folder = self.documents_root / "biblio"  # Keep for backward compatibility
        self.literature_folder = self.documents_root / "literature"
        self.your_work_folder = self.documents_root / "your_work"
        self.current_drafts_folder = self.documents_root / "current_drafts"
        self.manual_references_folder = self.documents_root / "manual_references"
        
        # Zotero integration folders
        self.zotero_sync_folder = self.documents_root / "zotero_sync"
        self.zotero_pdfs_folder = self.zotero_sync_folder / "pdfs"
        self.zotero_other_files_folder = self.zotero_sync_folder / "other_files"
        
        # NEW: Knowledge base storage
        self.knowledge_bases_folder = self._get_path("KNOWLEDGE_BASES_FOLDER", "knowledge_bases")
        self.default_kb_name = os.getenv("DEFAULT_KB_NAME", "physics_main")
        
        # Cache and output
        self.cache_file = self.project_root / "physics_knowledge_base.pkl"  # Legacy
        self.reports_folder = self.project_root / "reports"
        
        # API Configuration - Now loaded from .env file
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        # Zotero API Configuration
        self.zotero_api_key = os.getenv("ZOTERO_API_KEY")
        self.zotero_library_id = os.getenv("ZOTERO_LIBRARY_ID")
        self.zotero_library_type = os.getenv("ZOTERO_LIBRARY_TYPE", "user")  # "user" or "group"
        
        # Zotero sync settings
        self.zotero_download_attachments = bool(os.getenv("ZOTERO_DOWNLOAD_ATTACHMENTS", "true").lower() == "true")
        self.zotero_file_types = set(os.getenv("ZOTERO_FILE_TYPES", "application/pdf,text/plain").split(","))
        self.zotero_overwrite_files = bool(os.getenv("ZOTERO_OVERWRITE_FILES", "false").lower() == "true")
        self.zotero_sync_collections = os.getenv("ZOTERO_SYNC_COLLECTIONS", "").split(",") if os.getenv("ZOTERO_SYNC_COLLECTIONS") else None
        
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
    
    def _get_path(self, env_var: str, default: str) -> Path:
        """Get path from environment variable or use default."""
        env_value = os.getenv(env_var)
        if env_value:
            path = Path(env_value)
            # Make relative paths relative to project root
            if not path.is_absolute():
                path = self.project_root / path
            return path
        else:
            return self.project_root / default
    
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
            self.manual_references_folder,
            # Zotero directories
            self.zotero_sync_folder,
            self.zotero_pdfs_folder,
            self.zotero_other_files_folder,
            # NEW: Knowledge base storage
            self.knowledge_bases_folder,
            self.reports_folder
        ]
        
        for directory in directories:
            try:
                directory.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass  # Don't fail if we can't create directories
    
    # === NEW KNOWLEDGE BASE METHODS ===
    
    def get_knowledge_base_config(self, name: str = None) -> KnowledgeBaseConfig:
        """
        Get configuration for a specific knowledge base.
        
        Args:
            name: Name of the knowledge base (uses default if None)
        
        Returns:
            KnowledgeBaseConfig object
        """
        kb_name = name or self.default_kb_name
        
        return KnowledgeBaseConfig(
            name=kb_name,
            embedding_model=self.embedding_model,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            description=f"Physics literature knowledge base: {kb_name}"
        )
    
    def get_knowledge_base_path(self, name: str = None) -> Path:
        """
        Get the storage path for a specific knowledge base.
        
        Args:
            name: Name of the knowledge base (uses default if None)
        
        Returns:
            Path to the knowledge base directory
        """
        kb_name = name or self.default_kb_name
        return self.knowledge_bases_folder / kb_name
    
    def list_available_knowledge_bases(self) -> List[str]:
        """
        List all available knowledge base names.
        
        Returns:
            List of knowledge base names
        """
        if not self.knowledge_bases_folder.exists():
            return []
        
        kb_names = []
        for item in self.knowledge_bases_folder.iterdir():
            if item.is_dir():
                config_file = item / f"{item.name}_config.json"
                if config_file.exists():
                    kb_names.append(item.name)
        
        return sorted(kb_names)
    
    def get_legacy_cache_file(self) -> Path:
        """
        Get the legacy cache file path for backward compatibility.
        
        Returns:
            Path to legacy cache file
        """
        return self.cache_file
    
    def migrate_legacy_cache(self, target_kb_name: str = None) -> bool:
        """
        Migrate legacy cache file to new knowledge base system.
        
        Args:
            target_kb_name: Name for the migrated knowledge base
        
        Returns:
            True if migration was successful
        """
        if not self.cache_file.exists():
            return False
        
        kb_name = target_kb_name or self.default_kb_name
        
        try:
            # Import here to avoid circular imports
            from src.core import KnowledgeBase
            
            # Create new knowledge base
            new_kb = KnowledgeBase(
                name=kb_name,
                base_storage_dir=self.knowledge_bases_folder,
                embedding_model=self.embedding_model,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            
            # Load from legacy file
            success = new_kb.embeddings_manager.load_from_file(self.cache_file)
            
            if success:
                # Save in new format
                new_kb.save_to_storage()
                
                # Backup and remove legacy file
                backup_file = self.cache_file.with_suffix('.pkl.backup')
                self.cache_file.rename(backup_file)
                
                return True
            else:
                return False
                
        except Exception:
            return False
    
    # === EXISTING METHODS (ENHANCED) ===
    
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
    
    def validate_zotero_config(self) -> bool:
        """
        Validate Zotero configuration.
        
        Returns:
            bool: True if Zotero is properly configured
        """
        if not self.zotero_api_key:
            raise ValueError(
                "ZOTERO_API_KEY not found. Please set it in your .env file. "
                "Get your API key from: https://www.zotero.org/settings/keys"
            )
        
        if not self.zotero_library_id:
            raise ValueError(
                "ZOTERO_LIBRARY_ID not found. Please set it in your .env file. "
                "Find your library ID at: https://www.zotero.org/settings/keys"
            )
        
        if self.zotero_library_type not in ["user", "group"]:
            raise ValueError(
                "ZOTERO_LIBRARY_TYPE must be either 'user' or 'group'"
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
            'google_search_enabled': bool(self.google_api_key and self.google_search_engine_id),
            'zotero_api_key': bool(self.zotero_api_key),
            'zotero_library_id': bool(self.zotero_library_id),
            'zotero_configured': bool(self.zotero_api_key and self.zotero_library_id)
        }
    
    def validate_required_config(self) -> List[str]:
        """
        Validate required configuration and return list of missing items.
        
        Returns:
            List of missing configuration items
        """
        missing = []
        
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY (required for AI assistant)")
        
        # Check if directories are writable
        test_dirs = [
            self.documents_root,
            self.knowledge_bases_folder
        ]
        
        for test_dir in test_dirs:
            try:
                test_dir.mkdir(parents=True, exist_ok=True)
                test_file = test_dir / ".test_write"
                test_file.write_text("test")
                test_file.unlink()
            except Exception:
                missing.append(f"Write access to {test_dir}")
        
        return missing
    
    def create_sample_env_file(self) -> bool:
        """
        Create a sample .env file with all available settings.
        
        Returns:
            True if file was created successfully
        """
        env_file = self.project_root / ".env"
        
        if env_file.exists():
            return False
        
        sample_content = """# Physics Literature Synthesis Pipeline Configuration
# Copy this file and add your actual API keys

# REQUIRED: Anthropic API key for Claude AI
# Get from: https://console.anthropic.com/
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# OPTIONAL: Zotero integration for automatic PDF management
# Get from: https://www.zotero.org/settings/keys
ZOTERO_API_KEY=your-zotero-api-key-here
ZOTERO_LIBRARY_ID=your-zotero-library-id-here
ZOTERO_LIBRARY_TYPE=user

# OPTIONAL: Google Custom Search for enhanced arXiv search
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id-here

# DIRECTORIES: Customize document storage locations (relative to project root)
KNOWLEDGE_BASES_FOLDER=knowledge_bases

# KNOWLEDGE BASE SETTINGS
DEFAULT_KB_NAME=physics_main
EMBEDDING_MODEL=all-MiniLM-L6-v2
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# AI MODEL SETTINGS
CLAUDE_MODEL=claude-3-5-sonnet-20241022
DEFAULT_TEMPERATURE=0.3
MAX_CONTEXT_CHUNKS=8

# DOWNLOAD SETTINGS
DOWNLOAD_DELAY=1.2
MAX_RETRIES=3
TIMEOUT_SECONDS=30

# ZOTERO SYNC SETTINGS
ZOTERO_DOWNLOAD_ATTACHMENTS=true
ZOTERO_FILE_TYPES=application/pdf,text/plain
ZOTERO_OVERWRITE_FILES=false
"""
        
        try:
            env_file.write_text(sample_content)
            return True
        except Exception:
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration.
        
        Returns:
            Dictionary with configuration summary
        """
        status = self.check_env_file()
        missing = self.validate_required_config()
        
        return {
            'project_root': str(self.project_root),
            'knowledge_bases_folder': str(self.knowledge_bases_folder),
            'default_kb_name': self.default_kb_name,
            'available_knowledge_bases': self.list_available_knowledge_bases(),
            'api_status': status,
            'missing_config': missing,
            'document_folders': {k: str(v) for k, v in self.get_document_folders().items()},
            'models': {
                'embedding_model': self.embedding_model,
                'claude_model': self.claude_model,
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap
            }
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
    
    def get_zotero_config(self) -> Dict[str, Any]:
        """Get configuration specific to Zotero integration."""
        return {
            'api_key': self.zotero_api_key,
            'library_id': self.zotero_library_id,
            'library_type': self.zotero_library_type,
            'download_attachments': self.zotero_download_attachments,
            'file_types': self.zotero_file_types,
            'overwrite_files': self.zotero_overwrite_files,
            'sync_collections': self.zotero_sync_collections,
            'output_directory': self.zotero_sync_folder
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
            'manual_references': self.manual_references_folder,
            'zotero_sync': self.zotero_sync_folder  # Changed from separate pdf/other folders
        }
    
    def get_literature_sources(self) -> Dict[str, str]:
        """Get available literature source types and their descriptions."""
        return {
            'bibtex': 'Legacy BibTeX files (deprecated)',
            'arxiv': 'ArXiv downloads via API',
            'zotero': 'Zotero library synchronization (recommended)',
            'manual': 'Manually added references'
        }
    
    def __str__(self) -> str:
        """String representation of configuration."""
        api_status = self.check_env_file()
        available_kbs = self.list_available_knowledge_bases()
        
        return f"""Physics Pipeline Configuration:
  Project Root: {self.project_root}
  
  Document Folders:
    Literature: {self.literature_folder}
    Your Work: {self.your_work_folder}
    Current Drafts: {self.current_drafts_folder}
    Manual References: {self.manual_references_folder}
    Zotero Sync: {self.zotero_sync_folder}
  
  Knowledge Bases:
    Storage: {self.knowledge_bases_folder}
    Default: {self.default_kb_name}
    Available: {', '.join(available_kbs) if available_kbs else 'None'}
  
  Legacy Cache: {self.cache_file}
  Embedding Model: {self.embedding_model}
  Claude Model: {self.claude_model}
  
  API Keys Status:
    ✓ Anthropic: {'Configured' if api_status['anthropic_api_key'] else 'Missing'}
    {'✓' if api_status['google_api_key'] else '✗'} Google API: {'Configured' if api_status['google_api_key'] else 'Missing'}
    {'✓' if api_status['google_search_engine_id'] else '✗'} Google Search Engine: {'Configured' if api_status['google_search_engine_id'] else 'Missing'}
    {'✓' if api_status['google_search_enabled'] else '✗'} Google Search: {'Enabled' if api_status['google_search_enabled'] else 'Disabled'}
    {'✓' if api_status['zotero_api_key'] else '✗'} Zotero API: {'Configured' if api_status['zotero_api_key'] else 'Missing'}
    {'✓' if api_status['zotero_library_id'] else '✗'} Zotero Library: {'Configured' if api_status['zotero_library_id'] else 'Missing'}
    {'✓' if api_status['zotero_configured'] else '✗'} Zotero Integration: {'Enabled' if api_status['zotero_configured'] else 'Disabled'}
  
  Zotero Settings:
    Library Type: {self.zotero_library_type}
    Library ID: {self.zotero_library_id or 'Not set'}
    Download Attachments: {self.zotero_download_attachments}
    File Types: {', '.join(self.zotero_file_types) if self.zotero_file_types else 'None'}
"""

# For backward compatibility
PipelineConfig.__name__ = "PipelineConfig"

# Default configuration instance
default_config = PipelineConfig()