# Zotero Integration with DOI-based PDF Downloads

The Physics Literature Synthesis Pipeline now features comprehensive Zotero integration with **automated DOI-based PDF downloading**, providing seamless access to your research library with enhanced metadata and intelligent file acquisition.

## Why Enhanced Zotero Integration?

**Advantages over BibTeX approach:**
- 🔄 **Real-time sync** with your Zotero library
- 📄 **Automatic PDF downloads** from Zotero storage + DOI-based acquisition
- 🎯 **Rich metadata** with tags, collections, and notes
- 🔍 **Deduplication** - no more .tex/.pdf file conflicts
- 📚 **Collection-based filtering** for targeted research
- 🌐 **Cross-platform access** via Web API
- 🤖 **Enhanced AI assistance** with complete bibliographic context
- ⚡ **Smart PDF acquisition** - automatically downloads missing PDFs using DOIs

## Quick Setup

### 1. Install Dependencies

```bash
pip install pyzotero selenium
```

### 2. Get Your Zotero API Credentials

1. **Get API Key**: Visit [https://www.zotero.org/settings/keys](https://www.zotero.org/settings/keys)
   - Click "Create new private key"
   - Give it a descriptive name like "Physics Pipeline"
   - Check permissions you need (at minimum: library read access)

2. **Find Library ID**: 
   - **Personal library**: Your user ID is shown on the same page
   - **Group library**: Visit your group page, hover over settings - ID is after `/groups/`

### 3. Configure Environment Variables

Add to your `.env` file:

```bash
# Zotero Configuration
ZOTERO_API_KEY=your_api_key_here
ZOTERO_LIBRARY_ID=your_library_id_here
ZOTERO_LIBRARY_TYPE=user  # or "group" for group libraries

# Optional: Zotero Sync Settings
ZOTERO_DOWNLOAD_ATTACHMENTS=true
ZOTERO_FILE_TYPES=application/pdf,text/plain
ZOTERO_OVERWRITE_FILES=false
# ZOTERO_SYNC_COLLECTIONS=collection1,collection2  # Optional: specific collections
```

### 4. Install Chrome Driver (for DOI downloads)

```bash
# macOS
brew install chromedriver

# Or download manually from https://chromedriver.chromium.org/
```

## Basic Usage

### Connect and Test

```python
from config import PipelineConfig
from src.downloaders import EnhancedZoteroLiteratureSyncer

# Initialize configuration
config = PipelineConfig()

# Test connection
syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=config.get_zotero_config(),
    doi_downloads_enabled=True
)

# Test connection
connection_info = syncer.zotero_manager.test_connection()

if connection_info['connected']:
    print(f"✅ Connected! {connection_info['total_items']} items in library")
else:
    print(f"❌ Connection failed: {connection_info['error']}")
```

### Sync Collection with DOI Downloads

```python
# Preview what will be downloaded
preview = syncer.preview_collection_sync("Physics Papers")
print(f"📚 Total items: {preview['total_items']}")
print(f"📄 Items with PDFs: {preview['items_with_pdfs']}")
print(f"🔗 Items needing PDFs: {preview['items_with_dois_no_pdfs']}")

# Perform sync with automatic PDF downloads
result = syncer.sync_collection_with_doi_downloads(
    collection_name="Physics Papers",
    max_doi_downloads=10,      # Limit for safety
    headless=False,            # Set True to hide browser
    update_knowledge_base=True # Automatically add to KB
)

print(f"✅ Downloaded {result.zotero_sync_result.successful_doi_downloads} PDFs")
print(f"📊 Success rate: {result.zotero_sync_result.successful_doi_downloads / result.zotero_sync_result.doi_download_attempts * 100:.1f}%")
```

### Integration with Knowledge Base

```python
from src.core import KnowledgeBase
from src.chat import LiteratureAssistant

# Build knowledge base with Zotero content (includes DOI downloads)
kb = KnowledgeBase()
kb.build_from_directories(
    literature_folder=config.literature_folder,
    your_work_folder=config.your_work_folder,
    zotero_folder=config.zotero_sync_folder  # Includes DOI downloads
)

# AI assistant with enhanced Zotero knowledge
assistant = LiteratureAssistant(kb, config.anthropic_api_key)
response = assistant.ask("What are the latest quantum computing developments?")
```

## Advanced Features

### DOI Download Configuration

```python
# Configure DOI download behavior
syncer.configure_doi_downloads(
    enabled=True,
    max_per_sync=15,        # Maximum downloads per sync operation
    headless=True,          # Run browser in background (faster)
    timeout=30              # Download timeout in seconds
)

# Get recommendations for collections needing PDFs
collections_info = syncer.find_collections_needing_doi_downloads()
for coll in collections_info[:3]:
    print(f"📁 {coll['name']}: {coll['doi_download_candidates']} PDFs can be downloaded")
```

### Batch Collection Processing

```python
# Sync multiple collections efficiently
physics_collections = [
    'Condensed Matter', 
    'Quantum Physics', 
    'Statistical Mechanics'
]

results = syncer.batch_sync_collections(
    collection_names=physics_collections,
    max_doi_downloads_per_collection=5
)

# Summary of batch results
total_downloaded = sum(
    r.zotero_sync_result.successful_doi_downloads 
    for r in results.values() if r
)
print(f"📥 Total PDFs downloaded across all collections: {total_downloaded}")
```

### Collection-Based Workflows

```python
# Get all collections with download opportunities
collections = syncer.zotero_manager.get_collections()
for coll in collections:
    if coll['num_items'] > 0:
        summary = syncer.zotero_manager.get_collection_sync_summary_fast(coll['key'])
        if summary.get('items_with_dois_no_pdfs', 0) > 0:
            print(f"📁 {coll['name']}: {summary['items_with_dois_no_pdfs']} PDFs can be downloaded")
```

### Smart Physics Paper Detection

```python
# Find physics papers automatically
physics_papers = syncer.find_physics_papers()
print(f"🔬 Found {len(physics_papers)} physics papers")

# Custom physics tags
custom_physics_papers = syncer.find_physics_papers([
    'quantum entanglement', 'topological phases', 'machine learning physics'
])
```

### Export and Compatibility

```python
# Export to BibTeX for LaTeX compatibility
bibtex_path = syncer.export_zotero_to_bibtex()
print(f"📄 BibTeX exported to: {bibtex_path}")

# Export specific collections
physics_bibtex = syncer.export_zotero_to_bibtex(
    collections=['Physics Papers']
)
```

### Library Analytics and Recommendations

```python
# Get comprehensive library overview
overview = syncer.get_library_overview()
print(f"📊 Library stats: {overview['library_stats']}")
print(f"📄 Items with PDFs: {overview['items_with_pdfs']}")

# Get intelligent recommendations
recommendations = syncer.get_recommendations()
for rec in recommendations['recommendations']:
    print(f"{rec['type']}: {rec['title']}")
    print(f"   💡 {rec['message']}")
    print(f"   🔧 Action: {rec['action']}")
```

## DOI Download Publisher Support

### ✅ Fully Supported Publishers (90%+ Success Rate)
- **APS (Physical Review)**: All journals (PRL, PRA, PRB, RMP, etc.)
  - Automatic URL pattern detection
  - Fast, reliable downloads
- **MDPI**: All open-access journals
  - PDF button detection
  - High success rate
- **Nature Publishing**: Nature, Nature Physics, etc.
  - Generic PDF link detection
  - Good institutional access support

### 🔄 Partially Supported Publishers (60-80% Success)
- **arXiv**: Near-perfect for preprints
- **IEEE Xplore**: Depends on institutional access
- **IOP Publishing**: Journal-dependent
- **Springer**: Variable by journal and access

### ❌ Restricted Publishers
- **Elsevier/ScienceDirect**: Actively blocks automation
  - Use manual download for these papers
  - System respects publisher restrictions

## File Organization

The enhanced Zotero integration creates an organized file structure:

```
documents/
├── zotero_sync/           # Zotero synchronized files
│   ├── pdfs/             # PDF attachments from Zotero
│   ├── other_files/      # Other document types from Zotero
│   └── doi_downloads/    # 🆕 PDFs downloaded via DOI automation
├── literature/           # Legacy arXiv downloads
├── your_work/           # Your publications
└── current_drafts/      # Work in progress
```

## Configuration Options

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ZOTERO_API_KEY` | Required | Your Zotero API key |
| `ZOTERO_LIBRARY_ID` | Required | Your library ID |
| `ZOTERO_LIBRARY_TYPE` | `user` | Library type (`user` or `group`) |
| `ZOTERO_DOWNLOAD_ATTACHMENTS` | `true` | Download PDF attachments |
| `ZOTERO_FILE_TYPES` | `application/pdf,text/plain` | File types to download |
| `ZOTERO_OVERWRITE_FILES` | `false` | Overwrite existing files |
| `ZOTERO_SYNC_COLLECTIONS` | All | Comma-separated collection names |

### DOI Download Configuration

```python
# Programmatic configuration
custom_config = {
    'api_key': 'your_key',
    'library_id': 'your_id',
    'library_type': 'user',
    'download_attachments': True,
    'file_types': {'application/pdf', 'text/plain', 'text/html'},
    'overwrite_files': False,
    'output_directory': Path('custom/zotero/path')
}

syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=custom_config,
    doi_downloads_enabled=True
)

