# Configuration Guide

Complete configuration reference for the Physics Literature Synthesis Pipeline.

## 📋 Configuration Overview

The pipeline uses a centralized configuration system through the `PipelineConfig` class, with support for environment variables and programmatic overrides.

## 🔧 Environment Variables

### Required Variables

```bash
# Core API Keys (Required)
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ZOTERO_API_KEY=your-zotero-api-key-here
ZOTERO_LIBRARY_ID=your-zotero-user-id-here
```

### Zotero Configuration

```bash
# Zotero Settings
ZOTERO_LIBRARY_TYPE=user                    # "user" or "group"
ZOTERO_DOWNLOAD_ATTACHMENTS=true           # Download PDF attachments
ZOTERO_FILE_TYPES=application/pdf,text/plain  # File types to download
ZOTERO_OVERWRITE_FILES=false               # Overwrite existing files
# ZOTERO_SYNC_COLLECTIONS=collection1,collection2  # Optional: specific collections
```

### Optional API Keys

```bash
# Google Custom Search (Optional - for enhanced paper search)
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id-here
```

### Processing Configuration

```bash
# Document Processing
CHUNK_SIZE=1000                    # Words per text chunk for embeddings
CHUNK_OVERLAP=200                  # Overlapping words between chunks
EMBEDDING_MODEL=all-MiniLM-L6-v2   # Sentence transformer model

# Download Settings
DOWNLOAD_DELAY=1.2                 # Seconds between downloads
MAX_RETRIES=3                      # Download retry attempts
TIMEOUT_SECONDS=30                 # Download timeout

# Search Thresholds
TITLE_SIMILARITY_THRESHOLD=0.6     # Title matching threshold
ABSTRACT_SIMILARITY_THRESHOLD=0.5  # Abstract matching threshold
HIGH_CONFIDENCE_THRESHOLD=0.9      # High confidence match threshold
```

### AI Assistant Configuration

```bash
# Claude AI Settings
CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Claude model version
DEFAULT_TEMPERATURE=0.3            # AI creativity level (0.0-1.0)
MAX_TOKENS=4000                    # Maximum tokens per response
MAX_CONTEXT_CHUNKS=8               # Max literature chunks for context
MAX_CONVERSATION_HISTORY=20        # Max conversation messages to keep
```

## ⚙️ Configuration Classes

### PipelineConfig

The main configuration class that handles all settings:

```python
from config import PipelineConfig

# Default configuration
config = PipelineConfig()

# Configuration with overrides
config = PipelineConfig({
    'embedding_model': 'all-mpnet-base-v2',
    'chunk_size': 1500,
    'max_doi_downloads_per_sync': 25
})

# Access configuration values
print(config.anthropic_api_key)
print(config.zotero_sync_folder)
print(config.embedding_model)
```

### Configuration Validation

```python
# Validate required API keys
config.validate_api_keys()  # Raises ValueError if missing

# Validate Zotero configuration
config.validate_zotero_config()  # Raises ValueError if invalid

# Check all configuration status
status = config.check_env_file()
print(status)
# {
#     'anthropic_api_key': True,
#     'zotero_configured': True,
#     'google_search_enabled': False
# }
```

## 🎯 Component-Specific Configuration

### ArXiv Searcher Configuration

```python
arxiv_config = config.get_arxiv_config()
# {
#     'delay': 1.2,
#     'max_retries': 3,
#     'timeout': 30,
#     'title_threshold': 0.6,
#     'abstract_threshold': 0.5,
#     'high_confidence_threshold': 0.9,
#     'google_api_key': 'your-key',
#     'google_search_engine_id': 'your-id'
# }
```

### Zotero Configuration

```python
zotero_config = config.get_zotero_config()
# {
#     'api_key': 'your-key',
#     'library_id': 'your-id',
#     'library_type': 'user',
#     'download_attachments': True,
#     'file_types': {'application/pdf', 'text/plain'},
#     'overwrite_files': False,
#     'sync_collections': None,
#     'output_directory': Path('documents/zotero_sync')
# }
```

