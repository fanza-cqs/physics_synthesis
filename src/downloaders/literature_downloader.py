#!/usr/bin/env python3
"""
Enhanced Literature downloader with comprehensive debugging output.

This version provides detailed console output to help troubleshoot download failures.
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from .bibtex_parser import BibtexParser, PaperMetadata
from .arxiv_searcher import ArxivSearcher, ArxivSearchResult, DownloadResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class PaperDownloadResult:
    """Complete result for downloading a single paper."""
    paper_metadata: PaperMetadata
    search_result: ArxivSearchResult
    download_result: Optional[DownloadResult] = None
    processing_time: float = 0.0

class LiteratureDownloader:
    """
    Enhanced literature downloader with detailed debugging output.
    """
    
    def __init__(self, 
                 output_directory: Path,
                 delay_between_downloads: float = 1.2,
                 arxiv_config: Dict[str, Any] = None):
        """Initialize the literature downloader."""
        self.output_directory = Path(output_directory)
        self.output_directory.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.bibtex_parser = BibtexParser()
        
        # Configure arXiv searcher
        arxiv_config = arxiv_config or {}
        self.arxiv_searcher = ArxivSearcher(
            delay_between_requests=delay_between_downloads,
            title_similarity_threshold=arxiv_config.get('title_threshold', 0.6),
            abstract_similarity_threshold=arxiv_config.get('abstract_threshold', 0.5),
            high_confidence_threshold=arxiv_config.get('high_confidence_threshold', 0.9),
            google_api_key=arxiv_config.get('google_api_key'),
            google_search_engine_id=arxiv_config.get('google_search_engine_id')
        )
        
        print(f"📁 Literature downloader initialized")
        print(f"   Output directory: {output_directory}")
        print(f"   Delay between downloads: {delay_between_downloads}s")
        print(f"   ArXiv config: {arxiv_config}")
        
        logger.info(f"Literature downloader initialized with output: {output_directory}")
    
    def download_from_bibtex(self, 
                            bib_file_path: Path,
                            generate_report: bool = True,
                            debug_mode: bool = True) -> Dict[str, List[PaperDownloadResult]]:
        """Download papers from a BibTeX file with enhanced debugging."""
        
        print("\n" + "="*100)
        print("🚀 STARTING LITERATURE DOWNLOAD PROCESS")
        print("="*100)
        print(f"📖 BibTeX file: {bib_file_path}")
        print(f"📁 Output directory: {self.output_directory}")
        print(f"📊 Generate report: {generate_report}")
        print(f"🐛 Debug mode: {debug_mode}")
        print("="*100)
        
        logger.info(f"Starting download process from {bib_file_path}")
        start_time = time.time()
        
        # Parse BibTeX file
        print(f"\n📖 PARSING BIBTEX FILE...")
        papers = self.bibtex_parser.parse_file(bib_file_path)
        if not papers:
            print(f"❌ ERROR: No papers found in BibTeX file")
            logger.error("No papers found in BibTeX file")
            return {'successful': [], 'failed': []}
        
        print(f"✅ Found {len(papers)} papers to process")
        
        # Show paper summary
        if debug_mode:
            print(f"\n📋 PAPER SUMMARY:")
            for i, paper in enumerate(papers, 1):
                print(f"   {i:2d}. {paper.title[:70]}...")
                if paper.arxiv_id:
                    print(f"       📋 arXiv ID: {paper.arxiv_id}")
                if paper.abstract:
                    print(f"       📝 Abstract: {len(paper.abstract)} chars")
                if paper.authors:
                    print(f"       👥 Authors: {', '.join(paper.authors[:2])}" + 
                          (f" and {len(paper.authors)-2} more" if len(paper.authors) > 2 else ""))
                print()
        
        # Process each paper
        successful_downloads = []
        failed_downloads = []
        
        print(f"\n🔄 PROCESSING PAPERS...")
        print("="*100)
        
        for i, paper in enumerate(papers, 1):
            print(f"\n📄 PAPER {i}/{len(papers)}")
            print(f"📝 Title: {paper.title}")
            print(f"⏱️  Starting at: {time.strftime('%H:%M:%S')}")
            
            paper_start_time = time.time()
            result = self._process_single_paper(paper, debug_mode)
            result.processing_time = time.time() - paper_start_time
            
            if result.search_result.found and result.download_result:
                successful_downloads.append(result)
                print(f"✅ SUCCESS: Downloaded {result.search_result.arxiv_id} in {result.processing_time:.1f}s")
                if result.download_result.pdf_downloaded:
                    print(f"   📄 PDF: {result.download_result.pdf_path}")
                if result.download_result.tex_downloaded:
                    print(f"   📝 TEX: {result.download_result.tex_path}")
            else:
                failed_downloads.append(result)
                print(f"❌ FAILED: {result.search_result.error_message}")
                print(f"   🔍 Search method: {result.search_result.search_method}")
                print(f"   ⏱️  Time spent: {result.processing_time:.1f}s")
            
            # Progress indicator
            progress = i / len(papers) * 100
            print(f"📊 Progress: {progress:.1f}% ({i}/{len(papers)})")
            print("-" * 50)
        
        total_time = time.time() - start_time
        
        # Generate results summary
        results = {
            'successful': successful_downloads,
            'failed': failed_downloads
        }
        
        # Generate report if requested
        if generate_report:
            print(f"\n📝 GENERATING DOWNLOAD REPORT...")
            self._generate_download_report(
                results, bib_file_path, total_time
            )
        
        # Print summary
        self._print_download_summary(results, total_time)
        
        return results
    
    def _process_single_paper(self, paper: PaperMetadata, debug_mode: bool = True) -> PaperDownloadResult:
        """Process a single paper through search and download with detailed logging."""
        
        if debug_mode:
            print(f"🔍 Searching for paper...")
            if paper.authors:
                print(f"   👥 Authors: {', '.join(paper.authors[:3])}" + 
                      (f" and {len(paper.authors)-3} more" if len(paper.authors) > 3 else ""))
            if paper.year:
                print(f"   📅 Year: {paper.year}")
            if paper.journal:
                print(f"   📖 Journal: {paper.journal}")
        
        # Search for paper on arXiv
        search_result = self.arxiv_searcher.search_paper(paper)
        
        result = PaperDownloadResult(
            paper_metadata=paper,
            search_result=search_result
        )
        
        # If found, attempt download
        if search_result.found and search_result.arxiv_id:
            if debug_mode:
                print(f"📥 DOWNLOADING: {search_result.arxiv_id}")
                print(f"   📄 Title on arXiv: {search_result.arxiv_title}")
                print(f"   🎯 Confidence: {search_result.confidence:.3f}")
                print(f"   🔍 Method: {search_result.search_method}")
            
            try:
                download_result = self.arxiv_searcher.download_paper(
                    search_result.arxiv_id, 
                    self.output_directory
                )
                result.download_result = download_result
                
                if debug_mode:
                    if download_result.pdf_downloaded or download_result.tex_downloaded:
                        print(f"   ✅ Download completed!")
                        if download_result.pdf_downloaded:
                            print(f"      📄 PDF: Downloaded")
                        if download_result.tex_downloaded:
                            print(f"      📝 TEX: Downloaded")
                        if download_result.error_message:
                            print(f"      ⚠️  Warning: {download_result.error_message}")
                    else:
                        print(f"   ❌ Download failed: {download_result.error_message}")
                        
            except Exception as e:
                if debug_mode:
                    print(f"   💥 Download exception: {e}")
                logger.error(f"Download error for {search_result.arxiv_id}: {e}")
                result.download_result = DownloadResult(
                    error_message=f"Download exception: {e}"
                )
        else:
            if debug_mode:
                print(f"❌ SEARCH FAILED")
                print(f"   🔍 Method attempted: {search_result.search_method}")
                print(f"   💬 Error: {search_result.error_message}")
        
        return result
    
    def download_single_paper(self, 
                             paper_title: str,
                             arxiv_id: Optional[str] = None,
                             authors: List[str] = None,
                             abstract: str = "") -> PaperDownloadResult:
        """
        Download a single paper by metadata.
        
        Args:
            paper_title: Title of the paper
            arxiv_id: Optional arXiv ID if known
            authors: Optional list of authors
            abstract: Optional abstract text
        
        Returns:
            PaperDownloadResult
        """
        # Create paper metadata
        paper = PaperMetadata(
            title=paper_title,
            authors=authors or [],
            abstract=abstract,
            arxiv_id=arxiv_id
        )
        
        logger.info(f"Downloading single paper: {paper_title}")
        return self._process_single_paper(paper)
    
    def test_single_paper(self, paper_title: str, debug_mode: bool = True) -> PaperDownloadResult:
        """Test downloading a single paper by title with full debugging."""
        
        print(f"\n🧪 TESTING SINGLE PAPER DOWNLOAD")
        print("="*80)
        print(f"📝 Title: {paper_title}")
        
        # Create paper metadata
        paper = PaperMetadata(
            title=paper_title,
            authors=[],
            abstract=""
        )
        
        return self._process_single_paper(paper, debug_mode)
    
    def debug_search_methods(self, paper_title: str):
        """Debug all search methods for a specific paper."""
        
        print(f"\n🔬 DEBUGGING ALL SEARCH METHODS")
        print("="*80)
        print(f"📝 Title: {paper_title}")
        
        paper = PaperMetadata(title=paper_title, authors=[], abstract="")
        
        # Test each search method individually
        searcher = self.arxiv_searcher
        
        print(f"\n1️⃣  TESTING TITLE SEARCH...")
        title_result = searcher._search_by_title(paper)
        print(f"   Result: {'✅ Found' if title_result.found else '❌ Not found'}")
        if title_result.found:
            print(f"   arXiv ID: {title_result.arxiv_id}")
            print(f"   Confidence: {title_result.confidence:.3f}")
        else:
            print(f"   Error: {title_result.error_message}")
        
        print(f"\n2️⃣  TESTING GOOGLE API SEARCH...")
        if searcher.google_api_key and searcher.google_search_engine_id:
            google_result = searcher._google_search_fallback(paper)
            print(f"   Result: {'✅ Found' if google_result.found else '❌ Not found'}")
            if google_result.found:
                print(f"   arXiv ID: {google_result.arxiv_id}")
                print(f"   Confidence: {google_result.confidence:.3f}")
            else:
                print(f"   Error: {google_result.error_message}")
        else:
            print(f"   ⏭️  Skipped (Google API not configured)")
        
        print(f"\n3️⃣  TESTING BASIC GOOGLE SEARCH...")
        try:
            from googlesearch import search as google_search
            if google_search:
                basic_google_result = searcher._basic_google_search(paper)
                print(f"   Result: {'✅ Found' if basic_google_result.found else '❌ Not found'}")
                if basic_google_result.found:
                    print(f"   arXiv ID: {basic_google_result.arxiv_id}")
                    print(f"   Confidence: {basic_google_result.confidence:.3f}")
                else:
                    print(f"   Error: {basic_google_result.error_message}")
            else:
                print(f"   ⏭️  Skipped (googlesearch-python not available)")
        except ImportError:
            print(f"   ⏭️  Skipped (googlesearch-python not installed)")
    
    def check_arxiv_directly(self, arxiv_id: str):
        """Check if a specific arXiv ID exists and get its info."""
        
        print(f"\n🔍 CHECKING ARXIV ID DIRECTLY")
        print("="*50)
        print(f"📋 arXiv ID: {arxiv_id}")
        
        try:
            result = self.arxiv_searcher._get_paper_info_by_id(arxiv_id)
            if result:
                arxiv_id_found, title, abstract = result
                print(f"✅ FOUND ON ARXIV!")
                print(f"   📄 Title: {title}")
                print(f"   📝 Abstract: {abstract[:200]}...")
                return True
            else:
                print(f"❌ NOT FOUND ON ARXIV")
                return False
        except Exception as e:
            print(f"💥 ERROR: {e}")
            return False
    
    def analyze_failed_paper(self, paper_title: str):
        """Comprehensive analysis of why a paper failed to download."""
        
        print(f"\n🔬 COMPREHENSIVE FAILURE ANALYSIS")
        print("="*80)
        print(f"📝 Paper: {paper_title}")
        
        # Step 1: Test if we can find it manually on Google
        print(f"\n1️⃣  MANUAL GOOGLE SEARCH TEST")
        print(f"   Try searching: '{paper_title} arxiv'")
        print(f"   Expected first result should be arxiv.org link")
        
        # Step 2: Check title cleaning
        paper = PaperMetadata(title=paper_title, authors=[], abstract="")
        clean_title = self.arxiv_searcher._clean_title_for_search(paper_title)
        print(f"\n2️⃣  TITLE CLEANING ANALYSIS")
        print(f"   Original: {paper_title}")
        print(f"   Cleaned:  {clean_title}")
        print(f"   Length after cleaning: {len(clean_title)} chars")
        
        # Step 3: Test arXiv API search
        print(f"\n3️⃣  ARXIV API SEARCH TEST")
        query = f'ti:"{clean_title}"'
        print(f"   Query: {query}")
        try:
            results = self.arxiv_searcher._execute_arxiv_search(query, max_results=5)
            print(f"   Results: {len(results)} papers found")
            for i, (aid, atitle, aabstract) in enumerate(results):
                print(f"      {i+1}. {aid}: {atitle[:80]}...")
        except Exception as e:
            print(f"   Error: {e}")
        
        # Step 4: Run full search process
        print(f"\n4️⃣  FULL SEARCH PROCESS")
        self.debug_search_methods(paper_title)
        
        print(f"\n💡 RECOMMENDATIONS:")
        print(f"   1. Check if paper title has special characters affecting search")
        print(f"   2. Try searching with a shorter version of the title")
        print(f"   3. Check if the paper is actually on arXiv")
        print(f"   4. Consider adding abstract to improve search accuracy")
    
    def _generate_download_report(self, 
                                 results: Dict[str, List[PaperDownloadResult]],
                                 bib_file_path: Path,
                                 total_time: float) -> None:
        """Generate a detailed markdown report of download results."""
        successful = results['successful']
        failed = results['failed']
        
        # Create report content
        lines = ["# Literature Download Report\n\n"]
        
        # Summary section
        lines.append("## Summary\n\n")
        lines.append(f"- **BibTeX file**: {bib_file_path.name}\n")
        lines.append(f"- **Total papers**: {len(successful) + len(failed)}\n")
        lines.append(f"- **Successfully downloaded**: {len(successful)}\n")
        lines.append(f"- **Failed downloads**: {len(failed)}\n")
        lines.append(f"- **Success rate**: {len(successful) / (len(successful) + len(failed)) * 100:.1f}%\n")
        lines.append(f"- **Total processing time**: {total_time:.1f} seconds\n\n")
        
        # Search method breakdown
        search_methods = {}
        for result in successful:
            method = result.search_result.search_method
            search_methods[method] = search_methods.get(method, 0) + 1
        
        if search_methods:
            lines.append("## Search Methods Used\n\n")
            for method, count in search_methods.items():
                lines.append(f"- **{method}**: {count} papers\n")
            lines.append("\n")
        
        # Download statistics
        pdf_downloads = sum(1 for r in successful if r.download_result and r.download_result.pdf_downloaded)
        tex_downloads = sum(1 for r in successful if r.download_result and r.download_result.tex_downloaded)
        
        lines.append("## Download Statistics\n\n")
        lines.append(f"- **PDF files downloaded**: {pdf_downloads}\n")
        lines.append(f"- **TEX files downloaded**: {tex_downloads}\n\n")
        
        # Add detailed successful downloads section
        if successful:
            lines.append("## Successfully Downloaded Papers\n\n")
            for result in successful:
                paper = result.paper_metadata
                search = result.search_result
                download = result.download_result
                
                lines.append(f"### {paper.title}\n\n")
                lines.append(f"- **arXiv ID**: {search.arxiv_id}\n")
                lines.append(f"- **Search method**: {search.search_method}\n")
                lines.append(f"- **Confidence**: {search.confidence:.3f}\n")
                
                if download:
                    lines.append(f"- **PDF**: {'✓' if download.pdf_downloaded else '✗'}\n")
                    lines.append(f"- **TEX**: {'✓' if download.tex_downloaded else '✗'}\n")
                
                if paper.authors:
                    authors_str = ', '.join(paper.authors[:3])
                    if len(paper.authors) > 3:
                        authors_str += f" and {len(paper.authors) - 3} more"
                    lines.append(f"- **Authors**: {authors_str}\n")
                
                lines.append(f"- **Processing time**: {result.processing_time:.1f}s\n\n")
        
        # Add detailed failed downloads section
        if failed:
            lines.append("## Failed Downloads\n\n")
            for result in failed:
                paper = result.paper_metadata
                search = result.search_result
                
                lines.append(f"### {paper.title}\n\n")
                lines.append(f"- **Error**: {search.error_message or 'Unknown error'}\n")
                lines.append(f"- **Search method attempted**: {search.search_method}\n")
                
                if paper.authors:
                    authors_str = ', '.join(paper.authors[:2])
                    if len(paper.authors) > 2:
                        authors_str += f" and {len(paper.authors) - 2} more"
                    lines.append(f"- **Authors**: {authors_str}\n")
                
                if paper.journal:
                    lines.append(f"- **Journal**: {paper.journal}\n")
                
                lines.append("\n")
        
        # ArXiv searcher statistics
        search_stats = self.arxiv_searcher.get_search_statistics()
        lines.append("## Search Statistics\n\n")
        lines.append(f"- **ArXiv API calls**: {search_stats.get('api_calls', 0)}\n")
        lines.append(f"- **Google searches**: {search_stats.get('google_searches', 0)}\n")
        lines.append(f"- **Successful matches**: {search_stats.get('successful_matches', 0)}\n")
        lines.append(f"- **Failed matches**: {search_stats.get('failed_matches', 0)}\n\n")
        
        # Save report
        report_path = self.output_directory / 'download_report.md'
        report_path.write_text(''.join(lines), encoding='utf-8')
        
        print(f"📝 Download report saved to {report_path}")
        logger.info(f"Download report saved to {report_path}")
    
    def _print_download_summary(self, 
                               results: Dict[str, List[PaperDownloadResult]],
                               total_time: float) -> None:
        """Print a summary of download results to console."""
        successful = results['successful']
        failed = results['failed']
        
        print("\n" + "="*100)
        print("📚 LITERATURE DOWNLOAD SUMMARY")
        print("="*100)
        
        # Overall statistics
        total_papers = len(successful) + len(failed)
        success_rate = len(successful) / total_papers * 100 if total_papers > 0 else 0
        
        print(f"\n📊 OVERALL STATISTICS:")
        print(f"   Total papers processed: {total_papers}")
        print(f"   Successfully downloaded: {len(successful)}")
        print(f"   Failed downloads: {len(failed)}")
        print(f"   Success rate: {success_rate:.1f}%")
        print(f"   Total time: {total_time:.1f} seconds")
        print(f"   Average time per paper: {total_time/total_papers:.1f} seconds")
        
        # Download type breakdown
        if successful:
            pdf_count = sum(1 for r in successful if r.download_result and r.download_result.pdf_downloaded)
            tex_count = sum(1 for r in successful if r.download_result and r.download_result.tex_downloaded)
            
            print(f"\n📄 FILE DOWNLOADS:")
            print(f"   PDF files: {pdf_count}")
            print(f"   TEX files: {tex_count}")
        
        # Search method breakdown
        search_methods = {}
        for result in successful:
            method = result.search_result.search_method
            search_methods[method] = search_methods.get(method, 0) + 1
        
        if search_methods:
            print(f"\n🔍 SEARCH METHODS:")
            for method, count in search_methods.items():
                print(f"   {method}: {count} papers")
        
        # Show some successful downloads
        if successful:
            print(f"\n✅ SUCCESSFUL DOWNLOADS (showing first 3):")
            for i, result in enumerate(successful[:3]):
                paper = result.paper_metadata
                search = result.search_result
                print(f"   {i+1}. {paper.title[:60]}...")
                print(f"      arXiv: {search.arxiv_id} (confidence: {search.confidence:.3f})")
        
        # Show some failed downloads with details
        if failed:
            print(f"\n❌ FAILED DOWNLOADS (showing first 3):")
            for i, result in enumerate(failed[:3]):
                paper = result.paper_metadata
                search = result.search_result
                print(f"   {i+1}. {paper.title[:60]}...")
                print(f"      Reason: {search.error_message}")
                print(f"      Method tried: {search.search_method}")
        
        # ArXiv API usage
        search_stats = self.arxiv_searcher.get_search_statistics()
        print(f"\n🌐 API USAGE:")
        print(f"   ArXiv API calls: {search_stats.get('api_calls', 0)}")
        print(f"   Google searches: {search_stats.get('google_searches', 0)}")
        
        if failed:
            print(f"\n💡 DEBUGGING SUGGESTIONS:")
            print(f"   To debug a specific failed paper, use:")
            print(f"   downloader.analyze_failed_paper('Paper Title Here')")
        
        print("="*100)
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """Get statistics about downloads."""
        return self.arxiv_searcher.get_search_statistics()
    
    def list_downloaded_files(self) -> List[Dict[str, Any]]:
        """List all downloaded files in the output directory."""
        files = []
        
        for file_path in self.output_directory.iterdir():
            if file_path.is_file() and file_path.suffix in {'.pdf', '.tex'}:
                files.append({
                    'name': file_path.name,
                    'path': str(file_path),
                    'type': file_path.suffix[1:].upper(),
                    'size_mb': file_path.stat().st_size / (1024 * 1024)
                })
        
        return sorted(files, key=lambda x: x['name'])