# Troubleshooting Guide

Comprehensive troubleshooting guide for common issues with the Physics Literature Synthesis Pipeline.

## 🚨 Quick Diagnostics

Run this script to quickly identify common issues:

```python
#!/usr/bin/env python3
"""Quick diagnostic script for Physics Pipeline issues."""

from config import PipelineConfig
from src.downloaders import get_zotero_capabilities

def quick_diagnosis():
    print("🔍 PHYSICS PIPELINE QUICK DIAGNOSIS")
    print("=" * 45)
    
    # Test 1: Configuration
    try:
        config = PipelineConfig()
        config.validate_api_keys()
        config.validate_zotero_config()
        print("✅ Configuration: OK")
    except Exception as e:
        print(f"❌ Configuration: {e}")
        return False
    
    # Test 2: Dependencies
    capabilities = get_zotero_capabilities()
    for name, info in capabilities['capabilities'].items():
        status = "✅" if info['available'] else "❌"
        print(f"{status} {name}: {info['description']}")
    
    # Test 3: Zotero Connection
    try:
        from src.downloaders import EnhancedZoteroLiteratureSyncer
        syncer = EnhancedZoteroLiteratureSyncer(config.get_zotero_config())
        connection = syncer.zotero_manager.test_connection()
        if connection['connected']:
            print(f"✅ Zotero: Connected ({connection['total_items']} items)")
        else:
            print(f"❌ Zotero: {connection['error']}")
    except Exception as e:
        print(f"❌ Zotero: {e}")
    
    return True

if __name__ == "__main__":
    quick_diagnosis()
```

## 🔧 Installation Issues

### Python Version Problems

**Problem**: `ImportError` or compatibility issues
```bash
❌ ImportError: This package requires Python 3.8+
```

**Solution**:
```bash
# Check Python version
python --version

# If < 3.8, install newer Python
# Using pyenv (recommended)
pyenv install 3.9.16
pyenv local 3.9.16

# Using conda
conda create -n physics-pipeline python=3.9
conda activate physics-pipeline
```

### ChromeDriver Issues

**Problem**: `WebDriverException: 'chromedriver' executable not found`
```bash
❌ selenium.common.exceptions.WebDriverException: 'chromedriver' executable needs to be in PATH
```

**Solutions**:

#### macOS
```bash
# Install via Homebrew (recommended)
brew install chromedriver

# Manual installation
# 1. Download from https://chromedriver.chromium.org/
# 2. Move to /usr/local/bin/
# 3. Make executable: chmod +x /usr/local/bin/chromedriver
```

#### Linux (Ubuntu/Debian)
```bash
# Install via package manager
sudo apt update
sudo apt install chromium-chromedriver

# Or install Chrome and ChromeDriver manually
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list
sudo apt update
sudo apt install google-chrome-stable chromium-chromedriver
```

#### Windows
```bash
# 1. Install Chrome from https://www.google.com/chrome/
# 2. Download ChromeDriver from https://chromedriver.chromium.org/
# 3. Extract to C:\Windows\ or add to PATH
# 4. Verify with: chromedriver --version
```

**Verification**:
```python
# Test ChromeDriver installation
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
try:
    driver = webdriver.Chrome(options=options)
    print("✅ ChromeDriver working correctly")
    driver.quit()
except Exception as e:
    print(f"❌ ChromeDriver issue: {e}")
```

### Package Installation Issues

**Problem**: `pip install` failures or conflicts
```bash
❌ ERROR: Could not build wheels for some-package
```

**Solutions**:
```bash
# Use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install with verbose output to see specific errors
pip install -v -r requirements.txt

# If specific package fails, try conda
conda install package-name
```

## 🔑 API Key Issues

### Anthropic API Key Problems

**Problem**: `AuthenticationError` or `PermissionDeniedError`
```bash
❌ anthropic.AuthenticationError: Invalid API key
```

**Solutions**:
```bash
# 1. Check API key format (should start with 'sk-ant-')
echo $ANTHROPIC_API_KEY

# 2. Verify key is active at https://console.anthropic.com/
# 3. Check for extra spaces or newlines
export ANTHROPIC_API_KEY="$(echo $ANTHROPIC_API_KEY | tr -d '[:space:]')"

# 4. Test key directly
python -c "
import anthropic
client = anthropic.Anthropic(api_key='your-key-here')
try:
    response = client.messages.create(
        model='claude-3-sonnet-20240229',
        max_tokens=10,
        messages=[{'role': 'user', 'content': 'Hi'}]
    )
    print('✅ Anthropic API key working')
except Exception as e:
    print(f'❌ API key issue: {e}')
"
```

