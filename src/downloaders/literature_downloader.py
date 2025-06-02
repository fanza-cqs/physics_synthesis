#!/usr/bin/env python3
"""
Literature downloader orchestrator for the Physics Literature Synthesis Pipeline.

Coordinates the entire download process from BibTeX parsing to arXiv downloading.
Provides comprehensive reporting and error handling.
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
    Main orchestrator for literature downloading.
    
    Handles the complete pipeline from BibTeX parsing to file downloads.
    """
    
    def __init__(self, 
                 output_directory: Path,
                 delay_between_downloads: float = 1.2,
                 arxiv_config: Dict[str, Any] = None):
        """
        Initialize the literature downloader.
        
        Args:
            output_directory: Where to save downloaded papers
            delay_between_downloads: Seconds between download requests
            arxiv_config: Configuration for arXiv searcher
        """
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
            high_confidence_threshold=arxiv_config.get('high_confidence_threshold', 0.9)
        )
        
        logger.info(f"Literature downloader initialized with output: {output_directory}")
    
    def download_from_bibtex(self, 
                            bib_file_path: Path,
                            generate_report: bool = True) -> Dict[str, List[PaperDownloadResult]]:
        """
        Download papers from a BibTeX file.
        
        Args:
            bib_file_path: Path to the .bib file
            generate_report: Whether to generate markdown report
        
        Returns:
            Dictionary with 'successful' and 'failed' download results
        """
        logger.info(f"Starting download process from {bib_file_path}")
        start_time = time.time()
        
        # Parse BibTeX file
        papers = self.bibtex_parser.parse_file(bib_file_path)
        if not papers:
            logger.error("No papers found in BibTeX file")
            return {'successful': [], 'failed': []}
        
        logger.info(f"Found {len(papers)} papers to process")
        
        # Process each paper
        successful_downloads = []
        failed_downloads = []
        
        for i, paper in enumerate(papers, 1):
            logger.info(f"Processing paper {i}/{len(papers)}: {paper.title[:50]}...")
            
            paper_start_time = time.time()
            result = self._process_single_paper(paper)
            result.processing_time = time.time() - paper_start_time
            
            if result.search_result.found and result.download_result:
                successful_downloads.append(result)
                logger.info(f"✓ Successfully downloaded: {result.search_result.arxiv_id}")
            else:
                failed_downloads.append(result)
                logger.warning(f"✗ Failed to download: {paper.title[:50]}...")
        
        total_time = time.time() - start_time
        
        # Generate results summary
        results = {
            'successful': successful_downloads,
            'failed': failed_downloads
        }
        
        # Generate report if requested
        if generate_report:
            self._generate_download_report(
                results, bib_file_path, total_time
            )
        
        # Print summary
        self._print_download_summary(results, total_time)
        
        return results
    
    def _process_single_paper(self, paper: PaperMetadata) -> PaperDownloadResult:
        """
        Process a single paper through search and download.
        
        Args:
            paper: Paper metadata from BibTeX
        
        Returns:
            PaperDownloadResult with complete processing result
        """
        # Search for paper on arXiv
        search_result = self.arxiv_searcher.search_paper(paper)
        
        result = PaperDownloadResult(
            paper_metadata=paper,
            search_result=search_result
        )
        
        # If found, attempt download
        if search_result.found and search_result.arxiv_id:
            try:
                download_result = self.arxiv_searcher.download_paper(
                    search_result.arxiv_id, 
                    self.output_directory
                )
                result.download_result = download_result
                
                # Log download success/failure
                if download_result.pdf_downloaded or download_result.tex_downloaded:
                    logger.debug(f"Download successful for {search_result.arxiv_id}")
                else:
                    logger.warning(f"Download failed for {search_result.arxiv_id}")
                    
            except Exception as e:
                logger.error(f"Download error for {search_result.arxiv_id}: {e}")
                result.download_result = DownloadResult(
                    error_message=f"Download exception: {e}"
                )
        
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
    
    def _generate_download_report(self, 
                                 results: Dict[str, List[PaperDownloadResult]],
                                 bib_file_path: Path,
                                 total_time: float) -> None:
        """
        Generate a detailed markdown report of download results.
        
        Args:
            results: Download results dictionary
            bib_file_path: Original BibTeX file path
            total_time: Total processing time
        """
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
        
        # Successful downloads
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
        
        # Failed downloads
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
        
        logger.info(f"Download report saved to {report_path}")
    
    def _print_download_summary(self, 
                               results: Dict[str, List[PaperDownloadResult]],
                               total_time: float) -> None:
        """
        Print a summary of download results to console.
        
        Args:
            results: Download results dictionary
            total_time: Total processing time
        """
        successful = results['successful']
        failed = results['failed']
        
        print("\n" + "="*80)
        print("📚 LITERATURE DOWNLOAD SUMMARY")
        print("="*80)
        
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
            print(f"\n✅ SUCCESSFUL DOWNLOADS (showing first 5):")
            for i, result in enumerate(successful[:5]):
                paper = result.paper_metadata
                search = result.search_result
                print(f"   {i+1}. {paper.title[:60]}...")
                print(f"      arXiv: {search.arxiv_id} (confidence: {search.confidence:.3f})")
        
        # Show some failed downloads
        if failed:
            print(f"\n❌ FAILED DOWNLOADS (showing first 3):")
            for i, result in enumerate(failed[:3]):
                paper = result.paper_metadata
                search = result.search_result
                print(f"   {i+1}. {paper.title[:60]}...")
                print(f"      Reason: {search.error_message}")
        
        # ArXiv API usage
        search_stats = self.arxiv_searcher.get_search_statistics()
        print(f"\n🌐 API USAGE:")
        print(f"   ArXiv API calls: {search_stats.get('api_calls', 0)}")
        print(f"   Google searches: {search_stats.get('google_searches', 0)}")
        
        print("="*80)
    
    def get_download_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about downloads.
        
        Returns:
            Dictionary with download statistics
        """
        return self.arxiv_searcher.get_search_statistics()
    
    def list_downloaded_files(self) -> List[Dict[str, Any]]:
        """
        List all downloaded files in the output directory.
        
        Returns:
            List of file information dictionaries
        """
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