### Embeddings Configuration

```python
embedding_config = config.get_embedding_config()
# {
#     'model_name': 'all-MiniLM-L6-v2',
#     'chunk_size': 1000,
#     'chunk_overlap': 200
# }
```

### Chat Assistant Configuration

```python
chat_config = config.get_chat_config()
# {
#     'model': 'claude-3-5-sonnet-20241022',
#     'max_tokens': 4000,
#     'default_temperature': 0.3,
#     'max_context_chunks': 8,
#     'max_history': 20
# }
```

## 🔧 Advanced Configuration

### Enhanced Zotero Manager Configuration

```python
from src.downloaders import EnhancedZoteroLiteratureSyncer

# Basic configuration
syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=config.get_zotero_config(),
    doi_downloads_enabled=True,
    pdf_integration_enabled=True,
    default_integration_mode="attach"
)

# Advanced configuration
enhanced_config = {
    'api_key': 'your_key',
    'library_id': 'your_id', 
    'library_type': 'user',
    'download_attachments': True,
    'file_types': {'application/pdf', 'text/plain'},
    'overwrite_files': False,
    'output_directory': Path('custom/zotero/path'),
    # Enhanced options
    'doi_downloads_enabled': True,
    'pdf_integration_mode': 'attach',
    'max_doi_downloads_per_sync': 20,
    'browser_headless': True,
    'download_timeout': 45
}

syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=enhanced_config,
    pdf_integration_enabled=True
)
```

### DOI Downloads Configuration

```python
# Configure DOI download settings
syncer.configure_doi_downloads(
    enabled=True,
    max_per_sync=25,        # Adjust based on collection size
    headless=True,          # Faster for batch processing  
    timeout=60              # Longer timeout for slower networks
)
```

### PDF Integration Configuration

```python
# Configure PDF integration
syncer.configure_pdf_integration(
    enabled=True,
    default_mode="attach"   # Most reliable mode
)

# Available modes
from src.downloaders import get_available_modes
print(get_available_modes())
# ['download_only', 'attach']
```

## 📁 Directory Configuration

### Default Directory Structure

```python
config = PipelineConfig()

# Document folders
print(config.literature_folder)        # documents/literature
print(config.your_work_folder)         # documents/your_work
print(config.current_drafts_folder)    # documents/current_drafts
print(config.manual_references_folder) # documents/manual_references

# Zotero folders
print(config.zotero_sync_folder)       # documents/zotero_sync
print(config.zotero_pdfs_folder)       # documents/zotero_sync/pdfs
print(config.zotero_other_files_folder) # documents/zotero_sync/other_files

# Cache and output
print(config.cache_file)               # physics_knowledge_base.pkl
print(config.reports_folder)           # reports
```

### Custom Directory Configuration

```python
from pathlib import Path

# Custom configuration
custom_config = PipelineConfig({
    'documents_root': Path('/custom/research/papers'),
    'cache_file': Path('/custom/cache/physics_kb.pkl'),
    'reports_folder': Path('/custom/reports')
})
```

## 🎛️ Performance Configuration

### Large Library Configuration

```python
# For large Zotero libraries (1000+ items)
config = PipelineConfig({
    'chunk_size': 1500,                    # Larger chunks for efficiency
    'max_context_chunks': 10,              # More context for AI
    'max_doi_downloads_per_sync': 10,      # Conservative download limit
    'timeout_seconds': 60                  # Longer timeout
})
```

### High-Performance Configuration

```python
# For powerful machines with good internet
config = PipelineConfig({
    'chunk_size': 800,                     # Smaller chunks for precision
    'max_context_chunks': 15,              # Maximum context
    'max_doi_downloads_per_sync': 30,      # Aggressive downloading
    'download_delay': 0.8,                 # Faster downloads
    'embedding_model': 'all-mpnet-base-v2' # Higher quality embeddings
})
```

