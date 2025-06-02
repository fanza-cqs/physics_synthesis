#!/usr/bin/env python3
"""
Knowledge base module for the Physics Literature Synthesis Pipeline.

High-level interface for building and managing the literature knowledge base.
Coordinates document processing and embedding creation.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any

from .document_processor import DocumentProcessor, ProcessedDocument
from .embeddings import EmbeddingsManager, SearchResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class KnowledgeBase:
    """
    High-level knowledge base for physics literature.
    
    Manages the entire pipeline from document processing to semantic search.
    """
    
    def __init__(self, 
                 embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 supported_extensions: set = None):
        """
        Initialize the knowledge base.
        
        Args:
            embedding_model: Name of the sentence transformer model
            chunk_size: Words per text chunk
            chunk_overlap: Overlapping words between chunks
            supported_extensions: File extensions to process
        """
        self.document_processor = DocumentProcessor(supported_extensions)
        self.embeddings_manager = EmbeddingsManager(
            model_name=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Track processed documents
        self.processed_documents: List[ProcessedDocument] = []
        
        logger.info("Knowledge base initialized")
    
    def build_from_directories(self, 
                              literature_folder: Path,
                              your_work_folder: Path,
                              current_drafts_folder: Optional[Path] = None) -> Dict[str, Any]:
        """
        Build knowledge base from document directories.
        
        Args:
            literature_folder: Folder containing literature papers
            your_work_folder: Folder containing user's previous work
            current_drafts_folder: Optional folder with current drafts
        
        Returns:
            Dictionary with build statistics
        """
        logger.info("Building knowledge base from directories")
        
        all_documents = []
        
        # Process literature folder
        if literature_folder.exists():
            logger.info(f"Processing literature folder: {literature_folder}")
            lit_docs = self.document_processor.process_directory(
                literature_folder, "literature"
            )
            all_documents.extend(lit_docs)
            logger.info(f"Added {len(lit_docs)} documents from literature")
        else:
            logger.warning(f"Literature folder does not exist: {literature_folder}")
        
        # Process user's work folder
        if your_work_folder.exists():
            logger.info(f"Processing your work folder: {your_work_folder}")
            work_docs = self.document_processor.process_directory(
                your_work_folder, "your_work"
            )
            all_documents.extend(work_docs)
            logger.info(f"Added {len(work_docs)} documents from your work")
        else:
            logger.warning(f"Your work folder does not exist: {your_work_folder}")
        
        # Process current drafts folder if provided
        if current_drafts_folder and current_drafts_folder.exists():
            logger.info(f"Processing drafts folder: {current_drafts_folder}")
            draft_docs = self.document_processor.process_directory(
                current_drafts_folder, "current_drafts"
            )
            all_documents.extend(draft_docs)
            logger.info(f"Added {len(draft_docs)} documents from current drafts")
        
        if not all_documents:
            logger.warning("No documents were found to process")
            return {
                'total_documents': 0,
                'successful_documents': 0,
                'total_chunks': 0
            }
        
        # Store processed documents
        self.processed_documents = all_documents
        
        # Add to embeddings manager
        successful_docs = [doc for doc in all_documents if doc.processing_success]
        self.embeddings_manager.add_documents(successful_docs)
        
        # Get statistics
        stats = self.get_statistics()
        
        logger.info(f"Knowledge base built successfully:")
        logger.info(f"  Total documents: {stats['total_documents']}")
        logger.info(f"  Successful processing: {stats['successful_documents']}")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        
        return stats
    
    def add_document(self, file_path: Path, source_type: str) -> bool:
        """
        Add a single document to the knowledge base.
        
        Args:
            file_path: Path to the document file
            source_type: Type of source (literature, your_work, etc.)
        
        Returns:
            True if document was successfully added
        """
        logger.info(f"Adding single document: {file_path}")
        
        doc = self.document_processor.process_file(file_path, source_type)
        if not doc or not doc.processing_success:
            logger.error(f"Failed to process document: {file_path}")
            return False
        
        # Add to our records
        self.processed_documents.append(doc)
        
        # Add to embeddings
        self.embeddings_manager.add_documents([doc])
        
        logger.info(f"Successfully added document: {file_path}")
        return True
    
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Search the knowledge base for relevant content.
        
        Args:
            query: Search query
            top_k: Maximum number of results to return
        
        Returns:
            List of search results sorted by relevance
        """
        return self.embeddings_manager.search(query, top_k)
    
    def search_with_context(self, 
                           query: str, 
                           conversation_context: str = "",
                           top_k: int = 10) -> List[SearchResult]:
        """
        Search with conversation context for better results.
        
        Args:
            query: Primary search query
            conversation_context: Recent conversation context
            top_k: Maximum results to return
        
        Returns:
            List of search results
        """
        return self.embeddings_manager.search_with_context(
            query, conversation_context, top_k
        )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the knowledge base.
        
        Returns:
            Dictionary with detailed statistics
        """
        # Document processing stats
        doc_stats = self.document_processor.get_processing_stats(self.processed_documents)
        
        # Embedding stats
        embedding_stats = self.embeddings_manager.get_statistics()
        
        # Combine statistics
        combined_stats = {
            'total_documents': doc_stats.get('total_documents', 0),
            'successful_documents': doc_stats.get('successful_extractions', 0),
            'failed_documents': doc_stats.get('failed_extractions', 0),
            'success_rate': doc_stats.get('success_rate', 0),
            'total_words': doc_stats.get('total_words', 0),
            'total_size_mb': doc_stats.get('total_size_mb', 0),
            'avg_words_per_doc': doc_stats.get('avg_words_per_doc', 0),
            'total_chunks': embedding_stats.get('total_chunks', 0),
            'avg_chunk_length': embedding_stats.get('avg_chunk_length', 0),
            'embedding_model': embedding_stats.get('model_info', 'unknown'),
            'source_breakdown': doc_stats.get('source_breakdown', {})
        }
        
        return combined_stats
    
    def save_to_file(self, filepath: Path) -> None:
        """
        Save the knowledge base to disk.
        
        Args:
            filepath: Path where to save the knowledge base
        """
        logger.info(f"Saving knowledge base to {filepath}")
        self.embeddings_manager.save_to_file(filepath)
    
    def load_from_file(self, filepath: Path) -> bool:
        """
        Load knowledge base from disk.
        
        Args:
            filepath: Path to the saved knowledge base
        
        Returns:
            True if loaded successfully
        """
        logger.info(f"Loading knowledge base from {filepath}")
        success = self.embeddings_manager.load_from_file(filepath)
        
        if success:
            # Note: We don't have the original ProcessedDocument objects
            # but we can work with the chunks that were loaded
            logger.info("Knowledge base loaded successfully")
        else:
            logger.error("Failed to load knowledge base")
        
        return success
    
    def clear(self) -> None:
        """Clear all data from the knowledge base."""
        logger.info("Clearing knowledge base")
        self.processed_documents = []
        self.embeddings_manager.clear_database()
    
    def get_document_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific document in the knowledge base.
        
        Args:
            file_path: Path to the document
        
        Returns:
            Dictionary with document information or None if not found
        """
        # Find the document in our processed documents
        doc = None
        for processed_doc in self.processed_documents:
            if processed_doc.file_path == file_path:
                doc = processed_doc
                break
        
        if not doc:
            return None
        
        # Get chunks for this document
        chunks = self.embeddings_manager.get_document_chunks(file_path)
        
        return {
            'file_name': doc.file_name,
            'source_type': doc.source_type,
            'word_count': doc.word_count,
            'file_size_mb': doc.file_size_mb,
            'processing_success': doc.processing_success,
            'error_message': doc.error_message,
            'chunk_count': len(chunks)
        }
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """
        List all documents in the knowledge base.
        
        Returns:
            List of dictionaries with document information
        """
        documents_info = []
        
        for doc in self.processed_documents:
            if doc.processing_success:
                chunks = self.embeddings_manager.get_document_chunks(doc.file_path)
                documents_info.append({
                    'file_name': doc.file_name,
                    'file_path': doc.file_path,
                    'source_type': doc.source_type,
                    'word_count': doc.word_count,
                    'chunk_count': len(chunks)
                })
        
        return documents_info
    
    def get_source_summary(self) -> Dict[str, Dict[str, Any]]:
        """
        Get summary statistics by source type.
        
        Returns:
            Dictionary with source type summaries
        """
        source_summary = {}
        
        for doc in self.processed_documents:
            source_type = doc.source_type
            
            if source_type not in source_summary:
                source_summary[source_type] = {
                    'document_count': 0,
                    'successful_count': 0,
                    'total_words': 0,
                    'total_size_mb': 0
                }
            
            source_summary[source_type]['document_count'] += 1
            source_summary[source_type]['total_size_mb'] += doc.file_size_mb
            
            if doc.processing_success:
                source_summary[source_type]['successful_count'] += 1
                source_summary[source_type]['total_words'] += doc.word_count
        
        return source_summary