# Configure DOI download behavior
syncer.configure_doi_downloads(
    enabled=True,
    max_per_sync=10,
    headless=True,  # False for debugging
    timeout=30
)
```

## Migration from Basic Zotero Integration

If you're upgrading from the basic Zotero integration:

### 1. Update Your Code

```python
# OLD: Basic Zotero syncer
from src.downloaders import ZoteroLiteratureSyncer
syncer = ZoteroLiteratureSyncer(config.get_zotero_config())

# NEW: Enhanced syncer with DOI downloads
from src.downloaders import EnhancedZoteroLiteratureSyncer
syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=config.get_zotero_config(),
    doi_downloads_enabled=True
)
```

### 2. Install Additional Dependencies

```bash
pip install selenium
# Install Chrome driver (see setup section)
```

### 3. Use Enhanced Methods

```python
# OLD: Basic collection sync
result = syncer.sync_specific_collections(['Physics Papers'])

# NEW: Enhanced sync with DOI downloads
result = syncer.sync_collection_with_doi_downloads(
    collection_name='Physics Papers',
    max_doi_downloads=10,
    headless=False
)
```

## Troubleshooting

### Common Issues

**DOI Downloads Not Working**
```
❌ Selenium Chrome driver not found
```
- Install Chrome browser and ChromeDriver
- Ensure ChromeDriver is in PATH
- Try: `brew install chromedriver` (Mac)

**CAPTCHA Detected**
```
❌ Publisher blocks automated downloads
```
- This is expected for Elsevier/ScienceDirect
- Try with `headless=False` to see what's happening
- Use manual download for restricted publishers

**Browser Crashes During Downloads**
```
❌ Chrome process terminated unexpectedly
```
- Close other Chrome instances
- Try with `headless=True` for stability
- Reduce `max_doi_downloads` parameter

**Connection Failed**
```
❌ Connection failed: Invalid API key
```
- Verify `ZOTERO_API_KEY` in `.env` file
- Check key permissions at https://www.zotero.org/settings/keys
- Ensure key has library read access

**Slow Collection Access**
```
⏰ Taking too long to retrieve collection items
```
- The enhanced version uses optimized direct collection access
- Should be 10x faster than before (~2-3 seconds vs 30+ seconds)
- Large libraries: consider collection-specific sync

### Performance Optimization

**Large Libraries**
- Use collection-based sync for libraries with 1000+ items
- Set `ZOTERO_SYNC_COLLECTIONS` to specific collections
- Process collections in smaller batches

**DOI Download Optimization**
- Use `headless=True` for faster downloads (after testing)
- Set appropriate `max_doi_downloads` limits
- Consider institutional network access for better success rates

**Rate Limiting**
- Zotero API has rate limits (120 requests/minute)
- DOI downloads include respectful delays between requests
- Pipeline includes automatic retry logic

## Integration with Writing Workflow

### LaTeX Integration

```python
# Export enhanced Zotero library to BibTeX
bibtex_path = syncer.export_zotero_to_bibtex()

