# Technical Architecture

Detailed technical architecture and design decisions for the Physics Literature Synthesis Pipeline.

## 🏗️ System Overview

The Physics Literature Synthesis Pipeline is designed as a modular system with clear separation of concerns and extensible components.

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Jupyter Notebooks  │  CLI Scripts  │  Python API           │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
├─────────────────────────────────────────────────────────────┤
│  Literature Assistant  │  Enhanced Syncer  │  Knowledge Base │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                     Core Services                           │
├─────────────────────────────────────────────────────────────┤
│  Document Processor  │  Embeddings Manager  │  Chat Interface│
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                   Integration Layer                         │
├─────────────────────────────────────────────────────────────┤
│  Zotero Manager  │  PDF Integrator  │  DOI Downloader       │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    External APIs                            │
├─────────────────────────────────────────────────────────────┤
│  Zotero Web API  │  Anthropic API  │  Publisher Websites    │
└─────────────────────────────────────────────────────────────┘
```

## 📂 Directory Structure

```
physics_synthesis_pipeline/
├── src/                           # Source code
│   ├── core/                     # Core document processing & embeddings
│   │   ├── document_processor.py  # PDF/LaTeX text extraction
│   │   ├── embeddings.py          # Vector embeddings & search
│   │   └── knowledge_base.py      # High-level KB interface
│   ├── downloaders/               # Literature acquisition
│   │   ├── enhanced_zotero_manager.py       # DOI downloads + inheritance
│   │   ├── zotero_manager.py               # Core Zotero API operations
│   │   ├── enhanced_literature_syncer.py   # High-level sync orchestration
│   │   ├── zotero_pdf_integrator_fixed.py  # PDF integration system
│   │   ├── zotero_pdf_integrator_parts/    # Modular integration components
│   │   ├── bibtex_parser.py                # Legacy BibTeX support
│   │   ├── arxiv_searcher.py               # ArXiv API integration
│   │   └── literature_downloader.py        # Legacy download workflows
│   ├── chat/                      # AI conversation interface
│   │   ├── chat_interface.py      # Basic chat functionality
│   │   └── literature_assistant.py # Literature-aware AI assistant
│   └── utils/                     # Shared utilities
│       ├── logging_config.py      # Centralized logging
│       └── file_utils.py          # File operations
├── config/                        # Configuration management
│   ├── __init__.py
│   └── settings.py               # PipelineConfig class
├── documents/                     # Document storage
│   ├── zotero_sync/              # Enhanced Zotero content
│   │   ├── pdfs/                 # PDF attachments from Zotero
│   │   ├── other_files/          # Other document types
│   │   └── doi_downloads/        # Automatically downloaded PDFs
│   ├── literature/               # Legacy arXiv downloads
│   ├── your_work/                # User's publications
│   ├── current_drafts/           # Work in progress
│   └── manual_references/        # Manually added papers
├── notebooks/                     # Jupyter demonstration notebooks
├── reports/                       # Generated analysis reports
├── tests/                         # Unit and integration tests
└── readme/                        # Detailed documentation
```

## 🔧 Core Components

### 1. Configuration System (`config/`)

**Design Pattern**: Centralized configuration with environment variable support

```python
# Single source of truth for all configuration
class PipelineConfig:
    def __init__(self, config_dict=None):
        # Load from environment variables
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.zotero_api_key = os.getenv("ZOTERO_API_KEY")
        # Apply overrides if provided
        if config_dict:
            self._apply_overrides(config_dict)
```

**Benefits**:
- Single configuration entry point
- Environment variable support
- Type validation and error messages
- Component-specific configuration getters

### 2. Document Processing (`src/core/`)

**Architecture**: Layered processing pipeline

```
Raw Documents → Document Processor → Text Chunks → Embeddings → Knowledge Base
```

#### Document Processor
- **Purpose**: Extract text from PDFs, LaTeX, and plain text files
- **Design**: Plugin architecture for different file types
- **Features**: LaTeX cleaning, scientific content preservation

#### Embeddings Manager  
- **Purpose**: Create and manage vector embeddings for semantic search
- **Design**: Abstraction over sentence transformers
- **Features**: Chunking, similarity search, caching

#### Knowledge Base
- **Purpose**: High-level interface combining documents and embeddings
- **Design**: Facade pattern over document processor and embeddings
- **Features**: Multi-source building, search, statistics

### 3. Literature Acquisition (`src/downloaders/`)

**Architecture**: Inheritance hierarchy with graceful degradation

```
ZoteroLibraryManager (Base)
    └── EnhancedZoteroLibraryManager (Inherits + Adds DOI downloads)
        └── Used by EnhancedZoteroLiteratureSyncer (Orchestration)