### Zotero API Key Problems

**Problem**: `zotero.zotero.UnsupportedParams` or `403 Forbidden`
```bash
❌ pyzotero.zotero_errors.UnsupportedParams: The API key provided does not have permission
```

**Solutions**:
```bash
# 1. Check API key has read/write permissions
# Visit: https://www.zotero.org/settings/keys
# Ensure "Allow library access" and "Allow write access" are checked

# 2. Verify Library ID is correct
# Personal library: Your user ID from the API keys page
# Group library: Group ID from group URL

# 3. Check library type setting
export ZOTERO_LIBRARY_TYPE="user"  # or "group"

# 4. Test connection
python -c "
from pyzotero import zotero
zot = zotero.Zotero('your-library-id', 'user', 'your-api-key')
try:
    items = zot.top(limit=1)
    print('✅ Zotero API working')
except Exception as e:
    print(f'❌ Zotero issue: {e}')
"
```

## 📚 Zotero Integration Issues

### Connection Problems

**Problem**: `requests.exceptions.HTTPError: 404 Client Error`
```bash
❌ HTTPError: 404 Client Error: Not Found for url: https://api.zotero.org/users/invalid-id
```

**Diagnosis**:
```python
# Check your Zotero configuration
from config import PipelineConfig
config = PipelineConfig()

print(f"Library ID: {config.zotero_library_id}")
print(f"Library Type: {config.zotero_library_type}")
print(f"API Key: {config.zotero_api_key[:10]}...")

# Verify library exists
import requests
if config.zotero_library_type == "user":
    url = f"https://api.zotero.org/users/{config.zotero_library_id}"
else:
    url = f"https://api.zotero.org/groups/{config.zotero_library_id}"

response = requests.get(url)
print(f"Library exists: {response.status_code == 200}")
```

**Solutions**:
1. **Wrong Library ID**: Check your user ID on https://www.zotero.org/settings/keys
2. **Wrong Library Type**: Use "user" for personal library, "group" for group library
3. **Private Group**: Ensure API key has access to the group

### PDF Integration Failures

**Problem**: PDFs download but don't integrate into Zotero
```bash
✅ PDF downloaded successfully
❌ Attachment creation failed: Item not found
```

**Diagnosis**:
```python
# Check if items exist in Zotero
def diagnose_integration_failure(item_key):
    try:
        syncer = EnhancedZoteroLiteratureSyncer(config.get_zotero_config())
        item = syncer.zotero_manager.zot.item(item_key)
        print(f"✅ Item exists: {item['data']['title']}")
        
        # Check existing attachments
        attachments = syncer.zotero_manager.get_item_attachments(item_key)
        print(f"📎 Existing attachments: {len(attachments)}")
        
        return True
    except Exception as e:
        print(f"❌ Item issue: {e}")
        return False
```

**Solutions**:
1. **Item Key Mismatch**: Ensure item exists in the specified collection
2. **API Permissions**: Verify API key has write access
3. **File Path Issues**: Check PDF file exists and is readable
4. **Use Attach Mode**: Switch to `integration_mode="attach"` (most reliable)

## 🔄 DOI Download Issues

### Browser Automation Problems

**Problem**: Downloads fail with timeout or navigation errors
```bash
❌ TimeoutException: Message: timeout: Timed out receiving message from renderer
```

**Solutions**:
```python
# Increase timeout and disable headless mode for debugging
syncer.configure_doi_downloads(
    timeout=60,        # Longer timeout
    headless=False,    # See what's happening
    max_per_sync=3     # Smaller batches
)

# Test with single paper
result = syncer.sync_collection_with_doi_downloads_and_integration(
    collection_name="Test Collection",
    max_doi_downloads=1,
    headless=False
)
```

### Publisher-Specific Failures

**Problem**: Specific publishers always fail
```bash
❌ Science papers failing: Publisher blocks automation
❌ APS papers failing: Access denied
```

**Diagnosis by Publisher**:

#### Science/AAAS (Expected to fail)
```python
# This is normal - Science blocks automation
if 'science.org' in url:
    print("⚠️ Science papers require manual download (CAPTCHA protection)")
    # Solution: Download manually from browser
```