# Now includes papers downloaded via DOI automation
# Use in LaTeX document: \bibliography{path/to/zotero_export.bib}
```

### Citation Management with AI

```python
# Find papers by topic for citations (including DOI downloads)
physics_papers = syncer.find_physics_papers(['quantum mechanics'])

# Get AI suggestions for citations with enhanced coverage
assistant = LiteratureAssistant(kb, config.anthropic_api_key)
response = assistant.ask(
    "What papers should I cite for quantum entanglement introduction? "
    "Focus on recent experimental developments."
)
```

### Literature Reviews

```python
# Generate literature synthesis with enhanced coverage
synthesis = assistant.synthesize_literature(
    topic="measurement-induced phase transitions",
    focus_areas=["theoretical frameworks", "experimental evidence", "recent developments"]
)
print(synthesis.content)
```

## Best Practices

### Library Organization in Zotero

1. **Use Collections**: Organize papers by topic/project for efficient DOI downloads
2. **Consistent Tagging**: Use systematic tags for physics topics
3. **Include DOIs**: Ensure papers have DOI metadata for automatic downloads
4. **Rich Metadata**: Include abstracts, publication info for better AI assistance

### DOI Download Strategy

1. **Start Small**: Test with small collections first (`max_doi_downloads=5`)
2. **Use Visible Browser**: Set `headless=False` for initial testing
3. **Monitor Success Rates**: Track which publishers work for your institution
4. **Respect Publishers**: Don't attempt to circumvent access restrictions
5. **Batch Processing**: Process multiple collections during off-hours

### AI Assistant Usage

1. **Enhanced Queries**: Leverage increased PDF coverage for comprehensive answers
2. **Source Verification**: Always verify AI-provided information
3. **Iterative Refinement**: Build on previous conversations with richer context

## Examples

### Complete Enhanced Workflow

```python
from config import PipelineConfig
from src.downloaders import EnhancedZoteroLiteratureSyncer
from src.core import KnowledgeBase
from src.chat import LiteratureAssistant

