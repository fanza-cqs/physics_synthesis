#!/usr/bin/env python3
"""
Base embeddings functionality for the Physics Literature Synthesis Pipeline.

This file contains the original EmbeddingsManager functionality, moved from
src/core/embeddings.py during Phase 1A restructuring.

Creates and manages vector embeddings for semantic search over physics literature.
Uses sentence transformers for creating high-quality embeddings of scientific text.
"""

import pickle
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from ..document_processor import ProcessedDocument
from ...utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class DocumentChunk:
    """Container for a text chunk with metadata."""
    chunk_id: int
    file_path: str
    file_name: str
    source_type: str
    text: str
    chunk_index: int
    total_chunks: int
    full_document_text: str

@dataclass
class SearchResult:
    """Container for search results with relevance scores."""
    chunk: DocumentChunk
    similarity_score: float

class EmbeddingsManager:
    """
    Manages document embeddings for semantic search.
    
    Handles text chunking, embedding creation, and similarity search
    optimized for physics literature.
    
    Note: This is the base implementation moved from the original embeddings.py.
    Enhanced versions with improved chunking strategies will be added in Phase 1B.
    """
    
    def __init__(self, 
                 model_name: str = "all-MiniLM-L6-v2",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the embeddings manager.
        
        Args:
            model_name: Name of the sentence transformer model
            chunk_size: Number of words per chunk
            chunk_overlap: Number of overlapping words between chunks
        """
        self.model_name = model_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Storage for chunks and embeddings
        self.chunks: List[DocumentChunk] = []
        self.embeddings: Optional[np.ndarray] = None
        
        logger.info(f"Embeddings manager initialized with {model_name}")
    
    def chunk_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks for better context preservation.
        
        Args:
            text: Input text to chunk
        
        Returns:
            List of text chunks
        """
        if not text.strip():
            return []
        
        words = text.split()
        if len(words) <= self.chunk_size:
            return [text]
        
        chunks = []
        start_idx = 0
        
        while start_idx < len(words):
            # Calculate end index for this chunk
            end_idx = min(start_idx + self.chunk_size, len(words))
            
            # Create chunk from words
            chunk_words = words[start_idx:end_idx]
            chunk_text = ' '.join(chunk_words)
            
            if chunk_text.strip():
                chunks.append(chunk_text)
            
            # Move start index, accounting for overlap
            if end_idx >= len(words):
                break
            start_idx = end_idx - self.chunk_overlap
        
        logger.debug(f"Chunked text into {len(chunks)} chunks")
        return chunks
    
    def add_documents(self, documents: List[ProcessedDocument]) -> None:
        """
        Add documents to the embeddings database.
        
        Args:
            documents: List of processed documents to add
        """
        logger.info(f"Adding {len(documents)} documents to embeddings database")
        
        new_chunks = []
        chunk_id_counter = len(self.chunks)
        
        for doc in documents:
            if not doc.processing_success or not doc.text.strip():
                logger.warning(f"Skipping document with no text: {doc.file_name}")
                continue
            
            # Split document into chunks
            text_chunks = self.chunk_text(doc.text)
            
            # Create DocumentChunk objects
            for chunk_index, chunk_text in enumerate(text_chunks):
                chunk = DocumentChunk(
                    chunk_id=chunk_id_counter,
                    file_path=doc.file_path,
                    file_name=doc.file_name,
                    source_type=doc.source_type,
                    text=chunk_text,
                    chunk_index=chunk_index,
                    total_chunks=len(text_chunks),
                    full_document_text=doc.text
                )
                new_chunks.append(chunk)
                chunk_id_counter += 1
            
            logger.debug(f"Created {len(text_chunks)} chunks for {doc.file_name}")
        
        # Add new chunks to storage
        self.chunks.extend(new_chunks)
        
        # Create embeddings for new chunks
        if new_chunks:
            logger.info(f"Creating embeddings for {len(new_chunks)} new chunks")
            new_texts = [chunk.text for chunk in new_chunks]
            new_embeddings = self.model.encode(new_texts, show_progress_bar=True)
            
            # Combine with existing embeddings
            if self.embeddings is not None:
                self.embeddings = np.vstack([self.embeddings, new_embeddings])
            else:
                self.embeddings = new_embeddings
        
        logger.info(f"Total chunks in database: {len(self.chunks)}")
    
    def search(self, query: str, top_k: int = 10) -> List[SearchResult]:
        """
        Search for semantically similar chunks using cosine similarity.
        
        Args:
            query: Search query
            top_k: Number of top results to return
        
        Returns:
            List of search results sorted by similarity score
        """
        if not self.chunks or self.embeddings is None:
            logger.warning("No documents in embeddings database")
            return []
        
        # Create query embedding
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top results
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            result = SearchResult(
                chunk=self.chunks[idx],
                similarity_score=float(similarities[idx])
            )
            results.append(result)
        
        logger.debug(f"Found {len(results)} results for query: {query[:50]}...")
        return results
    
    def get_statistics(self) -> Dict[str, any]:
        """
        Get statistics about the embeddings database.
        
        Returns:
            Dictionary with database statistics
        """
        if not self.chunks:
            return {
                'total_chunks': 0,
                'total_documents': 0,
                'avg_chunk_length': 0,
                'model_info': self.model_name,
                'chunk_size': self.chunk_size,
                'chunk_overlap': self.chunk_overlap
            }
        
        # Calculate statistics
        unique_files = set(chunk.file_path for chunk in self.chunks)
        chunk_lengths = [len(chunk.text.split()) for chunk in self.chunks]
        avg_length = sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0
        
        return {
            'total_chunks': len(self.chunks),
            'total_documents': len(unique_files),
            'avg_chunk_length': round(avg_length, 2),
            'model_info': self.model_name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'last_updated': getattr(self, 'last_updated', None)
        }
    
    def save_to_file(self, filepath: Path) -> None:
        """
        Save embeddings to disk.
        
        Args:
            filepath: Path to save embeddings
        """
        logger.info(f"Saving embeddings to {filepath}")
        
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'chunks': self.chunks,
            'embeddings': self.embeddings,
            'model_name': self.model_name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info("Embeddings saved successfully")
    
    def load_from_file(self, filepath: Path) -> bool:
        """
        Load embeddings from disk.
        
        Args:
            filepath: Path to load embeddings from
            
        Returns:
            True if loaded successfully, False otherwise
        """
        if not filepath.exists():
            logger.warning(f"Embeddings file does not exist: {filepath}")
            return False
            
        logger.info(f"Loading embeddings from {filepath}")
        
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.chunks = data['chunks']
            self.embeddings = data['embeddings']
            
            # Verify model compatibility
            saved_model = data.get('model_name', 'unknown')
            if saved_model != self.model_name:
                logger.warning(f"Model mismatch: saved={saved_model}, current={self.model_name}")
            
            # Update chunk configuration if available
            self.chunk_size = data.get('chunk_size', self.chunk_size)
            self.chunk_overlap = data.get('chunk_overlap', self.chunk_overlap)
            
            logger.info(f"Loaded {len(self.chunks)} chunks and embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return False
    
    # Also add the alternative method names for backward compatibility
    def save_embeddings(self, filepath: Path) -> None:
        """Backward compatibility alias for save_to_file."""
        self.save_to_file(filepath)
    
    def load_embeddings(self, filepath: Path) -> bool:
        """Backward compatibility alias for load_from_file."""
        return self.load_from_file(filepath)
    
    def clear_database(self) -> None:
        """Clear all chunks and embeddings from memory."""
        logger.info("Clearing embeddings database")
        self.chunks = []
        self.embeddings = None
    
    def get_document_chunks(self, file_path: str) -> List[DocumentChunk]:
        """
        Get all chunks for a specific document.
        
        Args:
            file_path: Path to the document
        
        Returns:
            List of chunks for the specified document
        """
        return [chunk for chunk in self.chunks if chunk.file_path == file_path]
    
    def search_with_context(self, 
                           query: str, 
                           conversation_context: str = "", 
                           top_k: int = 10) -> List[SearchResult]:
        """
        Search for semantically similar chunks with conversation context.
        
        Args:
            query: Primary search query
            conversation_context: Recent conversation context
            top_k: Number of top results to return
        
        Returns:
            List of search results sorted by similarity score
        """
        # For now, just use the main query (context integration can be enhanced in Phase 1B)
        return self.search(query, top_k)