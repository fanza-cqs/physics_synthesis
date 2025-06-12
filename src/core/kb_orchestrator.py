#!/usr/bin/env python3
"""
Knowledge Base Orchestrator for the Physics Literature Synthesis Pipeline.

Coordinates the creation and updating of knowledge bases from multiple sources
with proper separation of concerns and error handling.

Location: src/core/kb_orchestrator.py
"""

import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .knowledge_base import KnowledgeBase, create_knowledge_base, load_knowledge_base
from .source_processors import (
    LocalFolderProcessor, 
    ZoteroProcessor, 
    CustomFolderProcessor,
    SourceProcessingResult
)
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

class KBOperation(Enum):
    """Knowledge base operation types."""
    CREATE_NEW = "create_new"
    REPLACE_EXISTING = "replace_existing" 
    ADD_TO_EXISTING = "add_to_existing"

@dataclass
class SourceSelection:
    """Configuration for source selection."""
    # Local folders
    use_local_folders: bool = False
    literature_folder: bool = True
    your_work_folder: bool = True
    current_drafts_folder: bool = False
    manual_references_folder: bool = True
    
    # Zotero
    use_zotero: bool = False
    zotero_collections: List[str] = None
    
    # Custom folder
    use_custom_folder: bool = False
    custom_folder_path: Optional[Path] = None
    
    def __post_init__(self):
        if self.zotero_collections is None:
            self.zotero_collections = []

@dataclass
class PreProcessingSummary:
    """Summary of documents found during pre-processing."""
    local_folders_summary: Dict[str, int] = None
    zotero_summary: Dict[str, int] = None
    custom_folder_summary: Dict[str, int] = None
    total_documents: int = 0
    has_valid_sources: bool = False
    error_messages: List[str] = None
    
    def __post_init__(self):
        if self.local_folders_summary is None:
            self.local_folders_summary = {}
        if self.zotero_summary is None:
            self.zotero_summary = {}
        if self.custom_folder_summary is None:
            self.custom_folder_summary = {}
        if self.error_messages is None:
            self.error_messages = []

@dataclass
class OrchestrationResult:
    """Result of knowledge base orchestration."""
    success: bool
    kb_name: str
    kb_path: Optional[str] = None
    total_documents: int = 0
    total_chunks: int = 0
    sources_processed: List[str] = None
    sources_failed: List[str] = None
    is_partial: bool = False
    error_messages: List[str] = None
    processing_time: float = 0.0
    
    def __post_init__(self):
        if self.sources_processed is None:
            self.sources_processed = []
        if self.sources_failed is None:
            self.sources_failed = []
        if self.error_messages is None:
            self.error_messages = []

