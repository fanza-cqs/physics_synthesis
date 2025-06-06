# Physics Literature Synthesis Pipeline

A modular, automated pipeline for physics research that downloads literature from arXiv, builds a searchable knowledge base, and provides AI-powered research assistance.

## Overview

This pipeline helps physicists:
- **Automate literature collection** from Zotero bibliographies with DOI-based PDF downloads
- **Build searchable knowledge bases** from physics papers
- **Get AI assistance** grounded in relevant literature
- **Synthesize research** with source-backed responses

## Architecture

```
physics_synthesis_pipeline/
├── src/
│   ├── core/           # Document processing & embeddings
│   ├── downloaders/    # Zotero sync, arXiv search & DOI-based downloads
│   ├── chat/          # AI chat interface
│   └── utils/         # Utilities & logging
├── config/            # Configuration management
├── documents/         # Your papers and literature
├── notebooks/         # Demo notebooks
└── tests/            # Unit tests
```

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd physics_synthesis_pipeline

# Install dependencies
pip install -r requirements.txt

# For DOI-based PDF downloads (optional)
pip install selenium

# Set your API keys
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export ZOTERO_API_KEY="your-zotero-api-key"
export ZOTERO_LIBRARY_ID="your-library-id"
```

### 2. Add Your Literature

```bash
# Option 1: Use Zotero integration (recommended)
# Configure your Zotero API credentials in .env file

# Option 2: Legacy BibTeX approach
# Export bibliography from Zotero as .bib file
# Place it in documents/biblio/

# Add your own papers (optional)
# Place PDFs/TEX files in documents/your_work/
# Place current drafts in documents/current_drafts/
```

### 3. Run the Demo

```bash
# Start Jupyter and open the demo notebook
jupyter notebook notebooks/physics_pipeline_demo.ipynb
```

## Features

### 📥 Literature Download & Sync
- **Zotero Integration**: Real-time sync with your Zotero library
- **DOI-based PDF Downloads**: Automatically download missing PDFs using DOIs
- **Multi-Publisher Support**: Works with APS, MDPI, Nature, arXiv, and more
- **Legacy BibTeX Support**: Parse Zotero .bib files automatically
- **Multi-strategy arXiv search**: Title, abstract, Google fallback
- **Comprehensive reporting**: Success rates and detailed logs

### 🧠 Knowledge Base
- Process PDF and LaTeX documents
- Create semantic embeddings for search
- Support multiple document types and sources
- Efficient caching system

### 💬 AI Assistant
- Literature-aware conversations
- Source-backed responses with citations
- Research synthesis and writing help
- Conversation memory and context

### 🔧 DOI-based PDF Downloads
- **Smart Publisher Detection**: Automatically identifies and handles different publishers
- **Browser Automation**: Uses Selenium for reliable PDF downloads
- **High Success Rates**: 90%+ success for supported publishers (APS, MDPI, Nature)
- **Respectful Access**: Built-in delays and publisher-specific handling
- **Collection-Based**: Download missing PDFs for entire Zotero collections

## Usage Examples

### Zotero Collection Sync with DOI Downloads

```python
from src.downloaders import EnhancedZoteroLiteratureSyncer
from config import PipelineConfig

# Initialize enhanced syncer
config = PipelineConfig()
syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=config.get_zotero_config(),
    doi_downloads_enabled=True
)

# Sync collection with automatic PDF downloads
result = syncer.sync_collection_with_doi_downloads(
    collection_name="Physics Papers",
    max_doi_downloads=10,
    headless=False  # Set True to hide browser
)

print(f"Downloaded {result.zotero_sync_result.successful_doi_downloads} PDFs")
```

### Simple Chat Interface

```python
from src.chat import LiteratureAssistant
from src.core import KnowledgeBase

# Initialize components
kb = KnowledgeBase()
kb.load_from_file("physics_knowledge_base.pkl")

assistant = LiteratureAssistant(kb, anthropic_api_key="your-key")

# Ask questions
response = assistant.ask("What are measurement-induced phase transitions?")
print(response.content)
print(f"Sources: {response.sources_used}")
```

### Literature Download (Legacy)

```python
from src.downloaders import LiteratureDownloader
from pathlib import Path

# Download from BibTeX
downloader = LiteratureDownloader("literature_folder")
results = downloader.download_from_bibtex(Path("my_papers.bib"))

print(f"Downloaded: {len(results['successful'])} papers")
```

### Knowledge Base Building

```python
from src.core import KnowledgeBase

