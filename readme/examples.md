# Usage Examples and Tutorials

Comprehensive examples showing how to use the Physics Literature Synthesis Pipeline for various research workflows.

## 🚀 Quick Start Examples

### Basic Literature Sync

```python
from src.downloaders import EnhancedZoteroLiteratureSyncer
from config import PipelineConfig

# Initialize configuration
config = PipelineConfig()

# Create enhanced syncer
syncer = EnhancedZoteroLiteratureSyncer(
    zotero_config=config.get_zotero_config(),
    pdf_integration_enabled=True,
    default_integration_mode="attach"
)

# Sync a collection with automatic PDF downloads
result = syncer.sync_collection_with_doi_downloads_and_integration(
    collection_name="Quantum Computing",
    max_doi_downloads=10,
    integration_mode="attach"
)

print(f"✅ Successfully integrated {result.pdfs_integrated} PDFs")
print(f"📊 Success rate: {result.integration_success_rate:.1f}%")
```

### AI Research Assistant

```python
from src.chat import LiteratureAssistant
from src.core import KnowledgeBase

# Build knowledge base from your literature
kb = KnowledgeBase()
kb.build_from_directories(
    literature_folder=config.literature_folder,
    your_work_folder=config.your_work_folder,
    zotero_folder=config.zotero_sync_folder
)

# Create AI assistant
assistant = LiteratureAssistant(kb, config.anthropic_api_key)

# Ask research questions
response = assistant.ask(
    "What are the main challenges in implementing surface code "
    "quantum error correction in current quantum computers?"
)

print(response.content)
print(f"Based on {len(response.sources_used)} sources")
```

## 📚 Collection Management Examples

### Preview Before Sync

```python
# Always preview collections before processing
preview = syncer.preview_collection_sync("Machine Learning Physics")

print(f"📊 Collection Analysis:")
print(f"  Total items: {preview['total_items']}")
print(f"  Items with PDFs: {preview['items_with_pdfs']}")
print(f"  DOI download candidates: {preview['items_with_dois_no_pdfs']}")
print(f"  Items without DOIs: {preview['items_without_dois']}")

# Recommendations
for rec in preview['recommendations']:
    icon = "✅" if rec['type'] == 'success' else "⚠️" if rec['type'] == 'warning' else "ℹ️"
    print(f"{icon} {rec['message']}")
    print(f"   Action: {rec['action']}")
```

### Batch Collection Processing

```python
# Process multiple collections efficiently
physics_collections = [
    "Quantum Computing",
    "Condensed Matter Theory",
    "Statistical Mechanics",
    "Machine Learning Physics"
]

results = syncer.batch_sync_collections_with_integration(
    collection_names=physics_collections,
    max_doi_downloads_per_collection=8,
    integration_mode="attach"
)

# Analyze results
total_downloaded = 0
total_integrated = 0

for collection_name, result in results.items():
    if result:
        downloaded = result.zotero_sync_result.successful_doi_downloads
        integrated = result.pdfs_integrated
        total_downloaded += downloaded
        total_integrated += integrated
        
        print(f"📚 {collection_name}:")
        print(f"   Downloaded: {downloaded} PDFs")
        print(f"   Integrated: {integrated} PDFs")
        print(f"   Success rate: {result.integration_success_rate:.1f}%")

print(f"\n📊 Batch Summary:")
print(f"   Total downloaded: {total_downloaded} PDFs")
print(f"   Total integrated: {total_integrated} PDFs")
```

### Smart Collection Discovery

```python
# Find collections that need attention
opportunities = syncer.find_collections_needing_doi_downloads()

print("🎯 Collections with DOI download opportunities:")
for collection in opportunities[:5]:
    completion = collection['completion_percentage']
    candidates = collection['doi_download_candidates']
    
    print(f"📁 {collection['name']}")
    print(f"   Completion: {completion:.1f}%")
    print(f"   DOI candidates: {candidates}")
    
    # Recommend action based on size
    if candidates <= 10:
        print(f"   💡 Recommendation: Good for quick sync")
    elif candidates <= 20:
        print(f"   💡 Recommendation: Process in one batch")
    else:
        print(f"   💡 Recommendation: Process in smaller batches")
```