class KnowledgeBaseOrchestrator:
    """
    Orchestrates knowledge base creation and updates from multiple sources.
    
    Coordinates local folders, Zotero collections, and custom folders while
    maintaining separation of concerns and providing comprehensive error handling.
    """
    
    def __init__(self, config):
        """
        Initialize the orchestrator.
        
        Args:
            config: PipelineConfig instance
        """
        self.config = config
        self.progress_callback: Optional[Callable[[str, float], None]] = None
        
        # Initialize source processors
        self.local_processor = LocalFolderProcessor(config)
        self.zotero_processor = ZoteroProcessor(config)
        self.custom_processor = CustomFolderProcessor(config)
        
        logger.info("Knowledge Base Orchestrator initialized")
    
    def set_progress_callback(self, callback: Callable[[str, float], None]):
        """Set callback function for progress updates."""
        self.progress_callback = callback
    
    def _update_progress(self, message: str, progress: float):
        """Update progress if callback is set."""
        if self.progress_callback:
            self.progress_callback(message, progress)
        logger.info(f"Progress: {progress:.1f}% - {message}")
    
    def preprocess_sources(self, 
                          source_selection: SourceSelection) -> PreProcessingSummary:
        """
        Scan selected sources and generate summary of available documents.
        
        Args:
            source_selection: Configuration of sources to scan
            
        Returns:
            PreProcessingSummary with document counts and validation
        """
        logger.info("Starting pre-processing source scan")
        self._update_progress("Scanning sources...", 0.0)
        
        summary = PreProcessingSummary()
        total_docs = 0
        
        try:
            # Scan local folders
            if source_selection.use_local_folders:
                self._update_progress("Scanning local folders...", 10.0)
                local_result = self.local_processor.scan_sources(source_selection)
                summary.local_folders_summary = local_result.document_counts
                total_docs += sum(local_result.document_counts.values())
                
                if local_result.error_message:
                    summary.error_messages.append(f"Local folders: {local_result.error_message}")
            
            # Scan Zotero collections
            if source_selection.use_zotero:
                self._update_progress("Scanning Zotero collections...", 40.0)
                zotero_result = self.zotero_processor.scan_sources(source_selection)
                summary.zotero_summary = zotero_result.document_counts
                total_docs += sum(zotero_result.document_counts.values())
                
                if zotero_result.error_message:
                    summary.error_messages.append(f"Zotero: {zotero_result.error_message}")
            
            # Scan custom folder
            if source_selection.use_custom_folder:
                self._update_progress("Scanning custom folder...", 70.0)
                custom_result = self.custom_processor.scan_sources(source_selection)
                summary.custom_folder_summary = custom_result.document_counts
                total_docs += sum(custom_result.document_counts.values())
                
                if custom_result.error_message:
                    summary.error_messages.append(f"Custom folder: {custom_result.error_message}")
            
            summary.total_documents = total_docs
            summary.has_valid_sources = total_docs > 0
            
            self._update_progress("Source scan complete", 100.0)
            logger.info(f"Pre-processing complete: {total_docs} documents found")
            
        except Exception as e:
            logger.error(f"Error during pre-processing: {e}")
            summary.error_messages.append(f"Pre-processing error: {str(e)}")
        
        return summary
    
    def create_knowledge_base(self,
                             kb_name: str,
                             source_selection: SourceSelection,
                             operation: KBOperation = KBOperation.CREATE_NEW,
                             existing_kb_name: Optional[str] = None,
                             force_rebuild: bool = False) -> OrchestrationResult:
        """
        Create or update a knowledge base from selected sources.
        
        Args:
            kb_name: Name for the new knowledge base
            source_selection: Configuration of sources to use
            operation: Type of operation (create/replace/add)
            existing_kb_name: Name of existing KB (for replace/add operations)
            force_rebuild: Force rebuild even if KB exists
            
        Returns:
            OrchestrationResult with operation details
        """
        start_time = time.time()
        logger.info(f"Starting KB orchestration: {operation.value} - {kb_name}")
        
        result = OrchestrationResult(
            success=False,
            kb_name=kb_name
        )
        
        try:
            # Validate inputs
            validation_error = self._validate_inputs(kb_name, source_selection, operation, existing_kb_name)
            if validation_error:
                result.error_messages.append(validation_error)
                return result
            
            # Pre-process to ensure we have valid sources
            self._update_progress("Validating sources...", 5.0)
            preprocessing = self.preprocess_sources(source_selection)
            
            if not preprocessing.has_valid_sources:
                result.error_messages.append("No valid documents found in selected sources")
                return result
            
            # Initialize or load knowledge base
            kb = self._setup_knowledge_base(kb_name, operation, existing_kb_name, force_rebuild)
            if not kb:
                result.error_messages.append("Failed to initialize knowledge base")
                return result
            
            # Process sources in order: Local → Zotero → Custom
            sources_to_process = self._determine_processing_order(source_selection)
            total_sources = len(sources_to_process)
            
            for i, source_type in enumerate(sources_to_process):
                base_progress = 20.0 + (i * 60.0 / total_sources)
                source_progress = 60.0 / total_sources
                
                success = self._process_source(
                    kb, source_type, source_selection, 
                    base_progress, source_progress, result
                )
                
                if success:
                    result.sources_processed.append(source_type)
                else:
                    result.sources_failed.append(source_type)
            
            # Finalize knowledge base
            self._update_progress("Finalizing knowledge base...", 85.0)
            
            # Handle partial creation
            if result.sources_failed and result.sources_processed:
                result.is_partial = True
                # Add _partial suffix to name
                original_name = kb.name
                partial_name = f"{original_name}_partial"
                
                # Create new KB with partial name
                partial_kb = create_knowledge_base(
                    name=partial_name,
                    base_storage_dir=kb.base_storage_dir,
                    embedding_model=kb.config['embedding_model'],
                    chunk_size=kb.config['chunk_size'],
                    chunk_overlap=kb.config['chunk_overlap']
                )
                
                # Copy data to partial KB
                partial_kb.processed_documents = kb.processed_documents
                partial_kb.embeddings_manager = kb.embeddings_manager
                partial_kb.save_to_storage()
                
                kb = partial_kb
                result.kb_name = partial_name
            
            # Save final knowledge base
            kb.save_to_storage()
            
            # Get final statistics
            stats = kb.get_statistics()
            result.kb_path = str(kb.kb_dir)
            result.total_documents = stats['total_documents']
            result.total_chunks = stats['total_chunks']
            result.success = True
            
            self._update_progress("Knowledge base creation complete!", 100.0)
            
            logger.info(f"KB orchestration complete: {result.kb_name}")
            logger.info(f"  Documents: {result.total_documents}")
            logger.info(f"  Chunks: {result.total_chunks}")
            logger.info(f"  Sources processed: {result.sources_processed}")
            if result.sources_failed:
                logger.warning(f"  Sources failed: {result.sources_failed}")
            
        except Exception as e:
            logger.error(f"Error during KB orchestration: {e}")
            result.error_messages.append(f"Orchestration error: {str(e)}")
        
        finally:
            result.processing_time = time.time() - start_time
        
        return result
    
    def _validate_inputs(self, 
                        kb_name: str, 
                        source_selection: SourceSelection,
                        operation: KBOperation,
                        existing_kb_name: Optional[str]) -> Optional[str]:
        """Validate inputs for KB creation."""
        if not kb_name or not kb_name.strip():
            return "Knowledge base name cannot be empty"
        
        if operation in [KBOperation.REPLACE_EXISTING, KBOperation.ADD_TO_EXISTING]:
            if not existing_kb_name:
                return "Existing KB name required for replace/add operations"
        
        # Check if at least one source is selected
        if not (source_selection.use_local_folders or 
                source_selection.use_zotero or 
                source_selection.use_custom_folder):
            return "At least one source must be selected"
        
        return None
    
    def _setup_knowledge_base(self, 
                             kb_name: str,
                             operation: KBOperation,
                             existing_kb_name: Optional[str],
                             force_rebuild: bool) -> Optional[KnowledgeBase]:
        """Set up knowledge base based on operation type."""
        try:
            if operation == KBOperation.CREATE_NEW:
                # Create new empty knowledge base
                kb_config = self.config.get_knowledge_base_config(kb_name)
                return create_knowledge_base(
                    name=kb_name,
                    base_storage_dir=self.config.knowledge_bases_folder,
                    embedding_model=kb_config.embedding_model,
                    chunk_size=kb_config.chunk_size,
                    chunk_overlap=kb_config.chunk_overlap
                )
            
            elif operation == KBOperation.REPLACE_EXISTING:
                # Load existing and clear it
                kb = load_knowledge_base(existing_kb_name, self.config.knowledge_bases_folder)
                if kb:
                    kb.clear()
                    # Rename to new name if different
                    if kb_name != existing_kb_name:
                        kb.name = kb_name
                        kb.config['name'] = kb_name
                    return kb
                else:
                    logger.error(f"Could not load existing KB: {existing_kb_name}")
                    return None
            
            elif operation == KBOperation.ADD_TO_EXISTING:
                # Load existing KB to add to
                kb = load_knowledge_base(existing_kb_name, self.config.knowledge_bases_folder)
                if kb:
                    # Create new KB with combined name if different
                    if kb_name != existing_kb_name:
                        combined_name = f"{existing_kb_name}_{kb_name}"
                        new_kb = create_knowledge_base(
                            name=combined_name,
                            base_storage_dir=self.config.knowledge_bases_folder,
                            embedding_model=kb.config['embedding_model'],
                            chunk_size=kb.config['chunk_size'],
                            chunk_overlap=kb.config['chunk_overlap']
                        )
                        # Copy existing data
                        new_kb.processed_documents = kb.processed_documents.copy()
                        new_kb.embeddings_manager = kb.embeddings_manager
                        return new_kb
                    return kb
                else:
                    logger.error(f"Could not load existing KB: {existing_kb_name}")
                    return None
            
        except Exception as e:
            logger.error(f"Error setting up knowledge base: {e}")
            return None
    
    def _determine_processing_order(self, source_selection: SourceSelection) -> List[str]:
        """Determine order of source processing."""
        order = []
        
        if source_selection.use_local_folders:
            order.append("local_folders")
        
        if source_selection.use_zotero:
            order.append("zotero")
        
        if source_selection.use_custom_folder:
            order.append("custom_folder")
        
        return order
    
    def _process_source(self,
                       kb: KnowledgeBase,
                       source_type: str,
                       source_selection: SourceSelection,
                       base_progress: float,
                       source_progress: float,
                       result: OrchestrationResult) -> bool:
        """Process a single source and update KB."""
        try:
            self._update_progress(f"Processing {source_type}...", base_progress)
            
            if source_type == "local_folders":
                processor_result = self.local_processor.process_source(kb, source_selection)
            elif source_type == "zotero":
                processor_result = self.zotero_processor.process_source(kb, source_selection)
            elif source_type == "custom_folder":
                processor_result = self.custom_processor.process_source(kb, source_selection)
            else:
                logger.error(f"Unknown source type: {source_type}")
                return False
            
            if processor_result.success:
                self._update_progress(f"Completed {source_type}", base_progress + source_progress)
                logger.info(f"Successfully processed {source_type}: {processor_result.documents_added} documents")
                return True
            else:
                error_msg = f"Failed to process {source_type}: {processor_result.error_message}"
                result.error_messages.append(error_msg)
                logger.error(error_msg)
                return False
        
        except Exception as e:
            error_msg = f"Exception processing {source_type}: {str(e)}"
            result.error_messages.append(error_msg)
            logger.error(error_msg)
            return False