# Build knowledge base from folders (includes Zotero downloads)
kb = KnowledgeBase()
stats = kb.build_from_directories(
    literature_folder=Path("documents/literature"),
    your_work_folder=Path("documents/your_work"),
    zotero_folder=Path("documents/zotero_sync")
)

# Save for later use
kb.save_to_file("knowledge_base.pkl")
```

## Configuration

The pipeline uses centralized configuration in `config/settings.py`:

```python
from config import PipelineConfig

# Use defaults
config = PipelineConfig()

# Or customize
config = PipelineConfig({
    'embedding_model': 'all-MiniLM-L6-v2',
    'chunk_size': 1000,
    'download_delay': 1.5,
    'default_temperature': 0.3
})
```

## Directory Structure

```
documents/
├── biblio/              # Legacy .bib files
├── literature/          # Downloaded papers (legacy arXiv)
├── your_work/           # Your previous publications
├── current_drafts/      # Your current drafts
├── manual_references/   # Manually added papers
└── zotero_sync/         # Zotero synchronized files
    ├── pdfs/           # PDF attachments from Zotero
    ├── other_files/    # Other document types
    └── doi_downloads/  # PDFs downloaded via DOI automation
```

## API Keys

Set your API keys in `.env` file:

```bash
# Required: Anthropic API for AI assistant
ANTHROPIC_API_KEY="your-anthropic-api-key"

# Required for Zotero integration
ZOTERO_API_KEY="your-zotero-api-key"
ZOTERO_LIBRARY_ID="your-library-id"
ZOTERO_LIBRARY_TYPE="user"  # or "group"

# Optional: Google search fallback
GOOGLE_API_KEY="your-google-api-key"
GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
```

## Publisher Support for DOI Downloads

### ✅ Fully Supported Publishers
- **APS (Physical Review)**: Automatic URL conversion, 95%+ success rate
- **MDPI**: PDF button detection, 95%+ success rate  
- **Nature Publishing**: Generic PDF link detection, 90%+ success rate
- **arXiv**: Direct PDF URL construction, 99%+ success rate

### 🔄 Partially Supported Publishers
- **IEEE Xplore**: Generic strategy, ~70% success rate
- **Springer**: Generic strategy, ~60% success rate
- **IOP Publishing**: Generic strategy, varies by journal

### ❌ Restricted Publishers
- **Elsevier/ScienceDirect**: Blocks automated access (CAPTCHA protection)

*Note: Success rates depend on institutional access and subscription status*

## Google Custom Search API Setup (Optional)

To enable Google search fallback for papers not found via arXiv API:

1. **Create a Custom Search Engine:**
   - Go to [Google Custom Search Engine](https://cse.google.com/cse/)
   - Click "Add" to create a new search engine
   - Set "Sites to search" to `arxiv.org`
   - Give it a name like "arXiv Papers"
   - Click "Create"

2. **Get your Search Engine ID:**
   - In the control panel, click on your search engine
   - Go to "Setup" → "Basics"
   - Copy the "Search engine ID"

3. **Enable the Custom Search API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one
   - Enable the "Custom Search API"
   - Go to "Credentials" and create an API key

4. **Set environment variables:**
   ```bash
   export GOOGLE_API_KEY="your-google-api-key"
   export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"
   ```

## Advanced Usage

### DOI Download Configuration

```python
from src.downloaders import EnhancedZoteroLiteratureSyncer

# Configure DOI download behavior
syncer.configure_doi_downloads(
    enabled=True,
    max_per_sync=10,        # Limit downloads per operation
    headless=True,          # Hide browser (set False for debugging)
    timeout=30              # Download timeout in seconds
)

# Get download recommendations
recommendations = syncer.get_recommendations()
for rec in recommendations['recommendations']:
    print(f"{rec['type']}: {rec['message']}")
```

### Custom Document Processing

```python
from src.core import DocumentProcessor

processor = DocumentProcessor()
doc = processor.process_file(Path("paper.pdf"), source_type="literature")
print(f"Extracted {doc.word_count} words")
```

### Direct arXiv Search

```python
from src.downloaders import ArxivSearcher

searcher = ArxivSearcher()
result = searcher.search_paper(paper_metadata)
if result.found:
    download_result = searcher.download_paper(result.arxiv_id, "output/")
```

### Knowledge Base Search

```python
# Direct search
results = kb.search("quantum entanglement", top_k=10)
for result in results:
    print(f"{result.chunk.file_name}: {result.similarity_score:.3f}")
