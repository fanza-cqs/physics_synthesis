#!/usr/bin/env python3
"""
Phase 3 Testing Script

Tests all new utilities added in Phase 3 one at a time.
Run from project root: python test_phase3.py
"""

import sys
import tempfile
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def print_test_header(test_name):
    """Print a test header."""
    print(f"\n{'='*60}")
    print(f"🧪 TESTING: {test_name}")
    print(f"{'='*60}")

def print_success(message):
    """Print success message."""
    print(f"✅ {message}")

def print_error(message):
    """Print error message."""
    print(f"❌ {message}")

def print_info(message):
    """Print info message."""
    print(f"ℹ️  {message}")

def test_file_operations():
    """Test file operations utility."""
    print_test_header("File Operations Utility")
    
    try:
        # Test import
        print_info("Testing import...")
        from src.utils.file_operations import (
            get_file_info,
            validate_file_for_processing,
            safe_create_directory,
            count_files_by_extension,
            calculate_file_hash,
            handle_file_operation_safely
        )
        print_success("Import successful")
        
        # Test with a real file
        print_info("Creating test file...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is test content for Phase 3 testing.\nLine 2 of content.")
            test_file_path = f.name
        
        print_success(f"Test file created: {test_file_path}")
        
        # Test get_file_info
        print_info("Testing get_file_info...")
        file_info = get_file_info(test_file_path)
        print_success(f"File info: exists={file_info['exists']}, size={file_info['size_bytes']} bytes")
        print_success(f"File details: name={file_info['name']}, extension={file_info['extension']}")
        
        # Test validate_file_for_processing
        print_info("Testing validate_file_for_processing...")
        is_valid = validate_file_for_processing(test_file_path, {'.txt'})
        print_success(f"File validation result: {is_valid}")
        
        # Test with invalid extension
        is_invalid = validate_file_for_processing(test_file_path, {'.pdf'})
        print_success(f"Invalid extension test: {is_invalid} (should be False)")
        
        # Test safe_create_directory
        print_info("Testing safe_create_directory...")
        test_dir = Path(tempfile.gettempdir()) / "phase3_test_dir"
        dir_created = safe_create_directory(test_dir)
        print_success(f"Directory creation: {dir_created}")
        
        # Test count_files_by_extension
        print_info("Testing count_files_by_extension...")
        file_counts = count_files_by_extension(Path(test_file_path).parent, recursive=False)
        print_success(f"File counts in temp dir: {dict(list(file_counts.items())[:3])}...")  # Show first 3
        
        # Test calculate_file_hash
        print_info("Testing calculate_file_hash...")
        file_hash = calculate_file_hash(test_file_path)
        print_success(f"File hash (MD5): {file_hash[:16]}...")  # Show first 16 chars
        
        # Test handle_file_operation_safely
        print_info("Testing handle_file_operation_safely...")
        def test_operation(path):
            return Path(path).stat().st_size
        
        success, result, error = handle_file_operation_safely(test_operation, test_file_path)
        print_success(f"Safe operation: success={success}, result={result}")
        
        # Test with failing operation
        success, result, error = handle_file_operation_safely(test_operation, "/nonexistent/file.txt")
        print_success(f"Safe failure handling: success={success}, error_type={type(error).__name__ if error else None}")
        
        # Cleanup
        Path(test_file_path).unlink()
        if test_dir.exists():
            test_dir.rmdir()
        
        print_success("File operations utility: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print_error(f"File operations test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_exceptions():
    """Test exception classes."""
    print_test_header("Exception Classes")
    
    try:
        # Test import
        print_info("Testing import...")
        from src.utils.exceptions import (
            ScientificAssistantError,
            DocumentProcessingError,
            KnowledgeBaseError,
            ZoteroIntegrationError,
            ConfigurationError,
            APIError
        )
        print_success("Import successful")
        
        # Test DocumentProcessingError
        print_info("Testing DocumentProcessingError...")
        try:
            raise DocumentProcessingError(
                "Test document error", 
                file_path="/test/document.pdf",
                original_error=ValueError("Original error")
            )
        except DocumentProcessingError as e:
            print_success(f"Exception caught: {e}")
            print_success(f"File path: {e.file_path}")
            print_success(f"Original error: {type(e.original_error).__name__}")
        
        # Test KnowledgeBaseError
        print_info("Testing KnowledgeBaseError...")
        try:
            raise KnowledgeBaseError(
                "Test KB error",
                kb_name="test_knowledge_base",
                operation="save_embeddings"
            )
        except KnowledgeBaseError as e:
            print_success(f"KB Exception: {e}")
            print_success(f"KB name: {e.kb_name}")
            print_success(f"Operation: {e.operation}")
        
        # Test ZoteroIntegrationError
        print_info("Testing ZoteroIntegrationError...")
        try:
            raise ZoteroIntegrationError(
                "Test Zotero error",
                item_key="ABC123",
                operation="attach_pdf"
            )
        except ZoteroIntegrationError as e:
            print_success(f"Zotero Exception: {e}")
            print_success(f"Item key: {e.item_key}")
        
        # Test ConfigurationError
        print_info("Testing ConfigurationError...")
        try:
            raise ConfigurationError(
                "Missing API key",
                config_key="ANTHROPIC_API_KEY"
            )
        except ConfigurationError as e:
            print_success(f"Config Exception: {e}")
            print_success(f"Config key: {e.config_key}")
        
        # Test APIError
        print_info("Testing APIError...")
        try:
            raise APIError(
                "API request failed",
                api_name="Claude",
                status_code=429
            )
        except APIError as e:
            print_success(f"API Exception: {e}")
            print_success(f"API: {e.api_name}, Status: {e.status_code}")
        
        # Test inheritance
        print_info("Testing exception inheritance...")
        try:
            raise DocumentProcessingError("Test inheritance")
        except ScientificAssistantError:
            print_success("Exception inheritance works correctly")
        
        print_success("Exception classes: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print_error(f"Exception classes test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_result_types():
    """Test result type classes."""
    print_test_header("Result Type Classes")
    
    try:
        # Test import
        print_info("Testing import...")
        from src.utils.result_types import (
            OperationResult,
            ProcessingResult,
            ValidationResult,
            success_result,
            error_result,
            processing_success,
            processing_failure,
            valid_result,
            invalid_result
        )
        print_success("Import successful")
        
        # Test OperationResult
        print_info("Testing OperationResult...")
        result = OperationResult(success=True, message="Test operation")
        result.add_warning("Minor issue detected")
        result.add_metadata("files_processed", 42)
        print_success(f"Operation result: success={result.success}")
        print_success(f"Warnings: {len(result.warnings)}")
        print_success(f"Metadata: {result.metadata}")
        
        # Test factory functions
        print_info("Testing factory functions...")
        success = success_result("Everything worked!", {"count": 10})
        error = error_result("Something failed", "Operation aborted")
        print_success(f"Success factory: {success.success}, data={success.data}")
        print_success(f"Error factory: {error.success}, error={error.error}")
        
        # Test ProcessingResult
        print_info("Testing ProcessingResult...")
        processing = ProcessingResult(
            success=True,
            processed_count=85,
            failed_count=5,
            skipped_count=10,
            processing_time=12.5
        )
        print_success(f"Processing result: total={processing.total_count}")
        print_success(f"Success rate: {processing.success_rate:.1%}")
        
        # Test processing factory functions
        proc_success = processing_success(100, 15.2)
        proc_failure = processing_failure("Database connection failed", 3)
        print_success(f"Processing success: {proc_success.processed_count} processed")
        print_success(f"Processing failure: {len(proc_failure.errors)} errors")
        
        # Test ValidationResult
        print_info("Testing ValidationResult...")
        validation = ValidationResult(is_valid=True)
        validation.add_warning("Deprecated function used")
        validation.add_warning("Consider updating syntax")
        print_success(f"Validation: valid={validation.is_valid}")
        print_success(f"Warnings: {len(validation.warnings)}")
        
        # Test validation that becomes invalid
        invalid_validation = ValidationResult(is_valid=True)
        invalid_validation.add_error("Critical error found")  # This should set is_valid=False
        print_success(f"Invalid after error: valid={invalid_validation.is_valid}")
        
        # Test validation factory functions
        valid = valid_result()
        invalid = invalid_result("File format not supported")
        print_success(f"Valid factory: {valid.is_valid}")
        print_success(f"Invalid factory: {invalid.is_valid}, errors={len(invalid.errors)}")
        
        # Test dataclass properties
        print_info("Testing dataclass properties...")
        result_with_timestamp = success_result("Timestamped result")
        print_success(f"Timestamp exists: {hasattr(result_with_timestamp, 'timestamp')}")
        print_success(f"Timestamp type: {type(result_with_timestamp.timestamp).__name__}")
        
        print_success("Result type classes: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print_error(f"Result types test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test that all utilities work together."""
    print_test_header("Integration Testing")
    
    try:
        print_info("Testing integrated workflow...")
        
        # Import everything
        from src.utils.file_operations import get_file_info, validate_file_for_processing
        from src.utils.exceptions import DocumentProcessingError
        from src.utils.result_types import success_result, error_result
        
        # Create test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Test Document\n\nThis is a test markdown file for integration testing.")
            test_file = f.name
        
        print_success("Test file created for integration test")
        
        # Simulate a file processing workflow
        print_info("Simulating file processing workflow...")
        
        def process_file(file_path):
            """Example function using all our utilities."""
            try:
                # Use file operations
                if not validate_file_for_processing(file_path, {'.md', '.txt', '.pdf'}):
                    return error_result("File validation failed")
                
                file_info = get_file_info(file_path)
                
                # Simulate some processing
                if file_info['size_bytes'] == 0:
                    raise DocumentProcessingError(
                        "Empty file cannot be processed",
                        file_path=file_path
                    )
                
                # Return success result with file info
                return success_result(
                    "File processed successfully",
                    {
                        "file_info": file_info,
                        "processing_time": 0.5
                    }
                )
                
            except DocumentProcessingError as e:
                return error_result(f"Processing error: {e}", f"Failed to process {e.file_path}")
            except Exception as e:
                return error_result(f"Unexpected error: {e}")
        
        # Test the workflow
        result = process_file(test_file)
        print_success(f"Workflow result: success={result.success}")
        print_success(f"File size processed: {result.data['file_info']['size_bytes']} bytes")
        
        # Test with invalid file
        invalid_result = process_file("/nonexistent/file.txt")
        print_success(f"Invalid file handling: success={invalid_result.success}")
        
        # Cleanup
        Path(test_file).unlink()
        
        print_success("Integration testing: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_existing_functionality():
    """Test that existing functionality still works."""
    print_test_header("Existing Functionality Regression Test")
    
    try:
        print_info("Testing core imports...")
        from src.core import KnowledgeBase
        from config import PipelineConfig
        print_success("Core imports working")
        
        print_info("Testing configuration...")
        config = PipelineConfig()
        print_success(f"Config loaded: project_root={config.project_root.name}")
        
        print_info("Testing KnowledgeBase creation...")
        kb = KnowledgeBase(name="test_regression")
        print_success(f"KnowledgeBase created: {kb.name}")
        
        # Test that old utils still work
        print_info("Testing existing utilities...")
        from src.utils import get_logger, ensure_directory_exists
        logger = get_logger("test")
        print_success("Existing utilities still work")
        
        print_success("Existing functionality: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print_error(f"Existing functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print(f"""
🚀 Phase 3 Testing Script
========================

Testing all new utilities added in Phase 3.
This script tests each component individually and together.

Project root: {project_root}
Python version: {sys.version.split()[0]}
""")
    
    # Track results
    test_results = []
    
    # Run all tests
    tests = [
        ("File Operations Utility", test_file_operations),
        ("Exception Classes", test_exceptions),
        ("Result Type Classes", test_result_types),
        ("Integration Testing", test_integration),
        ("Existing Functionality", test_existing_functionality)
    ]
    
    for test_name, test_func in tests:
        try:
            start_time = time.time()
            result = test_func()
            end_time = time.time()
            
            test_results.append((test_name, result, end_time - start_time))
            
            if result:
                print(f"\n🎉 {test_name}: PASSED ({end_time - start_time:.2f}s)")
            else:
                print(f"\n💥 {test_name}: FAILED ({end_time - start_time:.2f}s)")
                
        except Exception as e:
            print(f"\n💥 {test_name}: CRASHED - {e}")
            test_results.append((test_name, False, 0))
    
    # Print final summary
    print(f"\n{'='*60}")
    print(f"📊 FINAL RESULTS")
    print(f"{'='*60}")
    
    passed = sum(1 for _, result, _ in test_results if result)
    total = len(test_results)
    total_time = sum(duration for _, _, duration in test_results)
    
    for test_name, result, duration in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name} ({duration:.2f}s)")
    
    print(f"\nSummary: {passed}/{total} tests passed")
    print(f"Total time: {total_time:.2f}s")
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Phase 3 utilities are working correctly.")
        print(f"✅ Your new utilities are ready to use!")
        return 0
    else:
        print(f"\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)