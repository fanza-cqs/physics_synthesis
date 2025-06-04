# Physics Literature Synthesis Pipeline

A modular, automated pipeline for physics research that downloads literature from arXiv, builds a searchable knowledge base, and provides AI-powered research assistance.

## Overview

This pipeline helps physicists:
- **Automate literature collection** from Zotero bibliographies
- **Build searchable knowledge bases** from physics papers
- **Get AI assistance** grounded in relevant literature
- **Synthesize research** with source-backed responses

## Architecture

```
physics_synthesis_pipeline/
├── src/
│   ├── core/           # Document processing & embeddings
│   ├── downloaders/    # arXiv search & download
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

# Set your API key
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

### 2. Add Your Literature

```bash
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

### 📥 Literature Download
- Parse Zotero .bib files automatically
- Multi-strategy arXiv search (title, abstract, Google fallback)
- Download both PDF and TEX source files
- Comprehensive success reporting

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

## Usage Examples

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

### Literature Download

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

# Build knowledge base from folders
kb = KnowledgeBase()
stats = kb.build_from_directories(
    literature_folder=Path("documents/literature"),
    your_work_folder=Path("documents/your_work")
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
├── biblio/          # Place your .bib files here
├── literature/      # Downloaded papers (auto-created)
├── your_work/       # Your previous publications
└── current_drafts/  # Your current drafts
```

## API Keys

Set your Anthropic API key:

```bash
# Environment variable (recommended)
export ANTHROPIC_API_KEY="your-key"

# Or in config
config = PipelineConfig({'anthropic_api_key': 'your-key'})
```

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


## Advanced Usage

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

### Adding New Document Types

```python
# Extend DocumentProcessor
class CustomProcessor(DocumentProcessor):
    def extract_custom_format(self, file_path):
        # Your extraction logic
        return extracted_text
```

### Custom Search Providers

```python
# Extend ArxivSearcher for other sources
class CustomSearcher(ArxivSearcher):
    def search_custom_source(self, paper):
        # Your search logic
        return search_result
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
- **Download success rate**: 80-90% for physics papers
- **Processing speed**: ~1-2 minutes for 10 papers (first run)
- **Search speed**: <1 second for semantic search
- **Memory usage**: ~2GB for 100 papers with embeddings

### Optimization Tips
- Use caching for repeated knowledge base builds
- Adjust chunk sizes based on document types
- Use GPU acceleration for large embedding models
- Implement batch processing for large collections

## Troubleshooting

### Common Issues

**"No papers found in .bib file"**
- Check file encoding (use UTF-8)
- Ensure proper BibTeX format
- Verify file permissions

**"arXiv download failed"**
- Check internet connection
- Reduce download frequency (increase delay)
- Some papers may not be available in source format

**"Embedding creation failed"**
- Check available memory
- Try smaller chunk sizes
- Ensure sentence-transformers is installed correctly

**"API key invalid"**
- Verify your Anthropic API key
- Check environment variable is set
- Ensure sufficient API credits

### Performance Issues

**Slow knowledge base building**
- Use caching (`force_rebuild=False`)
- Process fewer documents initially
- Consider using smaller embedding models

**High memory usage**
- Reduce chunk sizes
- Process documents in batches
- Clear unused variables

## Contributing

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black isort

# Run tests
pytest tests/

# Format code
black src/
isort src/
```

### Adding Features

1. **New document types**: Extend `DocumentProcessor`
2. **New search providers**: Extend arXiv searcher patterns
3. **New AI models**: Modify chat interface
4. **New file formats**: Add to supported extensions

### Testing

```bash
# Run all tests
pytest

# Test specific modules
pytest tests/test_document_processor.py
pytest tests/test_embeddings.py
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
- **Issues**: Report bugs and feature requests via GitHub issues
- **Discussions**: Join community discussions for help and ideas

## Roadmap

### Upcoming Features
- [ ] Web-based interface (Streamlit app)
- [ ] Support for additional literature sources (APS, Nature, etc.)
- [ ] Advanced citation network analysis
- [ ] Integration with reference managers
- [ ] Cloud deployment options
- [ ] Collaborative knowledge bases

### Long-term Goals
- [ ] Multi-language support
- [ ] Real-time literature monitoring
- [ ] Automated research summaries
- [ ] Integration with experimental databases
- [ ] Advanced visualization tools

---

**Happy researching! 🚀🔬**

### Manual References

To add papers not available through arXiv:
1. Copy PDF, TEX, or TXT files to `documents/manual_references/`
2. They will be automatically included when building the knowledge base

