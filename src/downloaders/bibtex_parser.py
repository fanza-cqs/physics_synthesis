#!/usr/bin/env python3
"""
BibTeX parser for the Physics Literature Synthesis Pipeline.

Handles parsing of Zotero .bib files and extraction of paper metadata.
Cleans LaTeX formatting and extracts arXiv IDs from various fields.
"""

import re
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import bibtexparser

from ..utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class PaperMetadata:
    """Container for paper metadata extracted from BibTeX."""
    title: str
    authors: List[str]
    abstract: str = ""
    year: Optional[str] = None
    journal: Optional[str] = None
    arxiv_id: Optional[str] = None
    doi: Optional[str] = None
    url: Optional[str] = None
    bib_key: str = ""
    entry_type: str = ""

class BibtexParser:
    """
    Parser for Zotero BibTeX files.
    
    Extracts paper metadata and cleans LaTeX formatting for better processing.
    """
    
    def __init__(self):
        """Initialize the BibTeX parser."""
        self.parser = bibtexparser.bparser.BibTexParser(common_strings=True)
        logger.info("BibTeX parser initialized")
    
    def parse_file(self, bib_file_path: Path) -> List[PaperMetadata]:
        """
        Parse a .bib file and extract paper metadata.
        
        Args:
            bib_file_path: Path to the .bib file
        
        Returns:
            List of PaperMetadata objects
        """
        logger.info(f"Parsing BibTeX file: {bib_file_path}")
        
        if not bib_file_path.exists():
            logger.error(f"BibTeX file does not exist: {bib_file_path}")
            return []
        
        try:
            with open(bib_file_path, 'r', encoding='utf-8') as bib_file:
                bib_database = bibtexparser.load(bib_file, self.parser)
            
            papers = []
            skipped_books = 0
            
            for entry in bib_database.entries:
                # Skip books (focus on articles/papers)
                if entry.get('ENTRYTYPE', '').lower() == 'book':
                    skipped_books += 1
                    continue
                
                paper = self._extract_paper_metadata(entry)
                if paper:
                    papers.append(paper)
                    logger.debug(f"Extracted metadata for: {paper.title[:50]}...")
            
            logger.info(f"Successfully parsed {len(papers)} papers from {bib_file_path}")
            if skipped_books > 0:
                logger.info(f"Skipped {skipped_books} book entries")
            
            return papers
            
        except Exception as e:
            logger.error(f"Error parsing BibTeX file {bib_file_path}: {e}")
            return []
    
    # LEGACY METHOD - for backward compatibility with your original code
    def parse_bib_file(self, bib_file_path: str) -> List[PaperMetadata]:
        """Legacy method name for backward compatibility."""
        return self.parse_file(Path(bib_file_path))
    
    def _extract_paper_metadata(self, entry: Dict[str, Any]) -> Optional[PaperMetadata]:
        """
        Extract paper metadata from a single BibTeX entry.
        
        Args:
            entry: BibTeX entry dictionary
        
        Returns:
            PaperMetadata object or None if extraction fails
        """
        try:
            # Get title (required field)
            title = entry.get('title', '').strip()
            if not title:
                logger.warning("Skipping entry with no title")
                return None
            
            # Clean title from LaTeX formatting
            title = self._clean_latex_text(title)
            
            # Get authors
            authors_str = entry.get('author', '')
            authors = self._parse_authors(authors_str)
            
            # Get abstract
            abstract = self._clean_latex_text(entry.get('abstract', ''))
            
            # Get other metadata fields
            year = entry.get('year', '').strip()
            journal = (entry.get('journal', '') or 
                      entry.get('booktitle', '') or 
                      entry.get('publisher', '')).strip()
            doi = entry.get('doi', '').strip()
            url = entry.get('url', '').strip()
            bib_key = entry.get('ID', '').strip()
            entry_type = entry.get('ENTRYTYPE', '').strip()
            
            # Extract arXiv ID from various possible fields
            arxiv_id = self._extract_arxiv_id(entry)
            
            return PaperMetadata(
                title=title,
                authors=authors,
                abstract=abstract,
                year=year,
                journal=journal,
                arxiv_id=arxiv_id,
                doi=doi,
                url=url,
                bib_key=bib_key,
                entry_type=entry_type
            )
            
        except Exception as e:
            logger.warning(f"Error processing BibTeX entry: {e}")
            return None
    
    def _clean_latex_text(self, text: str) -> str:
        """
        Clean LaTeX commands and formatting from text.
        
        Args:
            text: Text with potential LaTeX formatting
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Remove curly braces
        text = re.sub(r'[{}]', '', text)
        
        # Remove common LaTeX commands
        # \command{content} -> content
        text = re.sub(r'\\[a-zA-Z]+\*?\{([^}]*)\}', r'\1', text)
        
        # Remove standalone LaTeX commands
        text = re.sub(r'\\[a-zA-Z]+\*?', '', text)
        
        # Remove escaped characters
        text = re.sub(r'\\[^\w\s]', '', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _parse_authors(self, authors_str: str) -> List[str]:
        """
        Parse author string into list of individual authors.
        
        Args:
            authors_str: Raw author string from BibTeX
        
        Returns:
            List of cleaned author names
        """
        if not authors_str:
            return []
        
        authors = []
        
        # Split by 'and' keyword
        for author in authors_str.split(' and '):
            author = author.strip()
            if not author:
                continue
            
            # Clean LaTeX formatting from author name
            author = self._clean_latex_text(author)
            
            if author:
                authors.append(author)
        
        return authors
    
    def _extract_arxiv_id_from_uri(self, uri: str) -> Optional[str]:
        """
        Extract arXiv ID from any arXiv URI - handles both old and new formats.
        
        Args:
            uri: URI that may contain an arXiv ID
        
        Returns:
            Extracted arXiv ID or None
        """
        if not uri or ('arxiv.org' not in uri and 'arxiv:' not in uri.lower()):
            return None
        
        # Handle different URI formats
        if '/abs/' in uri:
            arxiv_part = uri.split('/abs/')[-1]
        elif '/pdf/' in uri:
            arxiv_part = uri.split('/pdf/')[-1]
        elif 'arxiv:' in uri.lower():
            arxiv_part = uri.lower().split('arxiv:')[-1]
        else:
            # Fallback to last part of URL
            arxiv_part = uri.split('/')[-1]
        
        if not arxiv_part or len(arxiv_part) <= 3:
            return None
        
        # Clean up version numbers and file extensions
        if 'v' in arxiv_part and arxiv_part.split('v')[-1].isdigit():
            arxiv_part = arxiv_part.split('v')[0]
        
        if arxiv_part.endswith('.pdf'):
            arxiv_part = arxiv_part[:-4]
        
        logger.debug(f"Extracted arXiv ID: {arxiv_part}")
        return arxiv_part
    
    def _extract_arxiv_id(self, entry: Dict[str, Any]) -> Optional[str]:
        """
        Extract arXiv ID from various BibTeX fields using robust methods.
        
        Args:
            entry: BibTeX entry dictionary
        
        Returns:
            arXiv ID string or None if not found
        """
        # Fields that commonly contain arXiv IDs
        fields_to_check = [
            'eprint',           # Direct arXiv ID field
            'archiveprefix',    # Sometimes contains arXiv info
            'url',              # arXiv URLs
            'note',             # Sometimes contains arXiv info
            'howpublished',     # Alternative field
            'journal'           # Sometimes arXiv is listed as journal
        ]
        
        for field in fields_to_check:
            value = entry.get(field, '').strip()
            if not value:
                continue
            
            # Check if this field contains arXiv information
            if 'arxiv' in value.lower():
                # Try unified extraction method first
                arxiv_id = self._extract_arxiv_id_from_uri(value)
                if arxiv_id:
                    logger.debug(f"Found arXiv ID '{arxiv_id}' in field '{field}'")
                    return arxiv_id
                
                # Fallback to regex patterns for edge cases
                arxiv_id = self._parse_arxiv_id_from_text(value)
                if arxiv_id:
                    logger.debug(f"Found arXiv ID '{arxiv_id}' in field '{field}' via regex")
                    return arxiv_id
        
        return None
    
    def _parse_arxiv_id_from_text(self, text: str) -> Optional[str]:
        """
        Parse arXiv ID from text using various patterns.
        
        Args:
            text: Text that may contain an arXiv ID
        
        Returns:
            Extracted arXiv ID or None
        """
        if not text:
            return None
        
        # Pattern 1: New format (e.g., 1234.5678, 2012.12345)
        new_format = re.search(r'(?:arxiv:)?(\d{4}\.\d{4,5}(?:v\d+)?)', text, re.IGNORECASE)
        if new_format:
            return new_format.group(1)
        
        # Pattern 2: Old format (e.g., cond-mat/0408697, hep-th/9901001)
        old_format = re.search(r'(?:arxiv:)?([a-z-]+/\d{7}(?:v\d+)?)', text, re.IGNORECASE)
        if old_format:
            return old_format.group(1)
        
        # Pattern 3: Extract from URL
        if 'arxiv.org' in text.lower():
            # Extract from various URL formats
            url_patterns = [
                r'/abs/([^/\s]+)',
                r'/pdf/([^/\s]+)',
                r'arxiv\.org/[^/]*/([^/\s]+)'
            ]
            
            for pattern in url_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    arxiv_part = match.group(1)
                    # Clean up version numbers and extensions - FIXED REGEX
                    arxiv_part = re.sub(r'\.pdf$', '', arxiv_part)
                    if 'v' in arxiv_part and arxiv_part.split('v')[-1].isdigit():
                        arxiv_part = arxiv_part.split('v')[0]
                    
                    # Validate format
                    if (re.match(r'\d{4}\.\d{4,5}$', arxiv_part) or 
                        re.match(r'[a-z-]+/\d{7}$', arxiv_part)):
                        return arxiv_part
        
        return None
    
    def get_parsing_summary(self, papers: List[PaperMetadata]) -> Dict[str, Any]:
        """
        Get summary statistics about parsed papers.
        
        Args:
            papers: List of parsed paper metadata
        
        Returns:
            Dictionary with parsing statistics
        """
        if not papers:
            return {}
        
        # Count papers with different metadata
        with_abstracts = sum(1 for p in papers if p.abstract.strip())
        with_arxiv_ids = sum(1 for p in papers if p.arxiv_id)
        with_dois = sum(1 for p in papers if p.doi)
        with_years = sum(1 for p in papers if p.year)
        
        # Entry type breakdown
        entry_types = {}
        for paper in papers:
            entry_type = paper.entry_type or 'unknown'
            entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
        
        # Author statistics
        total_authors = sum(len(p.authors) for p in papers)
        avg_authors = total_authors / len(papers) if papers else 0
        
        summary = {
            'total_papers': len(papers),
            'with_abstracts': with_abstracts,
            'with_arxiv_ids': with_arxiv_ids,
            'with_dois': with_dois,
            'with_years': with_years,
            'entry_types': entry_types,
            'total_authors': total_authors,
            'avg_authors_per_paper': round(avg_authors, 1),
            'arxiv_coverage': round(with_arxiv_ids / len(papers) * 100, 1) if papers else 0
        }
        
        return summary
    
    def filter_papers_with_arxiv(self, papers: List[PaperMetadata]) -> List[PaperMetadata]:
        """
        Filter papers that have arXiv IDs.
        
        Args:
            papers: List of paper metadata
        
        Returns:
            List of papers with arXiv IDs
        """
        arxiv_papers = [paper for paper in papers if paper.arxiv_id]
        logger.info(f"Filtered to {len(arxiv_papers)} papers with arXiv IDs")
        return arxiv_papers
    
    def save_parsing_report(self, 
                           papers: List[PaperMetadata], 
                           output_path: Path) -> None:
        """
        Save a detailed parsing report to a markdown file.
        
        Args:
            papers: List of parsed papers
            output_path: Path where to save the report
        """
        logger.info(f"Saving parsing report to {output_path}")
        
        summary = self.get_parsing_summary(papers)
        
        # Create markdown report
        lines = ["# BibTeX Parsing Report\n\n"]
        
        # Summary statistics
        lines.append("## Summary Statistics\n\n")
        lines.append(f"- Total papers parsed: {summary.get('total_papers', 0)}\n")
        lines.append(f"- Papers with abstracts: {summary.get('with_abstracts', 0)}\n")
        lines.append(f"- Papers with arXiv IDs: {summary.get('with_arxiv_ids', 0)}\n")
        lines.append(f"- Papers with DOIs: {summary.get('with_dois', 0)}\n")
        lines.append(f"- ArXiv coverage: {summary.get('arxiv_coverage', 0)}%\n")
        lines.append(f"- Average authors per paper: {summary.get('avg_authors_per_paper', 0)}\n\n")
        
        # Entry types
        entry_types = summary.get('entry_types', {})
        if entry_types:
            lines.append("## Entry Types\n\n")
            for entry_type, count in entry_types.items():
                lines.append(f"- {entry_type}: {count}\n")
            lines.append("\n")
        
        # Papers with arXiv IDs
        arxiv_papers = [p for p in papers if p.arxiv_id]
        if arxiv_papers:
            lines.append("## Papers with arXiv IDs\n\n")
            for paper in arxiv_papers:
                lines.append(f"- **{paper.title}** (arXiv:{paper.arxiv_id})\n")
                if paper.authors:
                    lines.append(f"  - Authors: {', '.join(paper.authors[:3])}")
                    if len(paper.authors) > 3:
                        lines.append(f" and {len(paper.authors) - 3} more")
                    lines.append("\n")
                lines.append("\n")
        
        # Papers without arXiv IDs
        non_arxiv_papers = [p for p in papers if not p.arxiv_id]
        if non_arxiv_papers:
            lines.append("## Papers without arXiv IDs\n\n")
            for paper in non_arxiv_papers:
                lines.append(f"- **{paper.title}**\n")
                if paper.journal:
                    lines.append(f"  - Journal: {paper.journal}\n")
                if paper.doi:
                    lines.append(f"  - DOI: {paper.doi}\n")
                lines.append("\n")
        
        # Write report
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(''.join(lines), encoding='utf-8')
        
        logger.info(f"Parsing report saved to {output_path}")