### Development Configuration

```python
# For development and testing
config = PipelineConfig({
    'max_doi_downloads_per_sync': 3,       # Limit for testing
    'default_temperature': 0.5,            # More creative AI responses
    'max_conversation_history': 50,        # Longer conversation memory
    'timeout_seconds': 10                  # Fail fast for debugging
})
```

## 🔍 Model Configuration

### Embedding Models

Available sentence transformer models:

```python
# Fast and efficient (default)
'all-MiniLM-L6-v2'          # 384 dimensions, ~80MB

# Balanced performance
'all-MiniLM-L12-v2'         # 384 dimensions, ~120MB
'paraphrase-MiniLM-L6-v2'   # 384 dimensions, ~80MB

# High quality (slower)
'all-mpnet-base-v2'         # 768 dimensions, ~420MB
'paraphrase-mpnet-base-v2'  # 768 dimensions, ~420MB

# Specialized for science
'allenai-specter'           # Scientific papers
'sentence-transformers/multi-qa-mpnet-base-dot-v1'  # Question answering
```

### Claude Models

Available Anthropic Claude models:

```python
# Current models
'claude-3-5-sonnet-20241022'  # Latest Sonnet (recommended)
'claude-3-opus-20240229'      # Most capable
'claude-3-sonnet-20240229'    # Balanced
'claude-3-haiku-20240307'     # Fastest
```

## 📊 Configuration Examples

### Research Group Configuration

```python
# .env file for research group
ANTHROPIC_API_KEY=group-anthropic-key
ZOTERO_API_KEY=group-zotero-key
ZOTERO_LIBRARY_ID=group-library-id
ZOTERO_LIBRARY_TYPE=group

# Shared settings
CHUNK_SIZE=1200
EMBEDDING_MODEL=all-mpnet-base-v2
MAX_DOI_DOWNLOADS_PER_SYNC=15
DEFAULT_TEMPERATURE=0.3
```

### Individual Researcher Configuration

```python
# .env file for individual researcher
ANTHROPIC_API_KEY=personal-anthropic-key
ZOTERO_API_KEY=personal-zotero-key
ZOTERO_LIBRARY_ID=personal-user-id
ZOTERO_LIBRARY_TYPE=user

# Personal preferences
CHUNK_SIZE=1000
EMBEDDING_MODEL=all-MiniLM-L6-v2
MAX_DOI_DOWNLOADS_PER_SYNC=20
DEFAULT_TEMPERATURE=0.2
MAX_CONTEXT_CHUNKS=12
```

### Production Server Configuration

```python
# .env file for production deployment
ANTHROPIC_API_KEY=production-key
ZOTERO_API_KEY=production-zotero-key
ZOTERO_LIBRARY_ID=production-library-id

# Production settings
DOWNLOAD_DELAY=2.0                     # Respectful to servers
MAX_RETRIES=5                          # More resilient
TIMEOUT_SECONDS=45                     # Longer timeout
MAX_DOI_DOWNLOADS_PER_SYNC=10          # Conservative
BROWSER_HEADLESS=true                  # No GUI on server
```

## 🛠️ Configuration Utilities

### Configuration Validation Script