## 🤖 AI Research Assistant Examples

### Literature Review Generation

```python
# Generate comprehensive literature review
synthesis = assistant.synthesize_literature(
    topic="quantum error correction using surface codes",
    focus_areas=[
        "error threshold analysis",
        "experimental implementations", 
        "resource requirements",
        "recent improvements"
    ],
    max_chunks=20
)

print("📝 Literature Synthesis:")
print(synthesis.content)
print(f"\n📚 Sources consulted: {len(synthesis.sources_used)}")

# Save the synthesis
with open("reports/surface_codes_review.md", "w") as f:
    f.write(f"# Surface Codes Literature Review\n\n")
    f.write(synthesis.content)
    f.write(f"\n\n## Sources\n")
    for source in synthesis.sources_used:
        f.write(f"- {source}\n")
```

### Research Question Analysis

```python
# Analyze specific research questions
questions = [
    "What are the scaling advantages of topological qubits?",
    "How do measurement-induced phase transitions affect quantum computing?",
    "What progress has been made in quantum advantage demonstrations?",
    "How does quantum error correction overhead scale with system size?"
]

for i, question in enumerate(questions, 1):
    print(f"\n🔍 Question {i}: {question}")
    
    response = assistant.ask(question, max_context_chunks=10)
    
    # Extract key insights
    print(f"📋 Answer Summary:")
    print(response.content[:300] + "..." if len(response.content) > 300 else response.content)
    print(f"📚 Sources: {len(response.sources_used)}")
    
    # Save detailed analysis
    with open(f"reports/research_question_{i}.md", "w") as f:
        f.write(f"# {question}\n\n")
        f.write(response.content)
        f.write(f"\n\n## Sources Used\n")
        for source in response.sources_used:
            f.write(f"- {source}\n")
```

### Conversational Research Session

```python
# Extended research conversation
print("🗣️ Starting research conversation...")

# Context-building questions
context_questions = [
    "What are the main approaches to quantum error correction?",
    "How do surface codes compare to other QEC methods?",
    "What are the current experimental challenges?"
]

for question in context_questions:
    response = assistant.ask(question)
    print(f"\nQ: {question}")
    print(f"A: {response.content[:200]}...")

# Follow-up question that benefits from context
followup = assistant.ask(
    "Based on our discussion, which QEC approach shows the most promise "
    "for near-term quantum computers with limited connectivity?"
)

print(f"\n🎯 Synthesis Question:")
print(followup.content)

# Export the entire conversation
conversation_export = assistant.export_conversation_with_sources()
with open("reports/research_session.md", "w") as f:
    f.write(conversation_export)
```

## 🔧 Advanced Workflow Examples

### Custom Research Pipeline

