#!/usr/bin/env python3
"""
Enhanced Knowledge base module for the Physics Literature Synthesis Pipeline.

High-level interface for building and managing multiple named literature knowledge bases.
Coordinates document processing and embedding creation with organized storage.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import time
import json

from .document_processor import DocumentProcessor, ProcessedDocument
from .embeddings import EmbeddingsManager, SearchResult
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class KnowledgeBase:
    """
    High-level knowledge base for physics literature with named storage support.
    
    Manages the entire pipeline from document processing to semantic search,
    with support for multiple named knowledge bases stored in organized folders.
    """
    
    def __init__(self, 
                 name: str = "default",
                 base_storage_dir: Path = None,
                 embedding_model: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200,
                 supported_extensions: set = None):
        """
        Initialize the knowledge base.
        
        Args:
            name: Name of this knowledge base (used for storage)
            base_storage_dir: Base directory for storing knowledge bases
            embedding_model: Name of the sentence transformer model
            chunk_size: Words per text chunk
            chunk_overlap: Overlapping words between chunks
            supported_extensions: File extensions to process
        """
        self.name = name
        self.base_storage_dir = base_storage_dir or Path("knowledge_bases")
        self.kb_dir = self.base_storage_dir / name
        
        # Create knowledge base directory
        self.kb_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage paths
        self.embeddings_file = self.kb_dir / f"{name}_embeddings.pkl"
        self.metadata_file = self.kb_dir / f"{name}_metadata.json"
        self.config_file = self.kb_dir / f"{name}_config.json"
        
        self.document_processor = DocumentProcessor(supported_extensions)
        self.embeddings_manager = EmbeddingsManager(
            model_name=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        # Track processed documents
        self.processed_documents: List[ProcessedDocument] = []
        
        # Store configuration
        self.config = {
            'name': name,
            'embedding_model': embedding_model,
            'chunk_size': chunk_size,
            'chunk_overlap': chunk_overlap,
            'created_at': time.time(),
            'last_updated': time.time()
        }
        
        # Try to load existing knowledge base
        self._try_load_existing()
        
        logger.info(f"Knowledge base '{name}' initialized in {self.kb_dir}")
    
    def _try_load_existing(self) -> bool:
        """Try to load existing knowledge base if it exists."""
        if self.embeddings_file.exists() and self.metadata_file.exists():
            try:
                logger.info(f"Found existing knowledge base '{self.name}', loading...")
                success = self.load_from_storage()
                if success:
                    logger.info(f"Successfully loaded existing knowledge base '{self.name}'")
                    return True
                else:
                    logger.warning(f"Failed to load existing knowledge base '{self.name}'")
            except Exception as e:
                logger.warning(f"Error loading existing knowledge base: {e}")
        return False
    
    def build_from_directories(self, 
                              literature_folder: Optional[Path] = None,
                              your_work_folder: Optional[Path] = None,
                              current_drafts_folder: Optional[Path] = None,
                              manual_references_folder: Optional[Path] = None,
                              zotero_folder: Optional[Path] = None,
                              force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Build knowledge base from document directories.
        
        Args:
            literature_folder: Folder containing literature papers
            your_work_folder: Folder containing user's previous work
            current_drafts_folder: Optional folder with current drafts
            manual_references_folder: Optional folder with manually added references
            zotero_folder: Optional folder with Zotero-synced papers
            force_rebuild: Force rebuild even if KB exists
        
        Returns:
            Dictionary with build statistics
        """
        logger.info(f"Building knowledge base '{self.name}' from directories")
        
        # Check if we should skip building (unless forced)
        if not force_rebuild and self.embeddings_file.exists() and len(self.processed_documents) > 0:
            logger.info(f"Knowledge base '{self.name}' already exists, use force_rebuild=True to rebuild")
            return self.get_statistics()
        
        # Clear existing data if rebuilding
        if force_rebuild:
            self.clear()
        
        all_documents = []
        
        # Process literature folder
        if literature_folder and literature_folder.exists():
            logger.info(f"Processing literature folder: {literature_folder}")
            lit_docs = self.document_processor.process_directory(
                literature_folder, "literature"
            )
            all_documents.extend(lit_docs)
            logger.info(f"Added {len(lit_docs)} documents from literature")
        else:
            if literature_folder:
                logger.warning(f"Literature folder does not exist: {literature_folder}")
        
        # Process user's work folder
        if your_work_folder and your_work_folder.exists():
            logger.info(f"Processing your work folder: {your_work_folder}")
            work_docs = self.document_processor.process_directory(
                your_work_folder, "your_work"
            )
            all_documents.extend(work_docs)
            logger.info(f"Added {len(work_docs)} documents from your work")
        else:
            if your_work_folder:
                logger.warning(f"Your work folder does not exist: {your_work_folder}")
        
        # Process current drafts folder if provided
        if current_drafts_folder and current_drafts_folder.exists():
            logger.info(f"Processing drafts folder: {current_drafts_folder}")
            draft_docs = self.document_processor.process_directory(
                current_drafts_folder, "current_drafts"
            )
            all_documents.extend(draft_docs)
            logger.info(f"Added {len(draft_docs)} documents from current drafts")
        
        # Process manual references folder if provided
        if manual_references_folder and manual_references_folder.exists():
            logger.info(f"Processing manual references folder: {manual_references_folder}")
            manual_docs = self.document_processor.process_directory(
                manual_references_folder, "manual_references"
            )
            all_documents.extend(manual_docs)
            logger.info(f"Added {len(manual_docs)} documents from manual references")
        
        # Process Zotero folder if provided
        if zotero_folder and zotero_folder.exists():
            logger.info(f"Processing Zotero folder: {zotero_folder}")
            zotero_docs = self.document_processor.process_directory(
                zotero_folder, "zotero_sync"
            )
            all_documents.extend(zotero_docs)
            logger.info(f"Added {len(zotero_docs)} documents from Zotero sync")
        
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
        
        # Update configuration
        self.config['last_updated'] = time.time()
        
        # Save the knowledge base
        self.save_to_storage()
        
        # Get statistics
        stats = self.get_statistics()
        
        logger.info(f"Knowledge base '{self.name}' built successfully:")
        logger.info(f"  Total documents: {stats['total_documents']}")
        logger.info(f"  Successful processing: {stats['successful_documents']}")
        logger.info(f"  Total chunks: {stats['total_chunks']}")
        
        return stats
    
    def add_document(self, file_path: Path, source_type: str = "manual_references") -> bool:
        """
        Add a single document to the knowledge base.
        
        Args:
            file_path: Path to the document file
            source_type: Type of source (defaults to manual_references)
        
        Returns:
            True if document was successfully added
        """
        logger.info(f"Adding single document to '{self.name}': {file_path}")
        
        doc = self.document_processor.process_file(file_path, source_type)
        if not doc or not doc.processing_success:
            logger.error(f"Failed to process document: {file_path}")
            return False
        
        # Add to our records
        self.processed_documents.append(doc)
        
        # Add to embeddings
        self.embeddings_manager.add_documents([doc])
        
        # Update config and save
        self.config['last_updated'] = time.time()
        self.save_to_storage()
        
        logger.info(f"Successfully added document to '{self.name}': {file_path}")
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
    
    def save_to_storage(self) -> None:
        """Save the knowledge base to its designated storage location."""
        logger.info(f"Saving knowledge base '{self.name}' to storage")
        
        try:
            # Save embeddings
            self.embeddings_manager.save_to_file(self.embeddings_file)
            
            # Save metadata
            metadata = {
                'processed_documents': [
                    {
                        'file_path': doc.file_path,
                        'file_name': doc.file_name,
                        'source_type': doc.source_type,
                        'word_count': doc.word_count,
                        'file_size_mb': doc.file_size_mb,
                        'processing_success': doc.processing_success,
                        'error_message': doc.error_message
                    }
                    for doc in self.processed_documents
                ]
            }
            
            with open(self.metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Save configuration
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            
            logger.info(f"Knowledge base '{self.name}' saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving knowledge base '{self.name}': {e}")
            raise
    
    def load_from_storage(self) -> bool:
        """Load knowledge base from its designated storage location."""
        logger.info(f"Loading knowledge base '{self.name}' from storage")
        
        try:
            # Load embeddings
            if not self.embeddings_manager.load_from_file(self.embeddings_file):
                return False
            
            # Load metadata
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Reconstruct processed documents
                self.processed_documents = [
                    ProcessedDocument(
                        file_path=doc_data['file_path'],
                        file_name=doc_data['file_name'],
                        source_type=doc_data['source_type'],
                        text="",  # Text is stored in embeddings
                        word_count=doc_data['word_count'],
                        file_size_mb=doc_data['file_size_mb'],
                        processing_success=doc_data['processing_success'],
                        error_message=doc_data.get('error_message')
                    )
                    for doc_data in metadata['processed_documents']
                ]
            
            # Load configuration
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            
            logger.info(f"Knowledge base '{self.name}' loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error loading knowledge base '{self.name}': {e}")
            return False
    
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
            'name': self.name,
            'storage_location': str(self.kb_dir),
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
            'source_breakdown': doc_stats.get('source_breakdown', {}),
            'created_at': self.config.get('created_at'),
            'last_updated': self.config.get('last_updated')
        }
        
        return combined_stats
    
    def clear(self) -> None:
        """Clear all data from the knowledge base."""
        logger.info(f"Clearing knowledge base '{self.name}'")
        self.processed_documents = []
        self.embeddings_manager.clear_database()
        self.config['last_updated'] = time.time()
    
    def delete(self) -> None:
        """Delete the knowledge base and all its files."""
        logger.info(f"Deleting knowledge base '{self.name}' and all its files")
        
        try:
            # Clear in-memory data
            self.clear()
            
            # Delete files
            if self.embeddings_file.exists():
                self.embeddings_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
            if self.config_file.exists():
                self.config_file.unlink()
            
            # Remove directory if empty
            try:
                self.kb_dir.rmdir()
            except OSError:
                # Directory not empty, leave it
                pass
            
            logger.info(f"Knowledge base '{self.name}' deleted successfully")
            
        except Exception as e:
            logger.error(f"Error deleting knowledge base '{self.name}': {e}")
            raise
    
    # Legacy methods for backward compatibility
    #def save_to_file(self, filepath: Path) -> None:
    #    """Legacy method - redirects to save_to_storage()."""
    #    logger.warning("save_to_file() is deprecated, use save_to_storage() instead")
    #    self.save_to_storage()
    
    #def load_from_file(self, filepath: Path) -> bool:
    #    """Legacy method - redirects to load_from_storage()."""
    #    logger.warning("load_from_file() is deprecated, use load_from_storage() instead")
    #    return self.load_from_storage()
    
    # All other existing methods remain the same...
    def add_manual_reference(self, file_path: Path) -> bool:
        """Add a manually provided reference to the knowledge base."""
        return self.add_document(file_path, "manual_references")
    
    def batch_add_manual_references(self, file_paths: List[Path]) -> Dict[str, int]:
        """Add multiple manual references at once."""
        logger.info(f"Adding {len(file_paths)} manual references to '{self.name}'")
        
        successful = 0
        failed = 0
        
        for file_path in file_paths:
            if self.add_manual_reference(file_path):
                successful += 1
            else:
                failed += 1
        
        logger.info(f"Batch add complete: {successful} successful, {failed} failed")
        
        return {
            'successful': successful,
            'failed': failed,
            'total': len(file_paths)
        }
    
    def get_document_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific document in the knowledge base."""
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
    
    def list_documents(self, source_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all documents in the knowledge base, optionally filtered by source type."""
        documents_info = []
        
        for doc in self.processed_documents:
            if doc.processing_success:
                # Filter by source type if specified
                if source_type and doc.source_type != source_type:
                    continue
                
                chunks = self.embeddings_manager.get_document_chunks(doc.file_path)
                documents_info.append({
                    'file_name': doc.file_name,
                    'file_path': doc.file_path,
                    'source_type': doc.source_type,
                    'word_count': doc.word_count,
                    'chunk_count': len(chunks)
                })
        
        return documents_info
    
    def list_manual_references(self) -> List[Dict[str, Any]]:
        """List all manually added references."""
        return self.list_documents(source_type="manual_references")
    
    def get_source_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary statistics by source type."""
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
    
    def remove_document(self, file_path: str) -> bool:
        """Remove a document from the knowledge base."""
        # Find and remove from processed documents
        original_count = len(self.processed_documents)
        self.processed_documents = [
            doc for doc in self.processed_documents 
            if doc.file_path != file_path
        ]
        
        if len(self.processed_documents) == original_count:
            logger.warning(f"Document not found in knowledge base '{self.name}': {file_path}")
            return False
        
        # Rebuild embeddings without the removed document
        logger.info(f"Rebuilding embeddings after removing {file_path}")
        self.embeddings_manager.clear_database()
        
        successful_docs = [doc for doc in self.processed_documents if doc.processing_success]
        self.embeddings_manager.add_documents(successful_docs)
        
        # Update config and save
        self.config['last_updated'] = time.time()
        self.save_to_storage()
        
        logger.info(f"Successfully removed document from '{self.name}': {file_path}")
        return True


# Utility functions for managing multiple knowledge bases
def list_knowledge_bases(base_storage_dir: Path = None) -> List[Dict[str, Any]]:
    """
    List all available knowledge bases.
    
    Args:
        base_storage_dir: Base directory to search for knowledge bases
    
    Returns:
        List of knowledge base information dictionaries
    """
    base_dir = base_storage_dir or Path("knowledge_bases")
    
    if not base_dir.exists():
        return []
    
    knowledge_bases = []
    
    for kb_dir in base_dir.iterdir():
        if kb_dir.is_dir():
            config_file = kb_dir / f"{kb_dir.name}_config.json"
            if config_file.exists():
                try:
                    with open(config_file, 'r') as f:
                        config = json.load(f)
                    
                    # Get file sizes
                    embeddings_file = kb_dir / f"{kb_dir.name}_embeddings.pkl"
                    metadata_file = kb_dir / f"{kb_dir.name}_metadata.json"
                    
                    total_size = 0
                    if embeddings_file.exists():
                        total_size += embeddings_file.stat().st_size
                    if metadata_file.exists():
                        total_size += metadata_file.stat().st_size
                    
                    knowledge_bases.append({
                        'name': kb_dir.name,
                        'path': str(kb_dir),
                        'created_at': config.get('created_at'),
                        'last_updated': config.get('last_updated'),
                        'embedding_model': config.get('embedding_model'),
                        'size_mb': total_size / (1024 * 1024)
                    })
                    
                except Exception as e:
                    logger.warning(f"Error reading knowledge base config for {kb_dir.name}: {e}")
    
    return sorted(knowledge_bases, key=lambda x: x.get('last_updated', 0), reverse=True)


def create_knowledge_base(name: str, 
                         base_storage_dir: Path = None,
                         **kwargs) -> KnowledgeBase:
    """
    Create a new named knowledge base.
    
    Args:
        name: Name for the knowledge base
        base_storage_dir: Base directory for storage
        **kwargs: Additional arguments for KnowledgeBase constructor
    
    Returns:
        New KnowledgeBase instance
    """
    return KnowledgeBase(name=name, base_storage_dir=base_storage_dir, **kwargs)


def load_knowledge_base(name: str, 
                       base_storage_dir: Path = None) -> Optional[KnowledgeBase]:
    """
    Load an existing knowledge base by name.
    
    Args:
        name: Name of the knowledge base to load
        base_storage_dir: Base directory to search in
    
    Returns:
        Loaded KnowledgeBase instance or None if not found
    """
    base_dir = base_storage_dir or Path("knowledge_bases")
    kb_dir = base_dir / name
    
    if not kb_dir.exists():
        logger.warning(f"Knowledge base '{name}' not found in {base_dir}")
        return None
    
    config_file = kb_dir / f"{name}_config.json"
    if not config_file.exists():
        logger.warning(f"Configuration file not found for knowledge base '{name}'")
        return None
    
    try:
        # Load configuration to get parameters
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Create knowledge base with saved parameters
        kb = KnowledgeBase(
            name=name,
            base_storage_dir=base_dir,
            embedding_model=config.get('embedding_model', 'all-MiniLM-L6-v2'),
            chunk_size=config.get('chunk_size', 1000),
            chunk_overlap=config.get('chunk_overlap', 200)
        )
        
        return kb
        
    except Exception as e:
        logger.error(f"Error loading knowledge base '{name}': {e}")
        return None


def delete_knowledge_base(name: str, base_storage_dir: Path = None) -> bool:
    """
    Delete a knowledge base by name.
    
    Args:
        name: Name of the knowledge base to delete
        base_storage_dir: Base directory to search in
    
    Returns:
        True if deleted successfully
    """
    kb = load_knowledge_base(name, base_storage_dir)
    if kb:
        kb.delete()
        return True
    return False