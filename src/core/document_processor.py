#!/usr/bin/env python3
"""
Document processor for the Physics Literature Synthesis Pipeline.

Handles extraction and processing of text from physics papers in various formats.
Focuses on preserving scientific content while cleaning LaTeX formatting.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass

import PyPDF2
import fitz  # PyMuPDF

from ..utils.logging_config import get_logger
from ..utils.file_utils import safe_file_read, count_words_in_text

logger = get_logger(__name__)

@dataclass
class ProcessedDocument:
    """Container for a processed document with metadata."""
    file_path: str
    file_name: str
    source_type: str
    text: str
    word_count: int
    file_size_mb: float
    processing_success: bool
    error_message: Optional[str] = None

class DocumentProcessor:
    """
    Extracts and processes text from physics papers.
    
    Supports PDF and LaTeX files with special handling for scientific content.
    """
    
    def __init__(self, supported_extensions: Set[str] = None):
        """
        Initialize the document processor.
        
        Args:
            supported_extensions: Set of file extensions to process
        """
        self.supported_extensions = supported_extensions or {'.pdf', '.tex', '.txt'}
        logger.info(f"Document processor initialized with extensions: {self.supported_extensions}")
    
    def extract_pdf_text(self, pdf_path: Path) -> str:
        """
        Extract text from PDF using PyMuPDF with PyPDF2 fallback.
        
        Args:
            pdf_path: Path to the PDF file
        
        Returns:
            Extracted text content
        """
        logger.debug(f"Extracting text from PDF: {pdf_path}")
        
        # Try PyMuPDF first (better for scientific papers)
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            
            if text.strip():
                logger.debug(f"Successfully extracted {len(text)} characters with PyMuPDF")
                return text
            
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed for {pdf_path}: {e}")
        
        # Fallback to PyPDF2
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
            
            logger.debug(f"Successfully extracted {len(text)} characters with PyPDF2")
            return text
            
        except Exception as e:
            logger.error(f"Both PDF extraction methods failed for {pdf_path}: {e}")
            return ""
    
    def extract_tex_text(self, tex_path: Path) -> str:
        """
        Extract and clean text from LaTeX files.
        
        Preserves scientific content while removing LaTeX formatting commands.
        
        Args:
            tex_path: Path to the LaTeX file
        
        Returns:
            Cleaned text content
        """
        logger.debug(f"Extracting text from LaTeX: {tex_path}")
        
        raw_content = safe_file_read(tex_path)
        if not raw_content:
            return ""
        
        # Clean LaTeX content
        cleaned_text = self._clean_latex_content(raw_content)
        
        logger.debug(f"Extracted and cleaned {len(cleaned_text)} characters from LaTeX")
        return cleaned_text
    
    def _clean_latex_content(self, content: str) -> str:
        """
        Clean LaTeX content while preserving scientific meaning.
        
        Args:
            content: Raw LaTeX content
        
        Returns:
            Cleaned text
        """
        # Remove comments
        content = re.sub(r'%.*', '', content)
        
        # Preserve and clean equation environments
        content = re.sub(
            r'\\begin\{equation\*?\}(.*?)\\end\{equation\*?\}',
            r'EQUATION: \1',
            content,
            flags=re.DOTALL
        )
        content = re.sub(
            r'\\begin\{align\*?\}(.*?)\\end\{align\*?\}',
            r'EQUATIONS: \1',
            content,
            flags=re.DOTALL
        )
        
        # Clean inline math
        content = re.sub(r'\$([^$]+)\$', r'MATH: \1', content)
        
        # Remove figure/table environments but keep captions
        content = re.sub(
            r'\\begin\{figure\}.*?\\caption\{([^}]*)\}.*?\\end\{figure\}',
            r'Figure: \1',
            content,
            flags=re.DOTALL
        )
        content = re.sub(
            r'\\begin\{table\}.*?\\caption\{([^}]*)\}.*?\\end\{table\}',
            r'Table: \1',
            content,
            flags=re.DOTALL
        )
        
        # Clean common LaTeX commands while preserving content
        # \command{content} -> content
        content = re.sub(r'\\[a-zA-Z]+\*?\{([^}]*)\}', r'\1', content)
        
        # Remove standalone commands
        content = re.sub(r'\\[a-zA-Z]+\*?', '', content)
        
        # Clean up braces and special characters
        content = re.sub(r'[{}]', '', content)
        content = re.sub(r'\\[^\w\s]', '', content)  # Remove escaped symbols
        
        # Normalize whitespace
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        return content
    
    def process_file(self, file_path: Path, source_type: str = "unknown") -> Optional[ProcessedDocument]:
        """
        Process a single file and extract its content.
        
        Args:
            file_path: Path to the file to process
            source_type: Type of source (literature, your_work, etc.)
        
        Returns:
            ProcessedDocument object or None if processing fails
        """
        logger.info(f"Processing file: {file_path}")
        
        # Check if file exists and has supported extension
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None
        
        if file_path.suffix.lower() not in self.supported_extensions:
            logger.warning(f"Unsupported file extension: {file_path.suffix}")
            return None
        
        # Get file size
        try:
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
        except Exception:
            file_size_mb = 0.0
        
        # Extract text based on file type
        text = ""
        error_message = None
        processing_success = False
        
        try:
            if file_path.suffix.lower() == '.pdf':
                text = self.extract_pdf_text(file_path)
            elif file_path.suffix.lower() == '.tex':
                text = self.extract_tex_text(file_path)
            elif file_path.suffix.lower() == '.txt':
                text = safe_file_read(file_path)
            
            if text.strip():
                processing_success = True
                logger.info(f"Successfully processed {file_path.name}: {len(text)} characters")
            else:
                error_message = "No text extracted from file"
                logger.warning(f"No text extracted from {file_path}")
                
        except Exception as e:
            error_message = str(e)
            logger.error(f"Error processing {file_path}: {e}")
        
        return ProcessedDocument(
            file_path=str(file_path),
            file_name=file_path.name,
            source_type=source_type,
            text=text,
            word_count=count_words_in_text(text),
            file_size_mb=file_size_mb,
            processing_success=processing_success,
            error_message=error_message
        )
    
    def process_directory(self, directory_path: Path, source_type: str) -> List[ProcessedDocument]:
        """
        Process all supported files in a directory.
        
        Args:
            directory_path: Path to the directory to process
            source_type: Type of source for all files in this directory
        
        Returns:
            List of ProcessedDocument objects
        """
        logger.info(f"Processing directory: {directory_path} (source_type: {source_type})")
        
        if not directory_path.exists():
            logger.error(f"Directory does not exist: {directory_path}")
            return []
        
        documents = []
        processed_count = 0
        
        # Find all supported files
        for file_path in directory_path.rglob("*"):
            if (file_path.is_file() and 
                file_path.suffix.lower() in self.supported_extensions):
                
                doc = self.process_file(file_path, source_type)
                if doc:
                    documents.append(doc)
                    if doc.processing_success:
                        processed_count += 1
        
        logger.info(
            f"Directory processing complete: {processed_count}/{len(documents)} "
            f"files successfully processed from {directory_path}"
        )
        
        return documents
    
    def get_processing_stats(self, documents: List[ProcessedDocument]) -> Dict[str, any]:
        """
        Get statistics about processed documents.
        
        Args:
            documents: List of processed documents
        
        Returns:
            Dictionary with processing statistics
        """
        if not documents:
            return {}
        
        successful_docs = [doc for doc in documents if doc.processing_success]
        failed_docs = [doc for doc in documents if not doc.processing_success]
        
        stats = {
            'total_documents': len(documents),
            'successful_extractions': len(successful_docs),
            'failed_extractions': len(failed_docs),
            'success_rate': len(successful_docs) / len(documents) * 100,
            'total_words': sum(doc.word_count for doc in successful_docs),
            'total_size_mb': sum(doc.file_size_mb for doc in documents),
            'avg_words_per_doc': (
                sum(doc.word_count for doc in successful_docs) / len(successful_docs)
                if successful_docs else 0
            ),
            'source_breakdown': {}
        }
        
        # Source type breakdown
        for doc in documents:
            source_type = doc.source_type
            if source_type not in stats['source_breakdown']:
                stats['source_breakdown'][source_type] = {
                    'count': 0,
                    'successful': 0,
                    'words': 0
                }
            
            stats['source_breakdown'][source_type]['count'] += 1
            if doc.processing_success:
                stats['source_breakdown'][source_type]['successful'] += 1
                stats['source_breakdown'][source_type]['words'] += doc.word_count
        
        return stats