```python
def complete_research_pipeline(topic, collections, max_papers_per_collection=15):
    """Complete research pipeline for a specific topic."""
    
    print(f"🚀 Starting research pipeline for: {topic}")
    
    # Step 1: Sync relevant collections
    total_new_papers = 0
    for collection in collections:
        print(f"\n📚 Processing collection: {collection}")
        
        result = syncer.sync_collection_with_doi_downloads_and_integration(
            collection_name=collection,
            max_doi_downloads=max_papers_per_collection,
            integration_mode="attach",
            headless=True
        )
        
        new_papers = result.pdfs_integrated
        total_new_papers += new_papers
        print(f"   ✅ Added {new_papers} new papers")
    
    # Step 2: Update knowledge base if new papers added
    if total_new_papers > 0:
        print(f"\n🧠 Updating knowledge base with {total_new_papers} new papers...")
        kb = KnowledgeBase()
        kb_stats = kb.build_from_directories(
            literature_folder=config.literature_folder,
            your_work_folder=config.your_work_folder,
            zotero_folder=config.zotero_sync_folder
        )
        print(f"   📊 Knowledge base now contains {kb_stats['total_documents']} documents")
        
        # Save updated knowledge base
        kb.save_to_file(config.cache_file)
    else:
        # Load existing knowledge base
        kb = KnowledgeBase()
        kb.load_from_file(config.cache_file)
    
    # Step 3: Generate research synthesis
    assistant = LiteratureAssistant(kb, config.anthropic_api_key)
    
    synthesis = assistant.synthesize_literature(
        topic=topic,
        focus_areas=[
            "current state of research",
            "key findings and results",
            "open questions and challenges",
            "future directions"
        ],
        max_chunks=25
    )
    
    # Step 4: Save comprehensive report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = config.reports_folder / f"{topic.replace(' ', '_')}_{timestamp}.md"
    
    with open(report_path, "w") as f:
        f.write(f"# Research Report: {topic}\n\n")
        f.write(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"## Collection Summary\n")
        f.write(f"- Collections processed: {', '.join(collections)}\n")
        f.write(f"- New papers added: {total_new_papers}\n")
        f.write(f"- Total documents in KB: {kb_stats.get('total_documents', 'N/A')}\n\n")
        f.write(f"## Literature Synthesis\n\n")
        f.write(synthesis.content)
        f.write(f"\n\n## Sources ({len(synthesis.sources_used)})\n\n")
        for i, source in enumerate(synthesis.sources_used, 1):
            f.write(f"{i}. {source}\n")
    
    print(f"\n📝 Research report saved to: {report_path}")
    return report_path

# Example usage
report = complete_research_pipeline(
    topic="quantum machine learning algorithms",
    collections=[
        "Quantum Computing",
        "Machine Learning Physics", 
        "Quantum Algorithms"
    ],
    max_papers_per_collection=12
)
```

### Automated Daily Research Update

```python
import schedule
import time
from datetime import datetime

def daily_research_update():
    """Automated daily research workflow."""
    
    print(f"🌅 Daily Research Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Priority collections for daily monitoring
    priority_collections = [
        "Current Projects",
        "Recent Discoveries",
        "Weekly Reading",
        "Conference Papers"
    ]
    
    daily_summary = {
        'collections_processed': 0,
        'papers_downloaded': 0,
        'papers_integrated': 0,
        'errors': []
    }
    
    for collection in priority_collections:
        try:
            # Conservative settings for daily automation
            result = syncer.sync_collection_with_doi_downloads_and_integration(
                collection_name=collection,
                max_doi_downloads=5,  # Small number for daily updates
                integration_mode="attach",
                headless=True
            )
            
            daily_summary['collections_processed'] += 1
            daily_summary['papers_downloaded'] += result.zotero_sync_result.successful_doi_downloads
            daily_summary['papers_integrated'] += result.pdfs_integrated
            
            if result.pdfs_integrated > 0:
                print(f"✅ {collection}: {result.pdfs_integrated} new papers")
            else:
                print(f"📚 {collection}: No new papers")
                
        except Exception as e:
            error_msg = f"Error processing {collection}: {str(e)}"
            daily_summary['errors'].append(error_msg)
            print(f"❌ {error_msg}")
    
    # Generate daily summary
    print(f"\n📊 Daily Summary:")
    print(f"   Collections processed: {daily_summary['collections_processed']}")
    print(f"   Papers downloaded: {daily_summary['papers_downloaded']}")
    print(f"   Papers integrated: {daily_summary['papers_integrated']}")
    
    if daily_summary['errors']:
        print(f"   Errors: {len(daily_summary['errors'])}")
    
    # Save daily log
    log_path = config.reports_folder / "daily_updates.log"
    with open(log_path, "a") as f:
        f.write(f"{datetime.now().isoformat()}: {daily_summary}\n")
    
    return daily_summary

# Schedule daily updates
schedule.every().day.at("09:00").do(daily_research_update)  # 9 AM daily
schedule.every().day.at("17:00").do(daily_research_update)  # 5 PM daily

# Run scheduler (in a separate script or service)
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

# For immediate execution
if __name__ == "__main__":
    daily_research_update()
```

### Research Collaboration Workflow

