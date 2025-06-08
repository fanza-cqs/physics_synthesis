# Installation Guide

Complete installation instructions for the Physics Literature Synthesis Pipeline.

## 📋 System Requirements

- **Python**: 3.8 or higher
- **Operating System**: Windows, macOS, or Linux
- **Memory**: 4GB RAM minimum (8GB recommended for large libraries)
- **Storage**: 2GB free space (more for downloaded papers)
- **Browser**: Chrome or Chromium (for PDF downloads)

## 🚀 Installation Methods

### Method 1: Standard Installation (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd physics_synthesis_pipeline

# 2. Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Install optional dependencies for enhanced features
pip install selenium  # For DOI-based PDF downloads
```

### Method 2: Development Installation

```bash
# For contributors and developers
git clone <repository-url>
cd physics_synthesis_pipeline
pip install -e .  # Editable installation
pip install -r requirements-dev.txt  # Development dependencies
```

## 📦 Dependencies

### Core Dependencies
```
pyzotero>=1.5.0          # Zotero Web API integration
anthropic>=0.7.0         # Claude AI integration
sentence-transformers    # Text embeddings
scikit-learn            # Machine learning utilities
PyPDF2                  # PDF text extraction
pymupdf                 # Advanced PDF processing
bibtexparser           # BibTeX file parsing
python-dotenv          # Environment variable management
jupyter                # Notebook interface
pandas                 # Data manipulation
numpy                  # Numerical computing
requests               # HTTP requests
pathlib                # Path utilities
```

### Enhanced Features Dependencies
```
selenium>=4.0.0         # Browser automation for PDF downloads
googlesearch-python     # Google search fallback
matplotlib             # Plotting and visualization
plotly                 # Interactive visualizations
```

## 🔧 Browser Setup for PDF Downloads

### Chrome/Chromium Setup

#### macOS
```bash
# Install Chrome
brew install --cask google-chrome

# Install ChromeDriver
brew install chromedriver
```

#### Linux (Ubuntu/Debian)
```bash
# Install Chrome
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable

# Install ChromeDriver
sudo apt install chromium-chromedriver
```

#### Windows
1. Download Chrome from https://www.google.com/chrome/
2. Download ChromeDriver from https://chromedriver.chromium.org/
3. Add ChromeDriver to your PATH

### Verify Browser Setup
```bash
# Test ChromeDriver installation
python -c "
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
options = Options()
options.add_argument('--headless')
driver = webdriver.Chrome(options=options)
print('✅ ChromeDriver working correctly')
driver.quit()
"
```

## 🔑 API Keys Setup

### Required API Keys

1. **Anthropic API Key** (Required for AI features)
   - Visit: https://console.anthropic.com/
   - Create account and generate API key
   - Used for: AI research assistant, literature analysis

2. **Zotero API Key** (Required for Zotero integration)
   - Visit: https://www.zotero.org/settings/keys
   - Create new private key with read/write permissions
   - Note your User ID (library ID)
   - Used for: Literature synchronization, PDF integration

### Optional API Keys

3. **Google Custom Search API** (Optional - for enhanced search)
   - Visit: https://developers.google.com/custom-search/v1/introduction
   - Create API key and search engine ID
   - Used for: Fallback paper search when arXiv fails

### Environment Configuration

Create a `.env` file in your project root:

```bash
# Required API Keys
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ZOTERO_API_KEY=your-zotero-api-key-here
ZOTERO_LIBRARY_ID=your-zotero-user-id-here
ZOTERO_LIBRARY_TYPE=user

# Optional API Keys
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_SEARCH_ENGINE_ID=your-search-engine-id-here

