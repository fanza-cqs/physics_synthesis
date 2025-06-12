#!/usr/bin/env python3
"""
Knowledge Base validation utilities for pre-processing and validation.

Location: src/utils/kb_validation.py
"""

from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

from .logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    """Result of validation checks."""
    is_valid: bool
    error_messages: List[str] = None
    warning_messages: List[str] = None
    
    def __post_init__(self):
        if self.error_messages is None:
            self.error_messages = []
        if self.warning_messages is None:
            self.warning_messages = []

def validate_kb_name(kb_name: str) -> ValidationResult:
    """
    Validate knowledge base name.
    
    Args:
        kb_name: Name to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True)
    
    if not kb_name or not kb_name.strip():
        result.is_valid = False
        result.error_messages.append("Knowledge base name cannot be empty")
        return result
    
    # Clean the name
    clean_name = kb_name.strip()
    
    # Check for invalid characters
    invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    found_invalid = [char for char in invalid_chars if char in clean_name]
    
    if found_invalid:
        result.is_valid = False
        result.error_messages.append(f"Knowledge base name contains invalid characters: {', '.join(found_invalid)}")
    
    # Check length
    if len(clean_name) > 100:
        result.is_valid = False
        result.error_messages.append("Knowledge base name is too long (max 100 characters)")
    
    # Check for reserved names
    reserved_names = ['con', 'prn', 'aux', 'nul', 'com1', 'com2', 'lpt1', 'lpt2']
    if clean_name.lower() in reserved_names:
        result.is_valid = False
        result.error_messages.append(f"'{clean_name}' is a reserved name")
    
    # Warnings
    if clean_name != kb_name:
        result.warning_messages.append("Knowledge base name will be trimmed of whitespace")
    
    if ' ' in clean_name:
        result.warning_messages.append("Spaces in names may cause issues - consider using underscores")
    
    return result

def validate_source_selection(source_selection) -> ValidationResult:
    """
    Validate source selection configuration.
    
    Args:
        source_selection: SourceSelection object to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True)
    
    # Check if at least one source is selected
    sources_selected = (
        source_selection.use_local_folders or
        source_selection.use_zotero or
        source_selection.use_custom_folder
    )
    
    if not sources_selected:
        result.is_valid = False
        result.error_messages.append("At least one source must be selected")
        return result
    
    # Validate local folders selection
    if source_selection.use_local_folders:
        local_folders_selected = (
            source_selection.literature_folder or
            source_selection.your_work_folder or
            source_selection.current_drafts_folder or
            source_selection.manual_references_folder
        )
        
        if not local_folders_selected:
            result.is_valid = False
            result.error_messages.append("If using local folders, at least one folder must be selected")
    
    # Validate Zotero selection
    if source_selection.use_zotero:
        if not source_selection.zotero_collections:
            result.is_valid = False
            result.error_messages.append("If using Zotero, at least one collection must be selected")
    
    # Validate custom folder
    if source_selection.use_custom_folder:
        if not source_selection.custom_folder_path:
            result.is_valid = False
            result.error_messages.append("If using custom folder, a folder path must be provided")
        elif not Path(source_selection.custom_folder_path).exists():
            result.is_valid = False
            result.error_messages.append(f"Custom folder does not exist: {source_selection.custom_folder_path}")
    
    return result

def validate_existing_kb(kb_name: str, kb_storage_dir: Path) -> ValidationResult:
    """
    Validate that an existing knowledge base can be loaded.
    
    Args:
        kb_name: Name of existing knowledge base
        kb_storage_dir: Directory where knowledge bases are stored
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True)
    
    if not kb_name:
        result.is_valid = False
        result.error_messages.append("Existing knowledge base name cannot be empty")
        return result
    
    kb_dir = kb_storage_dir / kb_name
    
    if not kb_dir.exists():
        result.is_valid = False
        result.error_messages.append(f"Knowledge base '{kb_name}' does not exist")
        return result
    
    # Check for required files
    required_files = [
        kb_dir / f"{kb_name}_config.json",
        kb_dir / f"{kb_name}_metadata.json",
        kb_dir / f"{kb_name}_embeddings.pkl"
    ]
    
    missing_files = [f.name for f in required_files if not f.exists()]
    
    if missing_files:
        result.is_valid = False
        result.error_messages.append(f"Knowledge base '{kb_name}' is missing files: {', '.join(missing_files)}")
    
    return result

def validate_folder_permissions(folder_path: Path) -> ValidationResult:
    """
    Validate that a folder has proper read permissions.
    
    Args:
        folder_path: Path to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult(is_valid=True)
    
    if not folder_path.exists():
        result.is_valid = False
        result.error_messages.append(f"Folder does not exist: {folder_path}")
        return result
    
    if not folder_path.is_dir():
        result.is_valid = False
        result.error_messages.append(f"Path is not a directory: {folder_path}")
        return result
    
    try:
        # Test read access
        list(folder_path.iterdir())
    except PermissionError:
        result.is_valid = False
        result.error_messages.append(f"No read permission for folder: {folder_path}")
    except Exception as e:
        result.is_valid = False
        result.error_messages.append(f"Error accessing folder {folder_path}: {str(e)}")
    
    return result

def check_zotero_availability(config) -> Tuple[bool, Optional[str]]:
    """
    Check if Zotero integration is available and properly configured.
    
    Args:
        config: PipelineConfig instance
        
    Returns:
        Tuple of (is_available, error_message)
    """
    try:
        api_status = config.check_env_file()
        
        if not api_status.get('zotero_configured', False):
            return False, "Zotero not configured - missing API key or library ID"
        
        # Try to create a syncer to test connection
        from ..downloaders import create_literature_syncer
        syncer = create_literature_syncer(config)
        
        # Test connection by getting collections
        collections = syncer.zotero_manager.get_collections()
        
        return True, None
        
    except Exception as e:
        return False, f"Zotero connection error: {str(e)}"

def generate_summary_text(preprocessing_summary) -> str:
    """
    Generate human-readable summary text from preprocessing results.
    
    Args:
        preprocessing_summary: PreProcessingSummary object
        
    Returns:
        Formatted summary string
    """
    lines = []
    
    lines.append(f"📊 **Document Summary**")
    lines.append(f"Total documents found: **{preprocessing_summary.total_documents}**")
    lines.append("")
    
    # Local folders summary
    if preprocessing_summary.local_folders_summary:
        lines.append("📁 **Local Folders:**")
        for folder, count in preprocessing_summary.local_folders_summary.items():
            lines.append(f"   • {folder}: {count} documents")
        lines.append("")
    
    # Zotero summary
    if preprocessing_summary.zotero_summary:
        lines.append("🔗 **Zotero Collections:**")
        for collection, count in preprocessing_summary.zotero_summary.items():
            lines.append(f"   • {collection}: {count} items")
        lines.append("")
    
    # Custom folder summary
    if preprocessing_summary.custom_folder_summary:
        lines.append("📂 **Custom Folder:**")
        for folder, count in preprocessing_summary.custom_folder_summary.items():
            lines.append(f"   • {folder}: {count} documents")
        lines.append("")
    
    # Errors and warnings
    if preprocessing_summary.error_messages:
        lines.append("⚠️ **Issues Found:**")
        for error in preprocessing_summary.error_messages:
            lines.append(f"   • {error}")
        lines.append("")
    
    if preprocessing_summary.has_valid_sources:
        lines.append("✅ **Ready to proceed with knowledge base creation**")
    else:
        lines.append("❌ **Cannot proceed - no valid sources found**")
    
    return "\n".join(lines)