```python
def setup_collaboration_workspace(group_collections, shared_topics):
    """Set up shared research workspace for collaboration."""
    
    print("👥 Setting up collaboration workspace...")
    
    # Create shared knowledge base
    shared_kb = KnowledgeBase(
        embedding_model="all-mpnet-base-v2",  # Higher quality for shared use
        chunk_size=1200,                      # Larger chunks for better context
        chunk_overlap=300
    )
    
    # Process all group collections
    all_results = {}
    for collection in group_collections:
        print(f"📚 Processing shared collection: {collection}")
        
        result = syncer.sync_collection_with_doi_downloads_and_integration(
            collection_name=collection,
            max_doi_downloads=20,
            integration_mode="attach",
            headless=True
        )
        
        all_results[collection] = result
        print(f"   ✅ {result.pdfs_integrated} PDFs integrated")
    
    # Build comprehensive knowledge base
    kb_stats = shared_kb.build_from_directories(
        literature_folder=config.literature_folder,
        your_work_folder=config.your_work_folder,
        zotero_folder=config.zotero_sync_folder
    )
    
    # Save shared knowledge base
    shared_kb_path = config.reports_folder / "shared_knowledge_base.pkl"
    shared_kb.save_to_file(shared_kb_path)
    
    # Generate topic summaries for each research area
    assistant = LiteratureAssistant(shared_kb, config.anthropic_api_key)
    
    topic_summaries = {}
    for topic in shared_topics:
        print(f"📝 Generating summary for: {topic}")
        
        summary = assistant.synthesize_literature(
            topic=topic,
            focus_areas=[
                "key findings",
                "methodological approaches",
                "recent developments",
                "research gaps"
            ],
            max_chunks=30
        )
        
        topic_summaries[topic] = summary
        
        # Save individual topic summary
        topic_file = config.reports_folder / f"{topic.replace(' ', '_')}_summary.md"
        with open(topic_file, "w") as f:
            f.write(f"# {topic} - Research Summary\n\n")
            f.write(summary.content)
            f.write(f"\n\n## Sources ({len(summary.sources_used)})\n\n")
            for source in summary.sources_used:
                f.write(f"- {source}\n")
    
    # Create collaboration index
    index_path = config.reports_folder / "collaboration_index.md"
    with open(index_path, "w") as f:
        f.write("# Research Collaboration Workspace\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Collection Status\n\n")
        for collection, result in all_results.items():
            f.write(f"### {collection}\n")
            f.write(f"- Total items: {result.zotero_sync_result.total_items}\n")
            f.write(f"- PDFs integrated: {result.pdfs_integrated}\n")
            f.write(f"- Success rate: {result.integration_success_rate:.1f}%\n\n")
        
        f.write("## Knowledge Base Statistics\n\n")
        f.write(f"- Total documents: {kb_stats['total_documents']}\n")
        f.write(f"- Total chunks: {kb_stats['total_chunks']}\n")
        f.write(f"- Embedding model: {kb_stats['embedding_model']}\n\n")
        
        f.write("## Research Topic Summaries\n\n")
        for topic in shared_topics:
            topic_file = f"{topic.replace(' ', '_')}_summary.md"
            f.write(f"- [{topic}]({topic_file})\n")
    
    print(f"✅ Collaboration workspace ready!")
    print(f"📚 Knowledge base: {shared_kb_path}")
    print(f"📋 Index: {index_path}")
    
    return shared_kb_path, index_path

# Example usage
shared_kb, index = setup_collaboration_workspace(
    group_collections=[
        "Quantum Computing Research",
        "Shared Literature",
        "Current Projects",
        "Conference Papers 2024"
    ],
    shared_topics=[
        "quantum error correction",
        "quantum machine learning",
        "quantum algorithms",
        "quantum hardware"
    ]
)
```

## 🔍 Knowledge Base Examples

### Custom Knowledge Base Building

```python
from src.core import KnowledgeBase

# Create specialized knowledge base
specialized_kb = KnowledgeBase(
    embedding_model="all-mpnet-base-v2",  # High quality embeddings
    chunk_size=800,                       # Smaller chunks for precision
    chunk_overlap=150                     # Good context preservation
)

# Build from specific directories
kb_stats = specialized_kb.build_from_directories(
    literature_folder=Path("documents/quantum_computing"),
    your_work_folder=Path("documents/my_papers"),
    current_drafts_folder=Path("documents/current_work"),
    manual_references_folder=Path("documents/key_references")
)

print(f"📊 Specialized KB Statistics:")
for key, value in kb_stats.items():
    print(f"   {key}: {value}")

# Save for reuse
specialized_kb.save_to_file(Path("quantum_computing_kb.pkl"))
```