```

#### Design Rationale
- **Separation of Concerns**: Basic API operations vs. browser automation
- **Dependency Isolation**: Core functionality doesn't require Selenium
- **Graceful Degradation**: Enhanced features disable when dependencies unavailable
- **Maintainability**: Clear inheritance hierarchy, easier testing

#### ZoteroLibraryManager (Base)
```python
class ZoteroLibraryManager:
    """Core Zotero Web API functionality - lightweight dependencies"""
    def get_all_items(self): pass
    def get_item_attachments(self): pass
    def download_attachment(self): pass
    def sync_library(self): pass
```

#### EnhancedZoteroLibraryManager (Enhanced)
```python
class EnhancedZoteroLibraryManager(ZoteroLibraryManager):
    """Inherits ALL basic functionality + adds DOI downloads"""
    def setup_selenium_driver(self): pass
    def download_pdf_from_doi(self): pass
    def sync_collection_with_doi_downloads(self): pass
```

### 4. PDF Integration System (`src/downloaders/zotero_pdf_integrator_*`)

**Architecture**: Modular system with mode-based processing

```
Main Function → Configuration → Mode Selection → Execution → Results
```

#### Integration Modes
1. **Download Only**: Keep PDFs locally without Zotero integration
2. **Attach Mode**: Attach PDFs to existing Zotero records (recommended)
3. **Upload Replace**: Create new records (disabled due to API limitations)

#### Modular Design
- **Part 1**: Core classes and enums
- **Part 2**: Main integrator class structure  
- **Part 3**: Mode implementation functions
- **Part 4**: Attachment method implementations
- **Part 5**: Upload and replace methods
- **Part 6**: Main integration function and utilities

### 5. AI Assistant (`src/chat/`)

**Architecture**: Layered conversation management

```
User Query → Literature Search → Context Building → AI Response → Source Citations
```

#### Chat Interface
- **Purpose**: Basic conversational AI functionality
- **Features**: Message history, system prompts, conversation management

#### Literature Assistant
- **Purpose**: Literature-aware AI with source citations
- **Features**: Semantic search integration, source tracking, synthesis generation

## 🚀 Data Flow Architecture

### Literature Acquisition Flow

```
1. User requests collection sync
2. Enhanced Syncer gets collection items from Zotero API
3. Identifies items with DOIs but no PDFs
4. Downloads PDFs via browser automation
5. Integrates PDFs back into Zotero records
6. Updates local knowledge base
7. Returns comprehensive results
```

### AI Research Flow

```
1. User asks research question
2. Literature Assistant searches knowledge base semantically
3. Retrieves relevant document chunks
4. Formats context for AI model
5. Sends enhanced prompt to Claude
6. Processes response with source citations
7. Returns answer with source tracking
```

### Knowledge Base Building Flow

```
1. Scan document directories
2. Process each file (PDF/LaTeX/text extraction)
3. Split text into semantic chunks
4. Generate embeddings for each chunk
5. Store embeddings with metadata
6. Build search indices
7. Cache results for fast loading
```

## 🔍 Design Patterns Used

### 1. Factory Pattern
```python
def create_zotero_manager(config, prefer_enhanced=True):
    """Automatically select appropriate manager based on dependencies"""
    if prefer_enhanced and ENHANCED_ZOTERO_AVAILABLE:
        return EnhancedZoteroLibraryManager(...)
    elif ZOTERO_AVAILABLE:
        return ZoteroLibraryManager(...)
    else:
        raise ImportError("Zotero integration unavailable")
```

### 2. Strategy Pattern
```python
class DOIDownloader:
    def download_pdf(self, doi, url):
        if 'journals.aps.org' in url:
            return self._aps_strategy(doi, url)
        elif 'mdpi.com' in url:
            return self._mdpi_strategy(doi, url)
        else:
            return self._generic_strategy(doi, url)
```

### 3. Facade Pattern
```python
class KnowledgeBase:
    """Simplified interface over complex document processing"""
    def __init__(self):
        self.document_processor = DocumentProcessor()
        self.embeddings_manager = EmbeddingsManager()
    
    def build_from_directories(self, folders):
        # Orchestrates complex multi-step process
        pass
```

### 4. Observer Pattern
```python
class LiteratureAssistant:
    def ask(self, question):
        # Maintains conversation history
        # Tracks source usage
        # Updates context automatically
        pass
```

## 🔧 Dependency Management

### Core Dependencies (Always Required)
```
anthropic>=0.7.0          # Claude AI integration
pyzotero>=1.5.0           # Zotero Web API
sentence-transformers     # Text embeddings
scikit-learn             # ML utilities
PyPDF2, pymupdf          # PDF processing
```

### Enhanced Dependencies (Optional)
```
selenium>=4.0.0          # Browser automation for DOI downloads
googlesearch-python      # Google search fallback
```

### Graceful Degradation Logic
```python
try:
    from selenium import webdriver
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class EnhancedManager:
    def __init__(self, doi_downloads_enabled=True):
        self.doi_downloads_enabled = doi_downloads_enabled and SELENIUM_AVAILABLE
        if not SELENIUM_AVAILABLE and doi_downloads_enabled:
            logger.warning("DOI downloads disabled: Selenium not available")
