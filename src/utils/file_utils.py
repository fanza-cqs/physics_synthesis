#!/usr/bin/env python3
"""
File utilities for the Physics Literature Synthesis Pipeline.

Common file operations used across the application.
"""

import os
import shutil
import tarfile
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urlparse

from .logging_config import get_logger

logger = get_logger(__name__)

def ensure_directory_exists(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Directory path to create
    """
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")

def clean_filename(filename: str) -> str:
    """
    Clean a filename to be filesystem-safe.
    
    Args:
        filename: Original filename
    
    Returns:
        Cleaned filename safe for filesystem use
    """
    # Replace problematic characters
    replacements = {
        '/': '_',
        '\\': '_',
        ':': '_',
        '*': '_',
        '?': '_',
        '"': '_',
        '<': '_',
        '>': '_',
        '|': '_',
        ' ': '_'
    }
    
    clean_name = filename
    for old, new in replacements.items():
        clean_name = clean_name.replace(old, new)
    
    # Remove multiple underscores
    while '__' in clean_name:
        clean_name = clean_name.replace('__', '_')
    
    # Remove leading/trailing underscores
    clean_name = clean_name.strip('_')
    
    return clean_name

def extract_arxiv_id_from_url(url: str) -> Optional[str]:
    """
    Extract arXiv ID from various URL formats.
    
    Args:
        url: URL containing arXiv ID
    
    Returns:
        Extracted arXiv ID or None if not found
    """
    if not url or ('arxiv.org' not in url and 'arxiv:' not in url.lower()):
        return None
    
    # Handle different URI formats
    if '/abs/' in url:
        arxiv_part = url.split('/abs/')[-1]
    elif '/pdf/' in url:
        arxiv_part = url.split('/pdf/')[-1]
    elif 'arxiv:' in url.lower():
        arxiv_part = url.lower().split('arxiv:')[-1]
    else:
        # Fallback to last part of URL
        arxiv_part = url.split('/')[-1]
    
    if not arxiv_part or len(arxiv_part) <= 3:
        return None
    
    # Clean up version numbers and file extensions
    if 'v' in arxiv_part and arxiv_part.split('v')[-1].isdigit():
        arxiv_part = arxiv_part.split('v')[0]
    
    if arxiv_part.endswith('.pdf'):
        arxiv_part = arxiv_part[:-4]
    
    return arxiv_part

def extract_tar_archive(tar_path: Path, output_dir: Path, target_filename: str) -> Optional[Path]:
    """
    Extract a tar.gz archive and find the main .tex file.
    
    Args:
        tar_path: Path to the tar.gz file
        output_dir: Directory to extract to
        target_filename: Base name for the extracted file
    
    Returns:
        Path to the extracted main file, or None if extraction failed
    """
    try:
        temp_dir = output_dir / f"{target_filename}_temp"
        
        with tarfile.open(tar_path, 'r:gz') as tar:
            tar.extractall(temp_dir)
        
        # Find .tex files
        tex_files = list(temp_dir.rglob("*.tex"))
        
        if tex_files:
            # Heuristic: find main file (often the largest)
            main_tex = max(tex_files, key=lambda x: x.stat().st_size)
            
            # Copy to main directory
            final_tex_path = output_dir / f"{target_filename}.tex"
            final_tex_path.write_text(
                main_tex.read_text(encoding='utf-8', errors='ignore')
            )
            
            # Clean up temporary directory
            shutil.rmtree(temp_dir, ignore_errors=True)
            
            logger.info(f"Extracted main tex file: {final_tex_path}")
            return final_tex_path
        
        # Clean up if no tex files found
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.warning(f"No .tex files found in archive: {tar_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting tar archive {tar_path}: {e}")
        return None

def get_files_with_extensions(
    directory: Path,
    extensions: Set[str],
    recursive: bool = True
) -> List[Path]:
    """
    Get all files with specified extensions from a directory.
    
    Args:
        directory: Directory to search
        extensions: Set of file extensions (e.g., {'.pdf', '.tex'})
        recursive: Whether to search recursively
    
    Returns:
        List of file paths matching the extensions
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []
    
    files = []
    search_pattern = "**/*" if recursive else "*"
    
    for file_path in directory.glob(search_pattern):
        if file_path.is_file() and file_path.suffix.lower() in extensions:
            files.append(file_path)
    
    logger.debug(f"Found {len(files)} files with extensions {extensions} in {directory}")
    return files

def safe_file_read(file_path: Path, encoding: str = 'utf-8') -> str:
    """
    Safely read a text file with error handling.
    
    Args:
        file_path: Path to the file
        encoding: Text encoding to use
    
    Returns:
        File content as string, empty string if reading fails
    """
    try:
        return file_path.read_text(encoding=encoding, errors='ignore')
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return ""

def get_file_size_mb(file_path: Path) -> float:
    """
    Get file size in megabytes.
    
    Args:
        file_path: Path to the file
    
    Returns:
        File size in MB
    """
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0

def create_directory_structure(base_path: Path, subdirs: List[str]) -> None:
    """
    Create a directory structure with subdirectories.
    
    Args:
        base_path: Base directory path
        subdirs: List of subdirectory names to create
    """
    ensure_directory_exists(base_path)
    
    for subdir in subdirs:
        subdir_path = base_path / subdir
        ensure_directory_exists(subdir_path)
        logger.debug(f"Created subdirectory: {subdir_path}")

def count_words_in_text(text: str) -> int:
    """
    Count words in a text string.
    
    Args:
        text: Input text
    
    Returns:
        Number of words
    """
    if not text:
        return 0
    return len(text.split())