### Advanced Search Examples

```python
# Load knowledge base
kb = KnowledgeBase()
kb.load_from_file(config.cache_file)

# Semantic search examples
search_queries = [
    "surface code error thresholds experimental results",
    "quantum volume benchmarking methods",
    "variational quantum algorithms optimization",
    "quantum advantage demonstrations"
]

for query in search_queries:
    print(f"\n🔍 Searching: {query}")
    
    results = kb.search(query, top_k=5)
    
    for i, result in enumerate(results, 1):
        print(f"   {i}. {result.chunk.file_name}")
        print(f"      Similarity: {result.similarity_score:.3f}")
        print(f"      Preview: {result.chunk.text[:100]}...")

# Search with conversation context
assistant = LiteratureAssistant(kb, config.anthropic_api_key)

# Build context through questions
assistant.ask("What are the main types of quantum error correction codes?")
assistant.ask("How do surface codes work specifically?")

# Context-aware search
contextual_results = kb.search_with_context(
    query="experimental implementations",
    conversation_context=assistant.chat.get_context_for_search(),
    top_k=8
)

print(f"\n🎯 Context-aware search results:")
for result in contextual_results:
    print(f"   📄 {result.chunk.file_name} (similarity: {result.similarity_score:.3f})")
```

## 📊 Performance Monitoring Examples

### System Performance Analysis

```python
def analyze_system_performance():
    """Comprehensive system performance analysis."""
    
    print("📈 SYSTEM PERFORMANCE ANALYSIS")
    print("=" * 50)
    
    # Zotero capabilities
    capabilities = get_zotero_capabilities()
    print("\n🔧 Available Capabilities:")
    for name, info in capabilities['capabilities'].items():
        status = "✅" if info['available'] else "❌"
        print(f"   {status} {name}: {info['description']}")
    
    # DOI downloads summary
    doi_summary = syncer.get_doi_downloads_summary()
    print(f"\n📥 DOI Downloads:")
    print(f"   Enabled: {doi_summary['doi_downloads_enabled']}")
    print(f"   Total files: {doi_summary['total_files']}")
    print(f"   Storage used: {doi_summary['total_size_mb']:.1f} MB")
    
    # Integration summary
    integration_summary = syncer.get_integration_summary()
    print(f"\n🔧 PDF Integration:")
    print(f"   Enabled: {integration_summary['pdf_integration_enabled']}")
    print(f"   Default mode: {integration_summary['default_integration_mode']}")
    print(f"   Available modes: {', '.join(integration_summary['available_modes'])}")
    
    # Knowledge base statistics
    if config.cache_file.exists():
        kb = KnowledgeBase()
        if kb.load_from_file(config.cache_file):
            kb_stats = kb.get_statistics()
            print(f"\n🧠 Knowledge Base:")
            print(f"   Total documents: {kb_stats['total_documents']}")
            print(f"   Total chunks: {kb_stats['total_chunks']}")
            print(f"   Embedding model: {kb_stats['embedding_model']}")
            print(f"   Average chunk length: {kb_stats['avg_chunk_length']:.1f} words")
    
    return {
        'capabilities': capabilities,
        'doi_summary': doi_summary,
        'integration_summary': integration_summary,
        'kb_stats': kb_stats if 'kb_stats' in locals() else None
    }

# Run performance analysis
performance_data = analyze_system_performance()
```

### Quality Monitoring