# Optional Configuration
CHUNK_SIZE=1000
EMBEDDING_MODEL=all-MiniLM-L6-v2
DEFAULT_TEMPERATURE=0.3
MAX_RETRIES=3
DOWNLOAD_DELAY=1.2
```

### Environment Variables Reference

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Yes | Claude AI API key | None |
| `ZOTERO_API_KEY` | Yes | Zotero Web API key | None |
| `ZOTERO_LIBRARY_ID` | Yes | Your Zotero user/group ID | None |
| `ZOTERO_LIBRARY_TYPE` | No | "user" or "group" | "user" |
| `GOOGLE_API_KEY` | No | Google Custom Search API key | None |
| `GOOGLE_SEARCH_ENGINE_ID` | No | Google search engine ID | None |
| `CHUNK_SIZE` | No | Text chunking size for embeddings | 1000 |
| `EMBEDDING_MODEL` | No | Sentence transformer model | "all-MiniLM-L6-v2" |
| `DEFAULT_TEMPERATURE` | No | AI response creativity | 0.3 |
| `MAX_RETRIES` | No | Download retry attempts | 3 |
| `DOWNLOAD_DELAY` | No | Delay between downloads (seconds) | 1.2 |

## 📁 Directory Structure Setup

The installation will create the following directory structure:

```
physics_synthesis_pipeline/
├── documents/                    # Your papers and literature
│   ├── zotero_sync/             # Enhanced Zotero synchronized content
│   │   ├── pdfs/                # PDF attachments from Zotero
│   │   ├── other_files/         # Other document types
│   │   └── doi_downloads/       # Automatically downloaded PDFs
│   ├── literature/              # Legacy arXiv downloads
│   ├── your_work/               # Your publications
│   ├── current_drafts/          # Work in progress
│   └── manual_references/       # Manually added papers
├── config/                      # Configuration files
├── src/                         # Source code
├── notebooks/                   # Jupyter notebooks
├── reports/                     # Generated reports
└── physics_knowledge_base.pkl   # Cached knowledge base
```

## ✅ Installation Verification

### Test Core Installation
```bash
# Test core imports
python -c "
from config import PipelineConfig
from src.core import KnowledgeBase
from src.chat import LiteratureAssistant
print('✅ Core installation successful')
"
```

### Test Zotero Integration
```bash
# Test Zotero connection
python -c "
from src.downloaders import EnhancedZoteroLiteratureSyncer
from config import PipelineConfig
config = PipelineConfig()
syncer = EnhancedZoteroLiteratureSyncer(config.get_zotero_config())
result = syncer.zotero_manager.test_connection()
print(f'✅ Zotero connected: {result[\"connected\"]}')
print(f'📚 Library items: {result[\"total_items\"]}')
"
```

### Test Enhanced Features
```bash
# Test DOI downloads capability
python -c "
from src.downloaders import get_zotero_capabilities
caps = get_zotero_capabilities()
print('📊 Available capabilities:')
for name, info in caps['capabilities'].items():
    status = '✅' if info['available'] else '❌'
    print(f'  {status} {name}: {info[\"description\"]}')
"
```

## 🔧 Troubleshooting Installation

### Common Issues

#### Python Version Issues
```bash
# Check Python version
python --version  # Should be 3.8+

# If using older Python, install with pyenv or conda
conda create -n physics-pipeline python=3.9
conda activate physics-pipeline
```

#### ChromeDriver Issues
```bash
# Check ChromeDriver
chromedriver --version

# If not found, download manually:
# 1. Check Chrome version: chrome://version/
# 2. Download matching ChromeDriver
# 3. Add to PATH
```

#### API Key Issues
```bash
# Verify API keys
python -c "
from config import PipelineConfig
config = PipelineConfig()
status = config.check_env_file()
for key, value in status.items():
    print(f'{key}: {\"✅\" if value else \"❌\"}')
"
```

#### Permission Issues (Linux/macOS)
```bash
# Fix ChromeDriver permissions
sudo chmod +x /usr/local/bin/chromedriver

# Fix Python package permissions
pip install --user -r requirements.txt
```

### Getting Help

If you encounter issues:

1. **Check the logs**: Look in `logs/` directory for error details
2. **Verify dependencies**: Run verification tests above
3. **Check configuration**: Ensure all API keys are correct
4. **Update packages**: `pip install --upgrade -r requirements.txt`
5. **See troubleshooting guide**: [troubleshooting.md](troubleshooting.md)

## 🚀 Next Steps

After successful installation:

1. **Configure Zotero**: See [Zotero Integration Guide](zotero-integration.md)
2. **Run examples**: Check out [Examples](examples.md)
3. **Explore configuration**: Review [Configuration Guide](configuration.md)
4. **Try the demo**: Open `notebooks/enhanced_physics_pipeline_demo.ipynb`