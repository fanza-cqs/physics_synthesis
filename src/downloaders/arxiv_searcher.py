#!/usr/bin/env python3
"""
ArXiv searcher for the Physics Literature Synthesis Pipeline.

Handles searching and downloading papers from arXiv using multiple strategies:
1. Direct API search by title
2. Abstract-based search fallback
3. Google search fallback for difficult cases
"""

import os
import re
import time
import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

try:
    from googlesearch import search as google_search
except ImportError:
    google_search = None

from .bibtex_parser import PaperMetadata
from ..utils.logging_config import get_logger
from ..utils.file_utils import clean_filename, extract_tar_archive

logger = get_logger(__name__)

@dataclass
class ArxivSearchResult:
    """Result of an arXiv search operation."""
    found: bool
    arxiv_id: Optional[str] = None
    arxiv_title: Optional[str] = None
    confidence: float = 0.0
    search_method: str = ""
    error_message: Optional[str] = None

@dataclass
class DownloadResult:
    """Result of a download operation."""
    pdf_downloaded: bool = False
    tex_downloaded: bool = False
    pdf_path: Optional[str] = None
    tex_path: Optional[str] = None
    error_message: Optional[str] = None

class ArxivSearcher:
    """
    Search and download papers from arXiv.
    
    Uses multiple search strategies with validation to maximize success rate.
    """
    
    def __init__(self, 
                 delay_between_requests: float = 1.0,
                 title_similarity_threshold: float = 0.6,
                 abstract_similarity_threshold: float = 0.5,
                 high_confidence_threshold: float = 0.9,
                 google_api_key: Optional[str] = None,
                 google_search_engine_id: Optional[str] = None):
        """
        Initialize the arXiv searcher.
        
        Args:
            delay_between_requests: Seconds to wait between API calls
            title_similarity_threshold: Minimum title similarity for matches
            abstract_similarity_threshold: Minimum abstract similarity
            high_confidence_threshold: Threshold for high-confidence matches
            google_api_key: Google Custom Search API key
            google_search_engine_id: Google Custom Search Engine ID
        """
        self.api_base_url = "http://export.arxiv.org/api/query"
        self.delay = delay_between_requests
        self.title_threshold = title_similarity_threshold
        self.abstract_threshold = abstract_similarity_threshold
        self.high_confidence_threshold = high_confidence_threshold
        
        # Google Custom Search API credentials
        self.google_api_key = google_api_key or os.getenv('GOOGLE_API_KEY')
        self.google_search_engine_id = google_search_engine_id or os.getenv('GOOGLE_SEARCH_ENGINE_ID')

        if not self.google_api_key or not self.google_search_engine_id:
            logger.warning("Google API credentials not provided. Google fallback search will be disabled.")
            logger.warning("Set GOOGLE_API_KEY and GOOGLE_SEARCH_ENGINE_ID environment variables to enable.")
    

        # Statistics tracking
        self.search_stats = {
            'api_calls': 0,
            'google_searches': 0,
            'successful_matches': 0,
            'failed_matches': 0
        }
        
        logger.info("ArXiv searcher initialized")
        
        if not google_search:
            logger.warning("Google search not available (install googlesearch-python)")
    
    def search_paper(self, paper: PaperMetadata) -> ArxivSearchResult:
        """
        Search for a paper on arXiv using multiple strategies.
        
        Args:
            paper: Paper metadata from BibTeX
        
        Returns:
            ArxivSearchResult with search outcome
        """
        logger.info(f"Searching for paper: {paper.title[:50]}...")
        
        # Strategy 1: If we already have an arXiv ID, validate it
        if paper.arxiv_id:
            result = self._validate_existing_arxiv_id(paper)
            if result.found:
                print(f"✅ Validated existing arXiv ID: {result.arxiv_id}")
                return result
            else:
                print(f"❌ Failed to validate existing arXiv ID: {result.error_message}")
        
        
        # Strategy 2: Search by title using arXiv API
        result = self._search_by_title(paper)
        if result.found:
            print(f"✅ Found via title search: {result.arxiv_id} (confidence: {result.confidence:.3f})")
            return result
        else:
            print(f"❌ Title search failed: {result.error_message}")
        
        
        # Strategy 3: Search by abstract content if available
        if paper.abstract and len(paper.abstract.strip()) > 20:
            print(f"📝 Strategy 3: Searching by abstract content...")
            print(f"    Abstract preview: {paper.abstract[:100]}...")
            result = self._search_by_abstract(paper)
            if result.found:
                print(f"✅ Found via abstract search: {result.arxiv_id} (confidence: {result.confidence:.3f})")
                return result
            else:
                print(f"❌ Abstract search failed: {result.error_message}")
        else:
            print(f"⏭️  Skipping abstract search (no abstract or too short)")
        

        # Strategy 4: Google Custom Search API fallback
        if self.google_api_key and self.google_search_engine_id:
            print(f"🌐 Strategy 4: Google Custom Search API fallback...")
            result = self._google_search_fallback(paper)
            if result.found:
                print(f"✅ Found via Google API search: {result.arxiv_id} (confidence: {result.confidence:.3f})")
                return result
            else:
                print(f"❌ Google API search failed: {result.error_message}")
        else:
            print(f"⏭️  Skipping Google API search (not configured)")
        

        # All strategies failed
        print(f"💥 ALL SEARCH STRATEGIES FAILED")
        print("="*80)
        
        self.search_stats['failed_matches'] += 1
        return ArxivSearchResult(
            found=False,
            error_message="Not found using any search method",
            search_method="all_methods_failed"
        )

    def _validate_existing_arxiv_id(self, paper: PaperMetadata) -> ArxivSearchResult:
        """
        Validate an existing arXiv ID from the BibTeX.
        
        Args:
            paper: Paper with existing arXiv ID
        
        Returns:
            ArxivSearchResult
        """
        logger.debug(f"Validating existing arXiv ID: {paper.arxiv_id}")
        
        try:
            arxiv_info = self._get_paper_info_by_id(paper.arxiv_id)
            if not arxiv_info:
                return ArxivSearchResult(
                    found=False,
                    error_message=f"arXiv ID {paper.arxiv_id} not found on arXiv"
                )
            
            arxiv_id, arxiv_title, arxiv_abstract = arxiv_info
            print(f"    📄 Found on arXiv: {arxiv_title[:60]}...")
            
            
            # Validate with abstract if available
            if paper.abstract and arxiv_abstract:
                similarity = self._calculate_abstract_similarity(paper.abstract, arxiv_abstract)
                print(f"    📊 Abstract similarity: {similarity:.3f}")
                if similarity >= self.abstract_threshold:
                    self.search_stats['successful_matches'] += 1
                    return ArxivSearchResult(
                        found=True,
                        arxiv_id=arxiv_id,
                        arxiv_title=arxiv_title,
                        confidence=0.95,
                        search_method="existing_id_validated"
                    )
            else:
                # No abstract to validate, accept the ID
                print(f"    ℹ️  No abstract validation available")
                self.search_stats['successful_matches'] += 1
                return ArxivSearchResult(
                    found=True,
                    arxiv_id=arxiv_id,
                    arxiv_title=arxiv_title,
                    confidence=0.8,
                    search_method="existing_id_accepted"
                )
        
        except Exception as e:
            print(f"    ❌ Validation error: {e}")
            logger.error(f"Error validating arXiv ID {paper.arxiv_id}: {e}")
        
        return ArxivSearchResult(
            found=False,
            error_message=f"Failed to validate arXiv ID {paper.arxiv_id}"
        )
    
    def _search_by_title(self, paper: PaperMetadata) -> ArxivSearchResult:
        """
        Search arXiv by paper title.
        
        Args:
            paper: Paper metadata
        
        Returns:
            ArxivSearchResult
        """
        # Clean title for search
        clean_title = self._clean_title_for_search(paper.title)
        print(f"    📝 Original title: {paper.title}")
        print(f"    🧹 Cleaned title: {clean_title}")
        if not clean_title:
            return ArxivSearchResult(
                found=False,
                error_message="Title too short after cleaning"
            )
        
        # Build search query
        query = f"ti:\"{clean_title}\""
        print(f"    🔍 Search query: {query}")
        
        logger.debug(f"Title search query: {query}")
        
        try:
            results = self._execute_arxiv_search(query, max_results=10)
            print(f"    📊 Found {len(results)} results from arXiv API")
            
            
            for i, (arxiv_id, arxiv_title, arxiv_abstract) in enumerate(results):
                print(f"    📄 Result {i+1}: {arxiv_id} - {arxiv_title[:60]}...")
                
                # Calculate title similarity
                title_similarity = self._calculate_title_similarity(
                    paper.title, arxiv_title
                )
                print(f"        📊 Title similarity: {title_similarity:.3f}")
                
                # High confidence match
                if title_similarity >= self.high_confidence_threshold:
                    print(f"        ✅ HIGH CONFIDENCE MATCH!")
                    self.search_stats['successful_matches'] += 1
                    return ArxivSearchResult(
                        found=True,
                        arxiv_id=arxiv_id,
                        arxiv_title=arxiv_title,
                        confidence=title_similarity,
                        search_method="title_high_confidence"
                    )
                
                # Medium confidence - validate with abstract
                elif title_similarity >= self.title_threshold:
                    print(f"        🔍 Medium confidence, checking abstract...")
                    if paper.abstract and arxiv_abstract:
                        abstract_similarity = self._calculate_abstract_similarity(
                            paper.abstract, arxiv_abstract
                        )
                        print(f"        📊 Abstract similarity: {abstract_similarity:.3f}")
                        
                        if abstract_similarity >= self.abstract_threshold:
                            print(f"        ✅ VALIDATED WITH ABSTRACT!")
                            self.search_stats['successful_matches'] += 1
                            return ArxivSearchResult(
                                found=True,
                                arxiv_id=arxiv_id,
                                arxiv_title=arxiv_title,
                                confidence=title_similarity,
                                search_method="title_with_abstract_validation"
                            )
                        else:
                            print(f"        ❌ Abstract validation failed")
                    elif not paper.abstract:
                        print(f"        ✅ No abstract to validate, accepting medium confidence")
                        self.search_stats['successful_matches'] += 1
                        return ArxivSearchResult(
                            found=True,
                            arxiv_id=arxiv_id,
                            arxiv_title=arxiv_title,
                            confidence=title_similarity,
                            search_method="title_medium_confidence"
                        )
                else:
                    print(f"        ❌ Similarity too low ({title_similarity:.3f} < {self.title_threshold})")
        
        except Exception as e:
            print(f"    ❌ API Error: {e}")
            logger.error(f"Error in title search: {e}")
            return ArxivSearchResult(
                found=False,
                error_message=f"Title search failed: {e}"
            )
        
        return ArxivSearchResult(
            found=False,
            error_message="No matching papers found by title",
            search_method="title_search_failed"
        )
    
    def _search_by_abstract(self, paper: PaperMetadata) -> ArxivSearchResult:
        """
        Search arXiv using abstract content.
        
        Args:
            paper: Paper metadata with abstract
        
        Returns:
            ArxivSearchResult
        """
        # Extract meaningful snippet from abstract
        abstract_snippet = self._extract_abstract_snippet(paper.abstract)
        print(f"    📝 Abstract snippet: {abstract_snippet}")
        
        if not abstract_snippet:
            return ArxivSearchResult(
                found=False,
                error_message="Could not extract meaningful abstract snippet"
            )
        
        # Search in all fields
        query = f'all:"{abstract_snippet}"'
        print(f"    🔍 Search query: {query}")
        
        logger.debug(f"Abstract search query: {query}")
        
        try:
            results = self._execute_arxiv_search(query, max_results=5)
            print(f"    📊 Found {len(results)} results from arXiv API")
            
            
            for i, (arxiv_id, arxiv_title, arxiv_abstract) in enumerate(results):
                print(f"    📄 Result {i+1}: {arxiv_id} - {arxiv_title[:60]}...")
                
                # Check abstract similarity
                abstract_similarity = self._calculate_abstract_similarity(
                    paper.abstract, arxiv_abstract
                )
                print(f"        📊 Abstract similarity: {abstract_similarity:.3f}")
                
                if abstract_similarity >= self.abstract_threshold:
                    # Also check title for additional confidence
                    title_similarity = self._calculate_title_similarity(
                        paper.title, arxiv_title
                    )
                    print(f"        📊 Title similarity: {title_similarity:.3f}")
                    
                    confidence = max(title_similarity, 0.7)  # Boost confidence for abstract match
                    print(f"        ✅ ABSTRACT MATCH FOUND!")
                    
                    self.search_stats['successful_matches'] += 1
                    return ArxivSearchResult(
                        found=True,
                        arxiv_id=arxiv_id,
                        arxiv_title=arxiv_title,
                        confidence=confidence,
                        search_method="abstract_search"
                    )
                else:
                    print(f"        ❌ Abstract similarity too low")
        
        except Exception as e:
            logger.error(f"Error in abstract search: {e}")
        
        return ArxivSearchResult(
            found=False,
            error_message="No matching papers found by abstract",
            search_method="abstract_search_failed"
        )
    
    def _google_search_fallback(self, paper: PaperMetadata) -> ArxivSearchResult:
        """
        Use Google Custom Search API as fallback to find papers on arXiv.
        
        Args:
            paper: Paper metadata
        
        Returns:
            ArxivSearchResult
        """
        if not self.google_api_key or not self.google_search_engine_id:
            return ArxivSearchResult(
                found=False,
                error_message="Google API credentials not available"
            )
        
        #print(f"    🌐 Using Google Custom Search API...")
        #print(f"    🔑 API Key: {'***' + self.google_api_key[-4:] if self.google_api_key else 'Not set'}")
        #print(f"    🔍 Search Engine ID: {self.google_search_engine_id}")
        

        # ADD THIS LOG
        print(f"\n🔍 GOOGLE FALLBACK ACTIVATED for: {paper.title[:50]}...")
        logger.info(f"🔍 Google Custom Search API activated for: {paper.title[:50]}...")
    

        self.search_stats['google_searches'] += 1
        
        try:
            query = paper.title
            logger.debug(f"Google Custom Search API fallback for: {paper.title[:50]}...")
            print(f"    📝 Search query: {query}")
            
            # ADD THIS LOG
            #print(f"📡 Making Google API request with query: {query[:50]}...")

            # Google Custom Search API endpoint
            search_url = "https://www.googleapis.com/customsearch/v1"
            
            params = {
                'key': self.google_api_key,
                'cx': self.google_search_engine_id,
                'q': query,
                'siteSearch': 'arxiv.org',
                "siteSearchFilter": "i",
                'num': 5,  # Get up to 5 results
                'fields': 'items(link,title,snippet)'  # Only get the fields we need
            }
            
            print(f"    📡 Making Google API request...")
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            search_results = response.json()
            
            # ADD THIS LOG
            print(f"📊 Google returned {len(search_results.get('items', []))} results")

            if 'items' not in search_results:
                print(f"    ❌ No results from Google Custom Search API")
                logger.info("No results from Google Custom Search API")
                return ArxivSearchResult(
                    found=False,
                    error_message="No results from Google Custom Search API",
                    search_method="google_search_failed"
                )
            
            print(f"    📊 Google returned {len(search_results['items'])} results")


            for i, item in enumerate(search_results['items']):
                url = item['link']
                title = item.get('title', 'No title')
                print(f"    📄 Result {i+1}: {title[:60]}...")
                print(f"        🔗 URL: {url}")
                
                # Extract arXiv ID from URL
                arxiv_id = self._extract_arxiv_id_from_url(url)
                if not arxiv_id:
                    print(f"        ❌ Could not extract arXiv ID from URL")
                    continue
                
                print(f"        📋 Extracted arXiv ID: {arxiv_id}")
                
                # Get paper info from arXiv
                arxiv_info = self._get_paper_info_by_id(arxiv_id)
                if not arxiv_info:
                    print(f"        ❌ Could not fetch info for {arxiv_id}")
                    continue
                
                _, arxiv_title, arxiv_abstract = arxiv_info
                print(f"        📄 ArXiv title: {arxiv_title[:60]}...")
                
                # Validate using abstract matching (50% threshold for Google fallback)
                if paper.abstract and arxiv_abstract:
                    abstract_similarity = self._calculate_abstract_similarity(
                        paper.abstract, arxiv_abstract, threshold=0.5
                    )
                    print(f"        📊 Abstract similarity: {abstract_similarity:.3f}")
                    
                    if abstract_similarity >= 0.5:
                        print(f"        ✅ GOOGLE SEARCH MATCH FOUND!")
                        self.search_stats['successful_matches'] += 1
                        return ArxivSearchResult(
                            found=True,
                            arxiv_id=arxiv_id,
                            arxiv_title=arxiv_title,
                            confidence=0.6,
                            search_method="google_search"
                        )
                    else:
                        print(f"        ❌ Abstract validation failed")
                elif not paper.abstract:
                    print(f"        ✅ No abstract to validate, accepting Google match")
                    self.search_stats['successful_matches'] += 1
                    return ArxivSearchResult(
                        found=True,
                        arxiv_id=arxiv_id,
                        arxiv_title=arxiv_title,
                        confidence=0.5,
                        search_method="google_search"
                    )
                else:
                    print(f"        ❌ No arXiv abstract available for validation")
            
            return ArxivSearchResult(
                found=False,
                error_message="Google search failed to find matching paper",
                search_method="google_search_failed"
            )
            
        except requests.exceptions.HTTPError as e:
            error_msg = "Google API error"
            if e.response.status_code == 429:
                error_msg = "Google API rate limit exceeded - consider upgrading your quota"
            elif e.response.status_code == 403:
                error_msg = "Google API access forbidden - check your API key and billing"
            
            print(f"    ❌ {error_msg}: {e}")
            logger.warning(f"{error_msg}: {e}")
            return ArxivSearchResult(
                found=False,
                error_message=error_msg,
                search_method="google_search_failed"
            )
        except Exception as e:
            print(f"    ❌ Google API exception: {e}")
            logger.warning(f"Google Custom Search API failed: {e}")
            return ArxivSearchResult(
                found=False,
                error_message=f"Google search exception: {e}",
                search_method="google_search_failed"
            )


    def _basic_google_search(self, paper: PaperMetadata) -> ArxivSearchResult:
        """Use basic Google search as final fallback with detailed logging."""
        print(f"    🔍 Using basic Google search (googlesearch-python)...")
        
        try:
            query = f"{paper.title} site:arxiv.org"
            print(f"    📝 Search query: {query}")
            
            results = list(google_search(query, num_results=5, sleep_interval=2))
            print(f"    📊 Found {len(results)} Google results")
            
            for i, url in enumerate(results):
                print(f"    📄 Result {i+1}: {url}")
                
                # Extract arXiv ID from URL
                arxiv_id = self._extract_arxiv_id_from_url(url)
                if not arxiv_id:
                    print(f"        ❌ Could not extract arXiv ID from URL")
                    continue
                
                print(f"        📋 Extracted arXiv ID: {arxiv_id}")
                
                # Get paper info from arXiv
                arxiv_info = self._get_paper_info_by_id(arxiv_id)
                if not arxiv_info:
                    print(f"        ❌ Could not fetch info for {arxiv_id}")
                    continue
                
                _, arxiv_title, arxiv_abstract = arxiv_info
                print(f"        📄 ArXiv title: {arxiv_title[:60]}...")
                
                # Basic validation - just check if we can get the paper info
                print(f"        ✅ BASIC GOOGLE SEARCH MATCH FOUND!")
                self.search_stats['successful_matches'] += 1
                return ArxivSearchResult(
                    found=True,
                    arxiv_id=arxiv_id,
                    arxiv_title=arxiv_title,
                    confidence=0.4,  # Lower confidence for basic search
                    search_method="basic_google_search"
                )
            
            return ArxivSearchResult(
                found=False,
                error_message="Basic Google search failed to find matching paper",
                search_method="basic_google_search_failed"
            )
            
        except Exception as e:
            print(f"    ❌ Basic Google search exception: {e}")
            logger.warning(f"Basic Google search failed: {e}")
            return ArxivSearchResult(
                found=False,
                error_message=f"Basic Google search exception: {e}",
                search_method="basic_google_search_failed"
            )
    
    def _calculate_abstract_similarity(self, abstract1: str, abstract2: str, threshold: float = None) -> float:
        """Calculate similarity between two abstracts and return the score."""
        if threshold is None:
            threshold = self.abstract_threshold
        
        words1 = set(re.findall(r'\w+', abstract1.lower()))
        words2 = set(re.findall(r'\w+', abstract2.lower()))
        
        if len(words1) == 0 or len(words2) == 0:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity


    
    def _execute_arxiv_search(self, query: str, max_results: int = 10) -> List[Tuple[str, str, str]]:
        """Execute search query against arXiv API with detailed logging."""
        self.search_stats['api_calls'] += 1
        
        params = {
            'search_query': query,
            'start': 0,
            'max_results': max_results
        }
        
        print(f"    📡 ArXiv API call: {query}")
        
        response = requests.get(self.api_base_url, params=params)
        response.raise_for_status()
        
        # Parse XML response
        root = ET.fromstring(response.content)
        entries = root.findall('{http://www.w3.org/2005/Atom}entry')
        
        print(f"    📊 ArXiv returned {len(entries)} entries")
        
        results = []
        for entry in entries:
            try:
                # Extract arXiv ID from URL
                id_url = entry.find('{http://www.w3.org/2005/Atom}id').text
                arxiv_id = self._extract_arxiv_id_from_url(id_url)
                if not arxiv_id:
                    continue
                
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                
                results.append((arxiv_id, title, abstract))
                
            except Exception as e:
                logger.warning(f"Error parsing arXiv entry: {e}")
                continue
        
        # Add delay to be respectful to arXiv servers
        time.sleep(self.delay)
        
        return results
    
    def _get_paper_info_by_id(self, arxiv_id: str) -> Optional[Tuple[str, str, str]]:
        """
        Get paper information directly by arXiv ID.
        
        Args:
            arxiv_id: arXiv identifier
        
        Returns:
            Tuple of (arxiv_id, title, abstract) or None
        """
        params = {
            'id_list': arxiv_id,
            'max_results': 1
        }
        
        try:
            response = requests.get(self.api_base_url, params=params)
            
            # Handle old format papers
            if response.status_code == 400:
                params = {'search_query': f'id:{arxiv_id}', 'max_results': 1}
                response = requests.get(self.api_base_url, params=params)
            
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            entry = root.find('{http://www.w3.org/2005/Atom}entry')
            
            if entry is not None:
                title = entry.find('{http://www.w3.org/2005/Atom}title').text.strip()
                abstract = entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
                return arxiv_id, title, abstract
        
        except Exception as e:
            logger.error(f"Error getting info for arXiv ID {arxiv_id}: {e}")
        
        return None
    
    def _clean_title_for_search(self, title: str) -> str:
        """Clean title for arXiv search."""
        if not title:
            return ""
        
        # Remove special characters that break queries
        clean_title = re.sub(r'[:\.\(\)\[\]"\'`]', '', title)
        
        # Remove LaTeX commands
        clean_title = re.sub(r'\\[a-zA-Z]*\{([^}]*)\}', r'\1', clean_title)
        clean_title = re.sub(r'\\["\']', '', clean_title)
        clean_title = re.sub(r'\\[a-zA-Z]+', '', clean_title)
        
        # Replace hyphens with spaces
        clean_title = clean_title.replace("-", " ")
        
        # Normalize whitespace
        clean_title = re.sub(r'\s+', ' ', clean_title).strip()
        
        return clean_title
    
    def _extract_abstract_snippet(self, abstract: str) -> Optional[str]:
        """Extract a meaningful snippet from abstract for search."""
        if not abstract or len(abstract.strip()) < 20:
            return None
        
        # Clean abstract
        clean_abstract = re.sub(r'[^\w\s]', ' ', abstract)
        clean_abstract = re.sub(r'\s+', ' ', clean_abstract).strip()
        
        # Try to find first sentence
        sentences = re.split(r'[.!?]+', clean_abstract)
        if sentences and len(sentences[0].strip()) >= 20:
            snippet = sentences[0].strip()[:60]
        else:
            # Take first 50 characters of meaningful words
            words = clean_abstract.split()[:10]
            snippet = ' '.join(words)[:50]
        
        return snippet.strip() if len(snippet.strip()) >= 10 else None
    
    def _calculate_title_similarity_old(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        words1 = set(re.findall(r'\w+', title1.lower()))
        words2 = set(re.findall(r'\w+', title2.lower()))
        
        if len(words1) == 0 or len(words2) == 0:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    

    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles - IMPROVED to handle common variations.
        """
        import re
        
        def normalize_title(title):
            """Normalize title to handle common variations."""
            # Convert to lowercase
            title = title.lower()
            
            # Handle common singular/plural patterns
            title = re.sub(r'\btransitions?\b', 'transition', title)
            title = re.sub(r'\bmeasurements?\b', 'measurement', title)
            title = re.sub(r'\bphases?\b', 'phase', title)
            title = re.sub(r'\bstates?\b', 'state', title)
            title = re.sub(r'\bcircuits?\b', 'circuit', title)
            title = re.sub(r'\bsystems?\b', 'system', title)
            title = re.sub(r'\bmodels?\b', 'model', title)
            title = re.sub(r'\beffects?\b', 'effect', title)
            title = re.sub(r'\bproperties?\b', 'property', title)
            title = re.sub(r'\bmethods?\b', 'method', title)
            
            return title
        
        # Normalize both titles
        norm_title1 = normalize_title(title1)
        norm_title2 = normalize_title(title2)
        
        # Extract words
        words1 = set(re.findall(r'\w+', norm_title1))
        words2 = set(re.findall(r'\w+', norm_title2))
        
        if len(words1) == 0 or len(words2) == 0:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0


    def _abstracts_similar(self, abstract1: str, abstract2: str, threshold: float = None) -> bool:
        """Check if two abstracts are similar enough."""
        if threshold is None:
            threshold = self.abstract_threshold
        
        words1 = set(re.findall(r'\w+', abstract1.lower()))
        words2 = set(re.findall(r'\w+', abstract2.lower()))
        
        if len(words1) == 0 or len(words2) == 0:
            return False
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        similarity = intersection / union if union > 0 else 0
        return similarity >= threshold
    
    def _extract_arxiv_id_from_url(self, url: str) -> Optional[str]:
        """Extract arXiv ID from URL - FIXED to handle both old and new format IDs."""
        if not url or 'arxiv.org' not in url:
            return None
        
        # Handle different URL formats - CORRECTED patterns to capture full IDs
        patterns = [
            r'/abs/([^/\s\?#]+(?:/[^/\s\?#]+)?)',          # /abs/2112.00716 or /abs/quant-ph/0605249
            r'/pdf/([^/\s\?#]+(?:/[^/\s\?#]+)?)',          # /pdf/2112.00716.pdf or /pdf/quant-ph/0605249
            r'/html/([^/\s\?#]+(?:/[^/\s\?#]+)?)',         # /html/2112.00716v1 (some newer URLs)
            r'arxiv\.org/[^/]*/([^/\s\?#]+(?:/[^/\s\?#]+)?)' # arxiv.org/*/ID (catch-all)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                arxiv_part = match.group(1)
                
                # Clean up version numbers and file extensions
                arxiv_part = re.sub(r'\.pdf$', '', arxiv_part)  # Remove .pdf
                arxiv_part = re.sub(r'\.html$', '', arxiv_part)  # Remove .html
                
                # Handle version numbers (v1, v2, etc.)
                if 'v' in arxiv_part:
                    parts = arxiv_part.split('v')
                    if len(parts) == 2 and parts[1].isdigit():
                        arxiv_part = parts[0]
                
                # Validate format
                # New format: 2112.00716 (year.number)
                if re.match(r'^\d{4}\.\d{4,5}$', arxiv_part):
                    return arxiv_part
                
                # Old format: quant-ph/0605249 (subject-class/YYMMnnn)
                if re.match(r'^[a-z-]+/\d{7}$', arxiv_part):
                    return arxiv_part
                
                # Very old format: subject-class/YYMMnnn (flexible digits)
                if re.match(r'^[a-z-]+/\d{4,7}$', arxiv_part):
                    return arxiv_part
        
        return None
    
    def download_paper(self, arxiv_id: str, output_dir: Path) -> DownloadResult:
        """
        Download PDF and TEX files for a paper.
        
        Args:
            arxiv_id: arXiv identifier
            output_dir: Directory to save files
        
        Returns:
            DownloadResult with download status
        """
        logger.info(f"Downloading paper: {arxiv_id}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Clean arXiv ID for filename
        clean_id = clean_filename(arxiv_id)
        
        result = DownloadResult()
        
        # Download PDF
        pdf_path = output_dir / f"{clean_id}.pdf"
        pdf_urls = [
            f"https://arxiv.org/pdf/{arxiv_id}.pdf",
            f"https://arxiv.org/pdf/{arxiv_id}"
        ]
        
        for pdf_url in pdf_urls:
            try:
                logger.debug(f"Trying PDF download: {pdf_url}")
                response = requests.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(pdf_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                result.pdf_downloaded = True
                result.pdf_path = str(pdf_path)
                logger.info(f"PDF downloaded: {pdf_path}")
                break
                
            except Exception as e:
                logger.warning(f"PDF download failed for {pdf_url}: {e}")
        
        # Download TEX source
        tex_urls = [
            f"https://arxiv.org/e-print/{arxiv_id}",
            f"https://arxiv.org/src/{arxiv_id}"
        ]
        
        tar_path = output_dir / f"{clean_id}.tar.gz"
        
        for tex_url in tex_urls:
            try:
                logger.debug(f"Trying TEX download: {tex_url}")
                response = requests.get(tex_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(tar_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Extract main tex file
                extracted_tex = extract_tar_archive(tar_path, output_dir, clean_id)
                if extracted_tex:
                    result.tex_downloaded = True
                    result.tex_path = str(extracted_tex)
                    logger.info(f"TEX downloaded and extracted: {extracted_tex}")
                
                # Clean up tar file
                if tar_path.exists():
                    tar_path.unlink()
                break
                
            except Exception as e:
                logger.warning(f"TEX download failed for {tex_url}: {e}")
        
        # Add respectful delay
        time.sleep(self.delay)
        
        if not result.pdf_downloaded and not result.tex_downloaded:
            result.error_message = "Failed to download both PDF and TEX files"
        
        return result
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """Get search statistics."""
        return self.search_stats.copy()
    
    def reset_statistics(self) -> None:
        """Reset search statistics."""
        self.search_stats = {
            'api_calls': 0,
            'google_searches': 0,
            'successful_matches': 0,
            'failed_matches': 0
        }