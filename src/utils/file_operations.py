#!/usr/bin/env python3
"""
Enhanced file operations utilities.

Consolidates common file handling patterns used throughout the codebase.
This is an additive utility - existing code continues to work unchanged.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Union
import hashlib
import mimetypes

from .logging_config import get_logger

logger = get_logger(__name__)

def get_file_info(file_path: Union[str, Path]) -> Dict[str, any]:
    """
    Get comprehensive information about a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Dictionary with file information
    """
    path = Path(file_path)
    
    try:
        if not path.exists():
            return {
                'exists': False,
                'path': str(path),
                'name': path.name,
                'extension': path.suffix
            }
        
        stat = path.stat()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        return {
            'exists': True,
            'path': str(path),
            'name': path.name,
            'stem': path.stem,
            'extension': path.suffix.lower(),
            'size_bytes': stat.st_size,
            'size_mb': round(stat.st_size / (1024 * 1024), 2),
            'size_kb': round(stat.st_size / 1024, 2),
            'is_file': path.is_file(),
            'is_directory': path.is_dir(),
            'mime_type': mime_type,
            'modified_timestamp': stat.st_mtime,
            'readable': os.access(path, os.R_OK),
            'writable': os.access(path, os.W_OK)
        }
    except Exception as e:
        logger.error(f"Error getting file info for {path}: {e}")
        return {
            'exists': False,
            'path': str(path),
            'error': str(e)
        }

def validate_file_for_processing(file_path: Union[str, Path], 
                               supported_extensions: set = None) -> bool:
    """
    Validate if a file is suitable for document processing.
    
    Args:
        file_path: Path to validate
        supported_extensions: Set of allowed extensions (default: {'.pdf', '.txt', '.tex', '.md'})
    
    Returns:
        True if file is valid for processing
    """
    if supported_extensions is None:
        supported_extensions = {'.pdf', '.txt', '.tex', '.md'}
    
    info = get_file_info(file_path)
    
    if not info['exists']:
        return False
    
    if not info['is_file']:
        return False
    
    if info['size_bytes'] == 0:
        return False
    
    if info['extension'] not in supported_extensions:
        return False
    
    if not info['readable']:
        return False
    
    return True

def safe_create_directory(directory: Union[str, Path]) -> bool:
    """
    Safely create a directory with proper error handling.
    
    Args:
        directory: Directory path to create
    
    Returns:
        True if directory exists or was created successfully
    """
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logger.error(f"Failed to create directory {directory}: {e}")
        return False

def count_files_by_extension(directory: Union[str, Path], 
                           recursive: bool = True) -> Dict[str, int]:
    """
    Count files by extension in a directory.
    
    Args:
        directory: Directory to scan
        recursive: Whether to scan recursively
    
    Returns:
        Dictionary mapping extensions to counts
    """
    path = Path(directory)
    
    if not path.exists() or not path.is_dir():
        return {}
    
    counts = {}
    
    try:
        pattern = "**/*" if recursive else "*"
        
        for file_path in path.glob(pattern):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                counts[ext] = counts.get(ext, 0) + 1
    
    except Exception as e:
        logger.error(f"Error counting files in {directory}: {e}")
    
    return counts

def calculate_file_hash(file_path: Union[str, Path], 
                       algorithm: str = 'md5') -> Optional[str]:
    """
    Calculate hash of a file for deduplication.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
    
    Returns:
        Hex digest of file hash, or None if error
    """
    try:
        hasher = hashlib.new(algorithm)
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    except Exception as e:
        logger.error(f"Error calculating {algorithm} hash for {file_path}: {e}")
        return None

def handle_file_operation_safely(operation_func, *args, **kwargs):
    """
    Safely execute a file operation with standardized error handling.
    
    Args:
        operation_func: Function to execute
        *args, **kwargs: Arguments for the function
    
    Returns:
        Tuple of (success: bool, result: any, error: str)
    """
    try:
        result = operation_func(*args, **kwargs)
        return True, result, None
    except FileNotFoundError as e:
        error_msg = f"File not found: {e}"
        logger.error(error_msg)
        return False, None, error_msg
    except PermissionError as e:
        error_msg = f"Permission denied: {e}"
        logger.error(error_msg)
        return False, None, error_msg
    except OSError as e:
        error_msg = f"OS error: {e}"
        logger.error(error_msg)
        return False, None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        logger.error(error_msg)
        return False, None, error_msg