#### APS (Should work with institutional access)
```python
# Check institutional access
def test_aps_access():
    test_url = "https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.128.010401"
    
    from selenium import webdriver
    driver = webdriver.Chrome()
    driver.get(test_url)
    
    # Check if abstract is accessible
    title = driver.find_element(By.TAG_NAME, "h1").text
    print(f"Can access APS: {len(title) > 0}")
    
    # Check for paywall indicators
    paywall_indicators = ["Subscribe", "Purchase", "Sign in"]
    page_text = driver.page_source
    has_paywall = any(indicator in page_text for indicator in paywall_indicators)
    print(f"Paywall detected: {has_paywall}")
    
    driver.quit()
```

#### MDPI (Should always work - open access)
```python
# MDPI failures are unusual - check internet connection
def test_mdpi_access():
    test_url = "https://www.mdpi.com/1099-4300/24/1/130"
    # This should always work (open access)
```

### Network and Firewall Issues

**Problem**: Downloads fail due to network restrictions
```bash
❌ requests.exceptions.ConnectionError: Failed to establish a new connection
```

**Solutions**:
```bash
# 1. Check basic internet connectivity
curl -I https://arxiv.org

# 2. Test specific publisher access
curl -I https://journals.aps.org

# 3. Check proxy settings
export HTTP_PROXY=http://proxy.institution.edu:8080
export HTTPS_PROXY=http://proxy.institution.edu:8080

# 4. Configure Chrome with proxy
chrome_options.add_argument('--proxy-server=http://proxy.institution.edu:8080')
```

## 🧠 Knowledge Base Issues

### Embedding Model Problems

**Problem**: `OSError: Can't load tokenizer` or model download failures
```bash
❌ OSError: Can't load tokenizer for 'all-MiniLM-L6-v2'
```

**Solutions**:
```python
# 1. Check internet connection for model download
# 2. Try alternative model
config = PipelineConfig({
    'embedding_model': 'all-mpnet-base-v2'  # Alternative model
})

# 3. Manual model download
from sentence_transformers import SentenceTransformer
try:
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Model loading failed: {e}")
    
# 4. Clear transformers cache if corrupted
import shutil
from pathlib import Path
cache_dir = Path.home() / '.cache' / 'huggingface' / 'transformers'
if cache_dir.exists():
    shutil.rmtree(cache_dir)
    print("🧹 Cleared transformers cache - try again")
```

### Knowledge Base Corruption

**Problem**: `pickle.UnpicklingError` or corrupted knowledge base
```bash
❌ pickle.UnpicklingError: could not find MARK
```

**Solutions**:
```python
# 1. Delete corrupted cache file
import os
cache_file = "physics_knowledge_base.pkl"
if os.path.exists(cache_file):
    os.remove(cache_file)
    print("🗑️ Deleted corrupted knowledge base cache")

# 2. Rebuild knowledge base
from src.core import KnowledgeBase
kb = KnowledgeBase()
kb_stats = kb.build_from_directories(
    literature_folder=config.literature_folder,
    your_work_folder=config.your_work_folder,
    zotero_folder=config.zotero_sync_folder
)
kb.save_to_file(config.cache_file)
print(f"✅ Rebuilt knowledge base with {kb_stats['total_documents']} documents")
```

### Memory Issues with Large Libraries

**Problem**: `MemoryError` or system slowdown with large document collections
```bash
❌ MemoryError: Unable to allocate array
```

**Solutions**:
```python
# 1. Process in smaller batches
config = PipelineConfig({
    'chunk_size': 800,        # Smaller chunks
    'max_context_chunks': 5   # Fewer chunks in memory
})

# 2. Use more efficient embedding model
config = PipelineConfig({
    'embedding_model': 'all-MiniLM-L6-v2'  # Smaller model
})

# 3. Clear knowledge base and rebuild incrementally
kb = KnowledgeBase()
# Process one directory at a time
kb.build_from_directories(literature_folder=config.literature_folder)
kb.save_to_file("literature_only.pkl")

# Add more directories gradually
kb.add_documents_from_directory(config.your_work_folder, "your_work")
kb.save_to_file("expanded_kb.pkl")
```

## 💬 AI Assistant Issues

### Response Quality Problems

**Problem**: AI gives generic responses without using literature
```bash
❌ AI response doesn't reference sources or seems generic
```