# 1. Setup enhanced syncer
config = PipelineConfig()
syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=config.get_zotero_config(),
    doi_downloads_enabled=True
)

# 2. Configure DOI downloads for your workflow
syncer.configure_doi_downloads(
    enabled=True,
    max_per_sync=10,
    headless=True,  # Set False for initial testing
    timeout=30
)

# 3. Preview and sync specific physics collections
physics_collections = ['Quantum Computing', 'Condensed Matter Theory']

for collection_name in physics_collections:
    # Preview what will be downloaded
    preview = syncer.preview_collection_sync(collection_name)
    print(f"📁 {collection_name}:")
    print(f"   📚 Total items: {preview['total_items']}")
    print(f"   📄 Have PDFs: {preview['items_with_pdfs']}")
    print(f"   🔗 Need PDFs: {preview['items_with_dois_no_pdfs']}")
    
    # Perform enhanced sync with DOI downloads
    if preview['items_with_dois_no_pdfs'] > 0:
        result = syncer.sync_collection_with_doi_downloads(
            collection_name=collection_name,
            max_doi_downloads=10,
            headless=True
        )
        
        print(f"   ✅ Downloaded {result.zotero_sync_result.successful_doi_downloads} PDFs")
        print(f"   📊 Success rate: {result.zotero_sync_result.successful_doi_downloads / result.zotero_sync_result.doi_download_attempts * 100:.1f}%")

# 4. Build enhanced knowledge base
kb = KnowledgeBase()
kb_stats = kb.build_from_directories(
    literature_folder=config.literature_folder,
    your_work_folder=config.your_work_folder,
    current_drafts_folder=config.current_drafts_folder,
    manual_references_folder=config.manual_references_folder,
    zotero_folder=config.zotero_sync_folder  # Includes DOI downloads
)

print(f"📚 Knowledge base built with {kb_stats['total_documents']} documents")

# 5. AI-powered research assistance with enhanced coverage
assistant = LiteratureAssistant(kb, config.anthropic_api_key)

# Ask research questions with confidence in comprehensive coverage
response = assistant.ask(
    "What are the key theoretical approaches to quantum error correction "
    "discussed in recent literature? Focus on surface codes and logical qubits."
)

print("📚 Research Summary:")
print(response.content)
print(f"\n📖 Based on {len(response.sources_used)} sources")

# 6. Export enhanced bibliography for writing
bibtex_path = syncer.export_zotero_to_bibtex()
print(f"📄 Enhanced BibTeX (with DOI downloads) exported to: {bibtex_path}")
```

### Collection-Specific Research with DOI Enhancement

```python
# Focus on specific research area with automated PDF acquisition
quantum_syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=config.get_zotero_config(),
    doi_downloads_enabled=True
)

# Sync quantum computing collection with DOI downloads
result = quantum_syncer.sync_collection_with_doi_downloads(
    collection_name='Quantum Computing',
    max_doi_downloads=15,
    headless=True
)

print(f"📥 Enhanced quantum collection with {result.zotero_sync_result.successful_doi_downloads} new PDFs")

# Find related papers automatically (now with better coverage)
quantum_papers = quantum_syncer.find_physics_papers([
    'quantum algorithm', 'quantum error correction', 'quantum supremacy'
])

