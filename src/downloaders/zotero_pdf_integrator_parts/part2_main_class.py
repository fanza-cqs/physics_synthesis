# Fixed Zotero PDF Integration System - Part 2: Main Integrator Class (Modular)
# File: src/downloaders/zotero_pdf_integrator_parts/part2_main_class.py

import time
from pathlib import Path
from typing import Dict, List

# Import from Part 1
from .part1_core_classes import IntegrationMode, IntegrationConfig, IntegrationResult

class FixedZoteroPDFIntegrator:
    """
    FIXED PDF integration system using correct PyZotero attachment methods.
    
    Note: In modular assembly, the individual methods will be attached dynamically
    from the other parts. This class provides the structure and core functionality.
    """
    
    def __init__(self, zotero_manager, config: IntegrationConfig):
        """
        Initialize the integrator.
        
        Args:
            zotero_manager: Enhanced Zotero manager instance
            config: Integration configuration
        """
        self.zotero_manager = zotero_manager
        self.config = config
        
        # Statistics tracking
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'attachments_created': 0,
            'uploads_performed': 0,
            'replacements_performed': 0,
            'errors': []
        }
        
        print(f"🔧 FIXED PDF Integrator initialized in {config.mode.value} mode")
        if config.mode == IntegrationMode.UPLOAD_AND_REPLACE:
            print(f"   📁 Target collection: {config.target_collection_id}")
            print(f"   🔄 Replace original records: {config.replace_original}")
            print(f"   📌 Preserve tags: {config.preserve_tags}")
            print(f"   📝 Preserve notes: {config.preserve_notes}")
            print(f"   📚 Preserve collections: {config.preserve_collections}")
    
    def process_download_results(self, download_results: List[Dict]) -> List[IntegrationResult]:
        """
        Process all download results according to the configured mode.
        
        Args:
            download_results: List of successful DOI download results
        
        Returns:
            List of integration results
        """
        print(f"\n🚀 Processing {len(download_results)} downloaded PDFs in {self.config.mode.value} mode")
        print("=" * 70)
        
        results = []
        
        for i, download_result in enumerate(download_results, 1):
            print(f"\n📄 Processing {i}/{len(download_results)}: {Path(download_result['file_path']).name}")
            
            start_time = time.time()
            
            try:
                # These methods will be attached dynamically from other parts
                if self.config.mode == IntegrationMode.DOWNLOAD_ONLY:
                    result = self._mode1_download_only(download_result)
                elif self.config.mode == IntegrationMode.ATTACH_TO_EXISTING:
                    result = self._mode2_attach_to_existing_fixed(download_result)
                elif self.config.mode == IntegrationMode.UPLOAD_AND_REPLACE:
                    result = self._mode3_upload_and_replace_fixed(download_result)
                else:
                    raise ValueError(f"Unknown integration mode: {self.config.mode}")
                
                result.processing_time = time.time() - start_time
                
                if result.success:
                    self.stats['successful'] += 1
                    print(f"   ✅ Success ({result.processing_time:.1f}s)")
                else:
                    self.stats['failed'] += 1
                    print(f"   ❌ Failed: {result.error}")
                
            except Exception as e:
                result = IntegrationResult(
                    doi=download_result.get('doi', 'unknown'),
                    original_item_key=download_result.get('zotero_key', 'unknown'),
                    pdf_path=download_result['file_path'],
                    mode=self.config.mode,
                    success=False,
                    error=str(e),
                    processing_time=time.time() - start_time
                )
                self.stats['failed'] += 1
                self.stats['errors'].append(str(e))
                print(f"   💥 Exception: {e}")
            
            results.append(result)
            self.stats['total_processed'] += 1
        
        # Print summary
        self._print_processing_summary()
        
        return results
    
    def _print_processing_summary(self):
        """Print summary of processing results."""
        print(f"\n📊 FIXED INTEGRATION SUMMARY ({self.config.mode.value} mode)")
        print("=" * 50)
        print(f"✅ Successful: {self.stats['successful']}")
        print(f"❌ Failed: {self.stats['failed']}")
        
        if self.stats['total_processed'] > 0:
            print(f"📊 Success rate: {(self.stats['successful'] / self.stats['total_processed'] * 100):.1f}%")
        
        if self.config.mode == IntegrationMode.ATTACH_TO_EXISTING:
            print(f"📎 Attachments created: {self.stats['attachments_created']}")
        elif self.config.mode == IntegrationMode.UPLOAD_AND_REPLACE:
            print(f"📤 New records created: {self.stats['uploads_performed']}")
            if self.config.replace_original:
                print(f"🔄 Records replaced: {self.stats['replacements_performed']}")
        elif self.config.mode == IntegrationMode.DOWNLOAD_ONLY:
            print(f"📁 Files confirmed available locally")
        
        if self.stats['errors']:
            print(f"\n❌ Errors encountered:")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"   • {error}")
            if len(self.stats['errors']) > 5:
                print(f"   ... and {len(self.stats['errors']) - 5} more")

# Test function for this part
def test_part2():
    """Test that Part 2 works correctly."""
    print("🧪 Testing Part 2: Main Class...")
    
    # Test class creation
    config = IntegrationConfig(mode=IntegrationMode.DOWNLOAD_ONLY)
    integrator = FixedZoteroPDFIntegrator(None, config)
    
    assert integrator.config.mode == IntegrationMode.DOWNLOAD_ONLY
    assert integrator.stats['total_processed'] == 0
    
    print("✅ Part 2 test passed!")
    return True

if __name__ == "__main__":
    test_part2()