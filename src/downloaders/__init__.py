# src/downloaders/__init__.py
"""Download modules for literature acquisition from arXiv."""

from .bibtex_parser import BibtexParser, PaperMetadata
from .arxiv_searcher import ArxivSearcher, ArxivSearchResult, DownloadResult
from .literature_downloader import LiteratureDownloader, PaperDownloadResult

__all__ = [
    'BibtexParser',
    'PaperMetadata',
    'ArxivSearcher', 
    'ArxivSearchResult',
    'DownloadResult',
    'LiteratureDownloader',
    'PaperDownloadResult'
]