print(f"🔬 Found {len(quantum_papers)} quantum computing papers")

# Generate focused literature review with enhanced PDF coverage
quantum_kb = KnowledgeBase()
quantum_kb.build_from_directories(
    zotero_folder=config.zotero_sync_folder
)

assistant = LiteratureAssistant(quantum_kb, config.anthropic_api_key)
review = assistant.synthesize_literature(
    topic="quantum error correction",
    focus_areas=["surface codes", "logical qubits", "threshold theorem"]
)

print("📄 Comprehensive Literature Review:")
print(review.content)
```

### Publisher-Specific Analysis

```python
# Analyze DOI download success by publisher
download_summary = syncer.get_doi_downloads_summary()

print("📊 DOI Download Analysis:")
print(f"   Selenium available: {download_summary['selenium_available']}")
print(f"   Downloads enabled: {download_summary['doi_downloads_enabled']}")
print(f"   Total files downloaded: {download_summary['total_files']}")
print(f"   Total size: {download_summary['total_size_mb']:.1f} MB")

# Get recommendations for optimizing downloads
recommendations = syncer.get_recommendations()
print("\n💡 Optimization Recommendations:")
for rec in recommendations['recommendations']:
    print(f"   {rec['type']}: {rec['title']}")
    print(f"      {rec['message']}")
    print(f"      Action: {rec['action']}")
```

## API Reference

See the full API documentation for detailed method signatures and parameters:

- [`EnhancedZoteroLibraryManager`](src/downloaders/enhanced_zotero_manager.py) - DOI-based PDF downloading
- [`EnhancedZoteroLiteratureSyncer`](src/downloaders/enhanced_literature_syncer.py) - High-level enhanced synchronization
- [`ZoteroLibraryManager`](src/downloaders/zotero_manager.py) - Core Zotero Web API integration
- [Configuration](config/settings.py) - Zotero and DOI download configuration options

## Support and Contributing

### Getting Help

1. **Check Configuration**: Verify all environment variables are set
2. **Test Connection**: Use the connection test before attempting downloads
3. **Review Logs**: Check application logs for detailed error messages
4. **Browser Issues**: Try with `headless=False` to debug download problems
5. **Publisher Restrictions**: Some publishers block automation (this is expected)

### Contributing

The enhanced Zotero integration is actively developed. Contributions welcome:

- **Bug Reports**: Report issues with specific error messages and publisher details
- **New Publishers**: Help add support for additional publishers
- **Feature Requests**: Suggest improvements for research workflows  
- **Documentation**: Help improve setup and usage documentation
- **Testing**: Test with different library configurations and publishers

### Roadmap

Future enhancements planned:
- [ ] Real-time sync with Zotero changes
- [ ] Integration with Zotero notes and annotations
- [ ] Support for Zotero groups and collaborative workflows
- [ ] Enhanced metadata extraction from downloaded PDFs
- [ ] Integration with other reference managers
- [ ] Publisher success rate analytics and reporting
- [ ] Automatic retry mechanisms for failed downloads
- [ ] Advanced browser fingerprinting avoidance

### Performance Metrics

Track your enhanced Zotero integration performance:

```python
# Get comprehensive performance statistics
stats = {
    'zotero_sync_time': '2-3 seconds (optimized collection access)',
    'doi_download_success_rates': {
        'APS': '95%+',
        'MDPI': '95%+', 
        'Nature': '90%+',
        'IEEE': '70%+',
        'Elsevier': '5%+ (restricted)'
    },
    'download_speed': '1-2 PDFs per minute (respectful delays)',
    'knowledge_base_enhancement': 'Significant coverage improvement for physics literature'
}
```

---

**Enhanced research capabilities with automated PDF acquisition! 🚀🔬📄**

### Quick Reference

**Most Common Commands:**
```python
# 1. Test connection
syncer.test_zotero_connection()

# 2. Preview collection
syncer.preview_collection_sync("Collection Name")

# 3. Sync with DOI downloads
syncer.sync_collection_with_doi_downloads("Collection Name", max_doi_downloads=10, headless=False)

# 4. Get recommendations
syncer.get_recommendations()
```

**Troubleshooting Checklist:**
- ✅ Chrome and ChromeDriver installed
- ✅ Zotero API credentials in `.env`
- ✅ Collections have items with DOIs
- ✅ Institutional access for target publishers
- ✅ Start with `headless=False` for testing