**Solutions**:
```python
# 1. Check knowledge base has documents
kb = KnowledgeBase()
kb.load_from_file(config.cache_file)
stats = kb.get_statistics()
print(f"KB has {stats['total_documents']} documents")

# 2. Test search functionality
results = kb.search("quantum computing", top_k=5)
print(f"Search returned {len(results)} results")
for result in results[:3]:
    print(f"  - {result.chunk.file_name}: {result.similarity_score:.3f}")

# 3. Use more specific questions
response = assistant.ask(
    "What are the specific error thresholds reported for surface code "
    "quantum error correction in recent experimental papers?"
)

# 4. Increase context chunks
assistant = LiteratureAssistant(kb, api_key, {
    'max_context_chunks': 12  # More literature context
})
```

### API Rate Limiting

**Problem**: `RateLimitError` from Anthropic API
```bash
❌ anthropic.RateLimitError: Rate limit exceeded
```

**Solutions**:
```python
# 1. Add delays between requests
import time

responses = []
for question in questions:
    response = assistant.ask(question)
    responses.append(response)
    time.sleep(2)  # 2-second delay

# 2. Use lower temperature for more consistent responses
assistant = LiteratureAssistant(kb, api_key, {
    'default_temperature': 0.1  # More deterministic
})

# 3. Batch questions in conversation
# Instead of separate API calls, ask related questions together
combined_question = """
Please answer these related questions:
1. What are surface codes?
2. What are their error thresholds?
3. What recent experiments have been done?
"""
```

## 🔍 Performance Issues

### Slow Collection Processing

**Problem**: Collection sync takes extremely long
```bash
⏰ Collection processing taking 30+ minutes
```

**Diagnosis**:
```python
# Time different operations
import time

start = time.time()
preview = syncer.preview_collection_sync("Large Collection")
preview_time = time.time() - start
print(f"Preview took: {preview_time:.2f} seconds")

if preview['total_items'] > 100:
    print("⚠️ Large collection detected")
    print("💡 Recommendations:")
    print("  - Process in smaller batches")
    print("  - Use collection-specific sync")
    print("  - Enable headless mode")
```

**Solutions**:
```python
# 1. Use collection-specific sync (faster)
result = syncer.sync_collection_with_doi_downloads_and_integration(
    collection_name="Large Collection",
    max_doi_downloads=5,  # Smaller batches
    headless=True,        # Faster processing
    integration_mode="attach"
)

# 2. Process collections separately
large_collections = ["Collection A", "Collection B", "Collection C"]
for collection in large_collections:
    print(f"Processing {collection}...")
    result = syncer.sync_collection_with_doi_downloads_and_integration(
        collection_name=collection,
        max_doi_downloads=8,
        headless=True
    )
    time.sleep(30)  # Rest between collections
```

### High Memory Usage

**Problem**: System runs out of memory during processing
```bash
❌ System becomes unresponsive or crashes
```

**Solutions**:
```python
# 1. Monitor memory usage
import psutil
import os

def monitor_memory():
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    print(f"Memory usage: {memory_mb:.1f} MB")

# 2. Use smaller chunks and batch sizes
config = PipelineConfig({
    'chunk_size': 500,           # Smaller text chunks
    'max_context_chunks': 3,     # Fewer chunks in memory
    'max_doi_downloads_per_sync': 5  # Smaller download batches
})

# 3. Process and save incrementally
kb = KnowledgeBase()
for folder in [literature_folder, your_work_folder]:
    kb.add_documents_from_directory(folder)
    kb.save_to_file(f"kb_backup_{folder.name}.pkl")
    monitor_memory()
```

## 🧪 Testing and Validation

### Validate Your Setup

