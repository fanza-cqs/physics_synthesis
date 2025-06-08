# Fixed Zotero PDF Integration System - Part 1: Core Classes and Enums (Modular)
# File: src/downloaders/zotero_pdf_integrator_parts/part1_core_classes.py

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class IntegrationMode(Enum):
    """Integration modes for PDF processing."""
    DOWNLOAD_ONLY = "download_only"        # Mode 1: Just download, no Zotero integration
    ATTACH_TO_EXISTING = "attach"          # Mode 2: Attach to existing record
    UPLOAD_AND_REPLACE = "upload_replace"  # Mode 3: Upload new + replace original record

@dataclass
class IntegrationConfig:
    """Configuration for PDF integration."""
    mode: IntegrationMode
    replace_original: bool = True           # For UPLOAD_AND_REPLACE mode: whether to delete original
    target_collection_id: Optional[str] = None  # For upload mode
    backup_originals: bool = True          # Keep backup before replacing
    preserve_tags: bool = True             # Preserve tags during replacement
    preserve_notes: bool = True            # Preserve notes during replacement
    preserve_collections: bool = True      # Preserve collection memberships
    replacement_timeout: int = 30          # Timeout for replacement operations

@dataclass
class IntegrationResult:
    """Result of PDF integration operation."""
    doi: str
    original_item_key: str
    pdf_path: str
    mode: IntegrationMode
    success: bool
    error: Optional[str] = None
    
    # Mode-specific results
    attachment_key: Optional[str] = None     # For attach mode
    new_item_key: Optional[str] = None       # For upload mode
    replaced_item_key: Optional[str] = None  # For replacement operations
    replacement_performed: bool = False
    
    # Additional info
    processing_time: float = 0.0
    metadata_extracted: bool = False
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []

# Test function for this part
def test_part1():
    """Test that Part 1 works correctly."""
    print("🧪 Testing Part 1: Core Classes...")
    
    # Test IntegrationMode
    assert IntegrationMode.DOWNLOAD_ONLY.value == "download_only"
    assert IntegrationMode.ATTACH_TO_EXISTING.value == "attach"
    assert IntegrationMode.UPLOAD_AND_REPLACE.value == "upload_replace"
    
    # Test IntegrationConfig
    config = IntegrationConfig(mode=IntegrationMode.DOWNLOAD_ONLY)
    assert config.mode == IntegrationMode.DOWNLOAD_ONLY
    assert config.replace_original == True
    
    # Test IntegrationResult
    result = IntegrationResult(
        doi="test.doi",
        original_item_key="TEST123",
        pdf_path="/test/path.pdf",
        mode=IntegrationMode.DOWNLOAD_ONLY,
        success=True
    )
    assert result.warnings == []
    assert result.success == True
    
    print("✅ Part 1 test passed!")
    return True

if __name__ == "__main__":
    test_part1()