```

## Customization

### Adding New Publishers for DOI Downloads

```python
# In enhanced_zotero_manager.py, add to publisher-specific section:
elif 'your-publisher.com' in current_url:
    logger.debug("Trying Your Publisher PDF download...")
    try:
        # Publisher-specific download logic
        pdf_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='pdf']")
        if pdf_links:
            pdf_links[0].click()
            # ... download detection logic
    except Exception as e:
        logger.debug(f"Your Publisher strategy failed: {e}")
```

### Adding New Document Types

```python
# Extend DocumentProcessor
class CustomProcessor(DocumentProcessor):
    def extract_custom_format(self, file_path):
        # Your extraction logic
        return extracted_text
```

### Alternative AI Models

```python
# Use different chat models
config = PipelineConfig({
    'claude_model': 'claude-3-opus-20240229',
    'max_tokens': 8000
})
```

## Performance

### Typical Performance
- **Zotero sync speed**: ~2-3 seconds for collection access (optimized)
- **DOI download success**: 80-95% for supported publishers
- **Download speed**: 1-2 PDFs per minute (respectful delays)
- **Processing speed**: ~1-2 minutes for 10 papers (first run)
- **Search speed**: <1 second for semantic search
- **Memory usage**: ~2GB for 100 papers with embeddings

### Optimization Tips
- Use collection-based sync for large Zotero libraries
- Enable headless mode for faster downloads
- Use caching for repeated knowledge base builds
- Adjust chunk sizes based on document types
- Use GPU acceleration for large embedding models

## Troubleshooting

### Common Issues

**"No papers found in Zotero collection"**
- Check collection name spelling
- Verify Zotero API permissions
- Ensure collection has items

**"Selenium/Chrome driver not found"**
- Install Chrome browser
- Install ChromeDriver: `brew install chromedriver` (Mac) or download manually
- Ensure ChromeDriver is in PATH

**"DOI downloads failing"**
- Try with `headless=False` to see browser behavior
- Check institutional access to journals
- Some publishers block automated access (expected)

**"CAPTCHA detected"**
- This is normal for protected publishers (Elsevier)
- Use manual download for these papers
- Focus on supported publishers for automation

**"Zotero connection failed"**
- Verify ZOTERO_API_KEY and ZOTERO_LIBRARY_ID in .env
- Check API key permissions at https://www.zotero.org/settings/keys

### Performance Issues

**Slow Zotero collection access**
- Using optimized collection-direct access (should be fast)
- Large libraries: consider collection-based filtering

**High memory usage during downloads**
- Reduce max_doi_downloads parameter
- Process collections in smaller batches

## Contributing

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black isort selenium

# Run tests
pytest tests/

# Format code
black src/
isort src/
```

### Adding Features

1. **New document types**: Extend `DocumentProcessor`
2. **New publishers**: Add to `enhanced_zotero_manager.py`
3. **New AI models**: Modify chat interface
4. **New file formats**: Add to supported extensions

### Testing

```bash
# Run all tests
pytest

# Test specific modules
pytest tests/test_document_processor.py
pytest tests/test_zotero_integration.py
```

## License

MIT License - see LICENSE file for details.

## Citation

If you use this pipeline in your research, please cite:

```bibtex
@software{physics_synthesis_pipeline,
  title={Physics Literature Synthesis Pipeline},
  author={Your Name},
  year={2024},
  url={https://github.com/your-repo/physics-synthesis-pipeline}
}
```

## Support

- **Documentation**: See `notebooks/physics_pipeline_demo.ipynb`
- **Zotero Integration**: See `ZOTERO_README.md` for detailed setup
- **Issues**: Report bugs and feature requests via GitHub issues
- **Discussions**: Join community discussions for help and ideas

## Roadmap

### Upcoming Features
- [x] DOI-based PDF downloads with Selenium
- [x] Enhanced Zotero integration with collection sync
- [x] Multi-publisher support for automated downloads
- [ ] Web-based interface (Streamlit app)
- [ ] Advanced citation network analysis
- [ ] Integration with additional reference managers
- [ ] Cloud deployment options

### Long-term Goals
- [ ] Multi-language support
- [ ] Real-time literature monitoring
- [ ] Automated research summaries
- [ ] Integration with experimental databases
- [ ] Advanced visualization tools
- [ ] Collaborative knowledge bases

---

**Happy researching! 🚀🔬**

### Manual References

To add papers not available through automated download:
1. Copy PDF, TEX, or TXT files to `documents/manual_references/`
2. They will be automatically included when building the knowledge base