```python
def monitor_sync_quality(collection_results):
    """Monitor and report on sync quality metrics."""
    
    print("📊 SYNC QUALITY MONITORING")
    print("=" * 40)
    
    total_attempts = 0
    total_successes = 0
    total_integrations = 0
    publisher_stats = {}
    
    for collection_name, result in collection_results.items():
        if not result:
            continue
            
        attempts = result.zotero_sync_result.doi_download_attempts
        successes = result.zotero_sync_result.successful_doi_downloads
        integrations = result.pdfs_integrated
        
        total_attempts += attempts
        total_successes += successes
        total_integrations += integrations
        
        success_rate = (successes / attempts * 100) if attempts > 0 else 0
        integration_rate = result.integration_success_rate
        
        print(f"\n📚 {collection_name}:")
        print(f"   DOI Downloads: {successes}/{attempts} ({success_rate:.1f}%)")
        print(f"   PDF Integration: {integrations} ({integration_rate:.1f}%)")
        
        # Quality assessment
        if integration_rate >= 95:
            print(f"   🎉 Excellent quality")
        elif integration_rate >= 80:
            print(f"   ✅ Good quality")
        elif integration_rate >= 60:
            print(f"   ⚠️  Fair quality - consider reviewing")
        else:
            print(f"   ❌ Poor quality - needs attention")
    
    # Overall statistics
    overall_download_rate = (total_successes / total_attempts * 100) if total_attempts > 0 else 0
    
    print(f"\n🎯 Overall Quality Metrics:")
    print(f"   DOI Download Success: {total_successes}/{total_attempts} ({overall_download_rate:.1f}%)")
    print(f"   Total PDFs Integrated: {total_integrations}")
    
    # Recommendations
    print(f"\n💡 Recommendations:")
    if overall_download_rate >= 85:
        print("   ✅ System performing well - continue current settings")
    elif overall_download_rate >= 70:
        print("   ⚠️  Consider adjusting publisher strategies or checking access")
    else:
        print("   ❌ Review configuration and check institutional access")
    
    return {
        'total_attempts': total_attempts,
        'total_successes': total_successes,
        'total_integrations': total_integrations,
        'overall_download_rate': overall_download_rate
    }
```

## 🛠️ Utility Examples

### Configuration Testing

```python
def test_complete_setup():
    """Test complete pipeline setup and configuration."""
    
    print("🧪 COMPLETE SETUP TEST")
    print("=" * 30)
    
    # Test 1: Configuration
    try:
        config = PipelineConfig()
        config.validate_api_keys()
        config.validate_zotero_config()
        print("✅ Configuration: Valid")
    except Exception as e:
        print(f"❌ Configuration: {e}")
        return False
    
    # Test 2: Zotero Connection
    try:
        syncer = EnhancedZoteroLiteratureSyncer(config.get_zotero_config())
        connection = syncer.zotero_manager.test_connection()
        if connection['connected']:
            print(f"✅ Zotero: Connected ({connection['total_items']} items)")
        else:
            print(f"❌ Zotero: {connection['error']}")
            return False
    except Exception as e:
        print(f"❌ Zotero: {e}")
        return False
    
    # Test 3: AI Assistant
    try:
        # Load or create minimal knowledge base
        kb = KnowledgeBase()
        if config.cache_file.exists():
            kb.load_from_file(config.cache_file)
        
        assistant = LiteratureAssistant(kb, config.anthropic_api_key)
        response = assistant.ask("What is quantum computing?")
        
        if response.content:
            print("✅ AI Assistant: Working")
        else:
            print("❌ AI Assistant: No response")
            return False
    except Exception as e:
        print(f"❌ AI Assistant: {e}")
        return False
    
    # Test 4: DOI Downloads (if enabled)
    if syncer.doi_downloads_enabled:
        try:
            # Test browser setup
            driver = syncer.zotero_manager.setup_selenium_driver()
            if driver:
                driver.quit()
                print("✅ DOI Downloads: Browser ready")
            else:
                print("⚠️  DOI Downloads: Browser setup issues")
        except Exception as e:
            print(f"⚠️  DOI Downloads: {e}")
    else:
        print("ℹ️  DOI Downloads: Disabled")
    
    print("\n🎉 Setup test complete!")
    return True

# Run complete test
if test_complete_setup():
    print("✅ System ready for use!")
else:
    print("❌ Please fix configuration issues before proceeding")
```

For more examples and advanced usage patterns, see the Jupyter notebooks in the `notebooks/` directory and check out the [troubleshooting guide](troubleshooting.md) for common issues and solutions.