```python
#!/usr/bin/env python3
"""Validate pipeline configuration."""

from config import PipelineConfig

def validate_configuration():
    """Validate all configuration settings."""
    
    config = PipelineConfig()
    
    print("🔍 CONFIGURATION VALIDATION")
    print("=" * 40)
    
    # Check API keys
    try:
        config.validate_api_keys()
        print("✅ Anthropic API key: Valid")
    except ValueError as e:
        print(f"❌ Anthropic API key: {e}")
    
    try:
        config.validate_zotero_config()
        print("✅ Zotero configuration: Valid")
    except ValueError as e:
        print(f"❌ Zotero configuration: {e}")
    
    # Check optional features
    status = config.check_env_file()
    print(f"\n📊 Feature Status:")
    print(f"   Google Search: {'✅' if status['google_search_enabled'] else '❌'}")
    print(f"   Zotero Integration: {'✅' if status['zotero_configured'] else '❌'}")
    
    # Check directories
    print(f"\n📁 Directory Status:")
    config._create_directories()  # Ensure directories exist
    print(f"   Documents root: {config.documents_root}")
    print(f"   Zotero sync: {config.zotero_sync_folder}")
    print(f"   Cache file: {config.cache_file}")
    
    print(f"\n🎯 Ready for use: {'✅' if all(status.values()) else '⚠️  (some features disabled)'}")

if __name__ == "__main__":
    validate_configuration()
```

### Environment Setup Script

```python
#!/usr/bin/env python3
"""Interactive environment setup."""

import os
from pathlib import Path

def setup_environment():
    """Interactive setup of environment variables."""
    
    print("🚀 PHYSICS PIPELINE ENVIRONMENT SETUP")
    print("=" * 45)
    
    env_file = Path('.env')
    
    # Required keys
    anthropic_key = input("Enter your Anthropic API key: ").strip()
    zotero_key = input("Enter your Zotero API key: ").strip()
    zotero_id = input("Enter your Zotero Library ID: ").strip()
    
    # Optional keys
    google_key = input("Enter Google API key (optional, press Enter to skip): ").strip()
    google_engine = input("Enter Google Search Engine ID (optional): ").strip()
    
    # Write .env file
    with open(env_file, 'w') as f:
        f.write("# Physics Literature Synthesis Pipeline Configuration\n\n")
        f.write("# Required API Keys\n")
        f.write(f"ANTHROPIC_API_KEY={anthropic_key}\n")
        f.write(f"ZOTERO_API_KEY={zotero_key}\n")
        f.write(f"ZOTERO_LIBRARY_ID={zotero_id}\n")
        f.write("ZOTERO_LIBRARY_TYPE=user\n\n")
        
        if google_key:
            f.write("# Optional Google Search\n")
            f.write(f"GOOGLE_API_KEY={google_key}\n")
            f.write(f"GOOGLE_SEARCH_ENGINE_ID={google_engine}\n\n")
        
        f.write("# Default Settings\n")
        f.write("CHUNK_SIZE=1000\n")
        f.write("EMBEDDING_MODEL=all-MiniLM-L6-v2\n")
        f.write("DEFAULT_TEMPERATURE=0.3\n")
        f.write("MAX_DOI_DOWNLOADS_PER_SYNC=15\n")
    
    print(f"✅ Configuration saved to {env_file}")
    print("🎉 Setup complete! You can now use the pipeline.")

if __name__ == "__main__":
    setup_environment()
```

## 🔧 Troubleshooting Configuration

### Common Configuration Issues

#### Missing API Keys
```python
# Check for missing keys
config = PipelineConfig()
try:
    config.validate_api_keys()
    config.validate_zotero_config()
except ValueError as e:
    print(f"Configuration error: {e}")
    # Provide specific guidance for missing keys
```

#### Invalid Zotero Settings
```python
# Test Zotero connection
from src.downloaders import EnhancedZoteroLiteratureSyncer
try:
    syncer = EnhancedZoteroLiteratureSyncer(config.get_zotero_config())
    result = syncer.zotero_manager.test_connection()
    if not result['connected']:
        print(f"Zotero connection failed: {result['error']}")
except Exception as e:
    print(f"Zotero configuration error: {e}")
```

#### Model Loading Issues
```python
# Test embedding model
try:
    from src.core import EmbeddingsManager
    em = EmbeddingsManager(model_name=config.embedding_model)
    print("✅ Embedding model loaded successfully")
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    print("Try a different model or check internet connection")
```

For more troubleshooting help, see [troubleshooting.md](troubleshooting.md).