```python
#!/usr/bin/env python3
"""Comprehensive setup validation script."""

def validate_complete_setup():
    """Test all components of the pipeline."""
    
    print("🧪 COMPREHENSIVE SETUP VALIDATION")
    print("=" * 40)
    
    issues = []
    
    # Test 1: Dependencies
    try:
        import anthropic, pyzotero, sentence_transformers
        print("✅ Core dependencies: Installed")
    except ImportError as e:
        issues.append(f"Missing dependency: {e}")
    
    # Test 2: Optional dependencies
    try:
        import selenium
        print("✅ Enhanced features: Available")
    except ImportError:
        print("⚠️ Enhanced features: Selenium not available")
    
    # Test 3: Configuration
    try:
        from config import PipelineConfig
        config = PipelineConfig()
        config.validate_api_keys()
        config.validate_zotero_config()
        print("✅ Configuration: Valid")
    except Exception as e:
        issues.append(f"Configuration issue: {e}")
    
    # Test 4: API connections
    try:
        from src.downloaders import EnhancedZoteroLiteratureSyncer
        syncer = EnhancedZoteroLiteratureSyncer(config.get_zotero_config())
        connection = syncer.zotero_manager.test_connection()
        if connection['connected']:
            print(f"✅ Zotero: Connected ({connection['total_items']} items)")
        else:
            issues.append(f"Zotero connection: {connection['error']}")
    except Exception as e:
        issues.append(f"Zotero setup: {e}")
    
    # Test 5: AI Assistant
    try:
        from src.chat import LiteratureAssistant
        from src.core import KnowledgeBase
        
        kb = KnowledgeBase()
        assistant = LiteratureAssistant(kb, config.anthropic_api_key)
        response = assistant.ask("Test question")
        if response.content:
            print("✅ AI Assistant: Working")
        else:
            issues.append("AI Assistant: No response received")
    except Exception as e:
        issues.append(f"AI Assistant: {e}")
    
    # Summary
    if not issues:
        print("\n🎉 All tests passed! System ready for use.")
        return True
    else:
        print(f"\n❌ Found {len(issues)} issues:")
        for issue in issues:
            print(f"   • {issue}")
        return False

if __name__ == "__main__":
    validate_complete_setup()
```

### Test with Small Collection

```python
def test_with_small_collection():
    """Test complete workflow with a small collection."""
    
    print("🧪 SMALL COLLECTION TEST")
    print("=" * 30)
    
    # Find smallest collection
    syncer = EnhancedZoteroLiteratureSyncer(config.get_zotero_config())
    collections = syncer.zotero_manager.get_collections()
    
    small_collections = [c for c in collections if c['num_items'] <= 5]
    if not small_collections:
        print("❌ No small collections found for testing")
        return False
    
    test_collection = small_collections[0]
    print(f"Testing with: {test_collection['name']} ({test_collection['num_items']} items)")
    
    # Test preview
    preview = syncer.preview_collection_sync(test_collection['name'])
    print(f"Preview: {preview['items_with_dois_no_pdfs']} DOI candidates")
    
    # Test sync with minimal downloads
    result = syncer.sync_collection_with_doi_downloads_and_integration(
        collection_name=test_collection['name'],
        max_doi_downloads=2,  # Very conservative
        integration_mode="attach",
        headless=False  # Watch for issues
    )
    
    print(f"✅ Test complete: {result.pdfs_integrated} PDFs integrated")
    return True
```

## 🆘 Getting Additional Help

### Enable Debug Logging

```python
# Enable detailed logging for troubleshooting
import logging

# Set detailed logging
logging.getLogger('physics_pipeline').setLevel(logging.DEBUG)
logging.getLogger('pyzotero').setLevel(logging.DEBUG)
logging.getLogger('selenium').setLevel(logging.INFO)

# Add file handler for persistent logs
log_file = Path("debug.log")
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Add to all loggers
for logger_name in ['physics_pipeline', 'pyzotero', 'selenium']:
    logger = logging.getLogger(logger_name)
    logger.addHandler(file_handler)

print(f"📝 Debug logging enabled - check {log_file} for details")
```

### Common Error Patterns

| Error Type | Likely Cause | Quick Fix |
|------------|--------------|-----------|
| `ImportError` | Missing dependencies | `pip install -r requirements.txt` |
| `ConnectionError` | Network/proxy issues | Check internet, configure proxy |
| `AuthenticationError` | Invalid API keys | Verify keys at provider websites |
| `TimeoutException` | Browser automation timeout | Increase timeout, disable headless |
| `MemoryError` | Large documents/library | Reduce batch sizes, use smaller models |
| `FileNotFoundError` | Missing ChromeDriver | Install ChromeDriver for your system |

### When to Seek Help

If you encounter persistent issues after trying these solutions:

1. **Check the logs** in detail with debug logging enabled
2. **Test with minimal examples** (single paper, small collection)
3. **Verify your environment** matches the requirements
4. **Document the exact error** including full stack traces
5. **Note your system details** (OS, Python version, package versions)

For system-specific issues, include:
- Operating system and version
- Python version (`python --version`)
- Package versions (`pip list | grep -E "(anthropic|pyzotero|selenium)"`)
- Browser and ChromeDriver versions
- Any institutional network restrictions