```

## 📊 Performance Considerations

### 1. Caching Strategy
- **Knowledge Base**: Pickle serialization for embeddings and chunks
- **API Responses**: Optional caching for Zotero API calls
- **Downloaded Files**: Avoid re-downloading existing PDFs

### 2. Batch Processing
- **Collection Sync**: Process multiple collections efficiently
- **Embedding Generation**: Batch embed multiple documents
- **API Calls**: Use pagination and batch requests

### 3. Memory Management
- **Large Libraries**: Stream processing for large Zotero libraries
- **Embedding Storage**: Efficient numpy array storage
- **PDF Processing**: Process files individually to avoid memory issues

### 4. Network Optimization
- **Rate Limiting**: Respectful delays between API calls and downloads
- **Retry Logic**: Automatic retries with exponential backoff
- **Connection Pooling**: Reuse HTTP connections where possible

## 🛡️ Error Handling Strategy

### 1. Hierarchical Exception Structure
```python
class PipelineError(Exception):
    """Base exception for pipeline operations"""

class ZoteroConnectionError(PipelineError):
    """Zotero API connection issues"""

class PDFDownloadError(PipelineError):
    """PDF download failures"""

class IntegrationError(PipelineError):
    """PDF integration failures"""
```

### 2. Graceful Degradation
- **Missing Dependencies**: Disable features, continue with available functionality
- **API Failures**: Retry with fallback strategies
- **File Processing Errors**: Skip problematic files, continue processing others

### 3. Comprehensive Logging
```python
# Different log levels for different audiences
logger.debug("Detailed technical information")
logger.info("Progress and status updates")  
logger.warning("Recoverable issues")
logger.error("Serious problems requiring attention")
```

### 4. User-Friendly Error Messages
```python
try:
    syncer = EnhancedZoteroLiteratureSyncer(config)
except ImportError:
    raise ImportError(
        "Enhanced Zotero features require additional dependencies. "
        "Install with: pip install selenium"
    )
```

## 🔒 Security Considerations

### 1. API Key Management
- **Environment Variables**: Never hardcode API keys
- **Validation**: Check key format and permissions
- **Error Handling**: Don't log API keys in error messages

### 2. File System Security
- **Path Validation**: Prevent directory traversal attacks
- **Permissions**: Use appropriate file permissions
- **Sandboxing**: Isolate PDF processing from system files

### 3. Network Security
- **HTTPS**: Use encrypted connections for all API calls
- **Certificate Validation**: Verify SSL certificates
- **Rate Limiting**: Respect API rate limits

## 🧪 Testing Architecture

### 1. Unit Tests
- **Core Components**: Test document processing, embeddings, search
- **Integration Modules**: Test individual Zotero operations
- **Utilities**: Test file operations, configuration loading

### 2. Integration Tests
- **API Integration**: Test real Zotero API calls (with test data)
- **End-to-End**: Test complete workflows
- **Performance**: Test with realistic data sizes

### 3. Mock Testing
- **External APIs**: Mock Zotero, Anthropic, Google APIs
- **File System**: Mock file operations for isolated testing
- **Browser Automation**: Mock Selenium for CI/CD

## 🔮 Extensibility Points

### 1. Publisher Support
```python
class PublisherStrategy:
    def download_pdf(self, doi, url): pass

# Easy to add new publishers
class CustomPublisherStrategy(PublisherStrategy):
    def download_pdf(self, doi, url):
        # Custom implementation
        pass
```

### 2. Document Processors
```python
class DocumentProcessor:
    def register_processor(self, extension, processor_func):
        self.processors[extension] = processor_func

# Add support for new file types
processor.register_processor('.docx', process_word_document)
```

### 3. Embedding Models
```python
# Easy to swap embedding models
config = PipelineConfig({
    'embedding_model': 'custom-scientific-model'
})
```

### 4. AI Models
```python
# Support for different AI providers
class LiteratureAssistant:
    def __init__(self, knowledge_base, ai_client):
        self.ai_client = ai_client  # Could be Anthropic, OpenAI, etc.
```

## 📈 Scalability Considerations

### 1. Horizontal Scaling
- **Distributed Processing**: Process collections in parallel
- **Load Balancing**: Distribute API calls across multiple workers
- **Cloud Deployment**: Deploy on cloud infrastructure

### 2. Vertical Scaling
- **Memory Optimization**: Efficient data structures for large libraries
- **CPU Optimization**: Vectorized operations for embeddings
- **Storage Optimization**: Compressed serialization for knowledge bases

### 3. Database Integration
- **Vector Databases**: Replace in-memory embeddings with vector DB
- **Metadata Storage**: Use database for document metadata
- **Search Optimization**: Leverage database indices for fast search

This architecture provides a solid foundation for the current system while maintaining flexibility for future enhancements and scaling requirements.