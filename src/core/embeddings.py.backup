#!/usr/bin/env python3
"""
Embeddings module for the Physics Literature Synthesis Pipeline.

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

from .document_processor import ProcessedDocument
from ..utils.logging_config import get_logger

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
            query: Search query text
            top_k: Number of top results to return
        
        Returns:
            List of SearchResult objects sorted by relevance
        """
        if self.embeddings is None or len(self.chunks) == 0:
            logger.warning("No embeddings available for search")
            return []
        
        logger.debug(f"Searching for: '{query[:50]}...' (top_k={top_k})")
        
        # Create query embedding
        query_embedding = self.model.encode([query])
        
        # Calculate similarities
        similarities = cosine_similarity(query_embedding, self.embeddings)[0]
        
        # Get top-k indices
        top_indices = np.argsort(similarities)[-top_k:][::-1]
        
        # Create search results
        results = []
        for idx in top_indices:
            if idx < len(self.chunks):  # Safety check
                result = SearchResult(
                    chunk=self.chunks[idx],
                    similarity_score=similarities[idx]
                )
                results.append(result)
        
        logger.debug(f"Found {len(results)} search results")
        return results
    
    def search_with_context(self, 
                           query: str, 
                           conversation_context: str = "",
                           top_k: int = 10) -> List[SearchResult]:
        """
        Search with additional context from conversation history.
        
        Args:
            query: Primary search query
            conversation_context: Recent conversation context
            top_k: Number of results to return
        
        Returns:
            List of SearchResult objects
        """
        # Combine query with context for better search
        if conversation_context.strip():
            enhanced_query = f"{query} {conversation_context[:200]}"
        else:
            enhanced_query = query
        
        return self.search(enhanced_query, top_k)
    
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
                'source_breakdown': {},
                'model_info': self.model_name
            }
        
        # Count unique documents
        unique_files = set(chunk.file_path for chunk in self.chunks)
        
        # Source breakdown
        source_breakdown = {}
        for chunk in self.chunks:
            source = chunk.source_type
            if source not in source_breakdown:
                source_breakdown[source] = {
                    'chunks': 0,
                    'documents': set()
                }
            source_breakdown[source]['chunks'] += 1
            source_breakdown[source]['documents'].add(chunk.file_path)
        
        # Convert document sets to counts
        for source_data in source_breakdown.values():
            source_data['documents'] = len(source_data['documents'])
        
        stats = {
            'total_chunks': len(self.chunks),
            'total_documents': len(unique_files),
            'source_breakdown': source_breakdown,
            'avg_chunk_length': np.mean([len(chunk.text.split()) for chunk in self.chunks]),
            'model_info': self.model_name,
            'embeddings_shape': self.embeddings.shape if self.embeddings is not None else None
        }
        
        return stats
    
    def save_to_file(self, filepath: Path) -> None:
        """
        Save the embeddings database to disk.
        
        Args:
            filepath: Path where to save the database
        """
        logger.info(f"Saving embeddings database to {filepath}")
        
        # Prepare data for serialization
        save_data = {
            'chunks': self.chunks,
            'embeddings': self.embeddings,
            'model_name': self.model_name,
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap
        }
        
        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Save with pickle
        try:
            with open(filepath, 'wb') as f:
                pickle.dump(save_data, f)
            logger.info(f"Successfully saved {len(self.chunks)} chunks to {filepath}")
        except Exception as e:
            logger.error(f"Error saving embeddings database: {e}")
            raise
    
    def load_from_file(self, filepath: Path) -> bool:
        """
        Load embeddings database from disk.
        
        Args:
            filepath: Path to the saved database
        
        Returns:
            True if loaded successfully, False otherwise
        """
        if not filepath.exists():
            logger.warning(f"Embeddings file does not exist: {filepath}")
            return False
        
        logger.info(f"Loading embeddings database from {filepath}")
        
        try:
            with open(filepath, 'rb') as f:
                save_data = pickle.load(f)
            
            # Restore data
            self.chunks = save_data['chunks']
            self.embeddings = save_data['embeddings']
            
            # Check if model configuration matches
            saved_model = save_data.get('model_name', 'unknown')
            if saved_model != self.model_name:
                logger.warning(
                    f"Model mismatch: saved={saved_model}, current={self.model_name}"
                )
            
            self.chunk_size = save_data.get('chunk_size', self.chunk_size)
            self.chunk_overlap = save_data.get('chunk_overlap', self.chunk_overlap)
            
            logger.info(f"Successfully loaded {len(self.chunks)} chunks from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading embeddings database: {e}")
            return False
    
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