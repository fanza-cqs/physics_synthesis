#!/usr/bin/env python3
"""
Session System Validation Script
Tests the session-conversation alignment fix
"""

import sys
import os
from pathlib import Path

# Add project root to path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all imports work correctly"""
    print("🧪 Testing Imports...")
    
    try:
        # Test session imports
        from src.sessions import SessionManager, SessionOperationContext
        print("✅ Session manager imports work")
        
        from src.sessions.session_integration import SessionIntegration
        print("✅ Session integration imports work")
        
        # Test KB manager imports
        from src.core.knowledge_base_manager import KnowledgeBaseManager
        print("✅ KB manager imports work")
        
        # Test core module exports
        from src.core import create_knowledge_base, delete_knowledge_base, list_knowledge_bases
        print("✅ Core module exports work")
        
        # Test config
        from config.settings import PipelineConfig
        print("✅ Config imports work")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_session_context():
    """Test session context system"""
    print("\n🧪 Testing Session Context...")
    
    try:
        from src.sessions import SessionManager, SessionOperationContext
        from src.sessions.session_integration import SessionIntegration
        
        # Initialize
        session_manager = SessionManager(project_root)
        integration = SessionIntegration(session_manager)
        
        # Test context switching
        session_manager.set_operation_context(SessionOperationContext.CONVERSATION)
        current_context = session_manager._operation_context
        
        if current_context == SessionOperationContext.CONVERSATION:
            print("✅ Context setting works")
        else:
            print("❌ Context setting failed")
            return False
        
        # Test context manager
        with integration.handle_kb_management_operations():
            kb_context = session_manager._operation_context
            if kb_context == SessionOperationContext.KB_MANAGEMENT:
                print("✅ KB management context works")
            else:
                print("❌ KB management context failed")
                return False
        
        # Should be back to conversation context
        final_context = session_manager._operation_context
        if final_context == SessionOperationContext.CONVERSATION:
            print("✅ Context restoration works")
        else:
            print("❌ Context restoration failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Context test error: {e}")
        return False

def test_session_creation():
    """Test session creation logic"""
    print("\n🧪 Testing Session Creation...")
    
    try:
        from src.sessions import SessionManager, SessionOperationContext
        from src.sessions.session_integration import SessionIntegration
        
        # Initialize
        session_manager = SessionManager(project_root)
        integration = SessionIntegration(session_manager)
        
        # Count initial sessions
        initial_count = len(session_manager.list_sessions())
        print(f"   Initial sessions: {initial_count}")
        
        # Test: KB operations should NOT create sessions
        with integration.handle_kb_management_operations():
            # Try to save session in KB context (should be blocked)
            session_manager.save_current_session("kb_operation")
        
        kb_op_count = len(session_manager.list_sessions())
        print(f"   After KB operation: {kb_op_count}")
        
        # Test: Conversation operations SHOULD create sessions
        session = None
        with integration.with_context(SessionOperationContext.CONVERSATION):
            session = session_manager.create_session(trigger="user_initiated")
            if session:
                session.add_message("user", "Test message")
                session_manager.save_current_session("add_message")
        
        final_count = len(session_manager.list_sessions())
        print(f"   After conversation: {final_count}")
        
        # Check results
        kb_ops_ok = (kb_op_count == initial_count)
        conversation_ok = (final_count > initial_count) and (session is not None)
        
        if kb_ops_ok:
            print("✅ KB operations don't create sessions")
        else:
            print(f"❌ KB operations created sessions: {initial_count} -> {kb_op_count}")
        
        if conversation_ok:
            print("✅ Conversation operations create sessions")
        else:
            print(f"❌ Conversation operations failed: session={session is not None}, count={initial_count} -> {final_count}")
        
        return kb_ops_ok and conversation_ok
        
    except Exception as e:
        print(f"❌ Session creation test error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_kb_manager():
    """Test KB manager integration"""
    print("\n🧪 Testing KB Manager...")
    
    try:
        from src.core.knowledge_base_manager import KnowledgeBaseManager
        from config.settings import PipelineConfig
        
        config = PipelineConfig()
        manager = KnowledgeBaseManager(config)
        
        # Test list function
        kbs = manager.list_knowledge_bases()
        print(f"✅ KB Manager works - found {len(kbs)} knowledge bases")
        
        return True
        
    except Exception as e:
        print(f"❌ KB Manager test error: {e}")
        return False

def test_core_module_fallback():
    """Test that core module functions work without Streamlit context"""
    print("\n🧪 Testing Core Module Fallback...")
    
    try:
        # This should work even without Streamlit session state
        from src.core import list_knowledge_bases
        
        kbs = list_knowledge_bases()
        print(f"✅ Core module fallback works - found {len(kbs)} knowledge bases")
        
        return True
        
    except Exception as e:
        print(f"❌ Core module fallback test error: {e}")
        return False

def test_sessions_directory():
    """Test sessions directory setup"""
    print("\n🧪 Testing Sessions Directory...")
    
    try:
        sessions_dir = project_root / "sessions"
        
        if not sessions_dir.exists():
            print("ℹ️  Sessions directory doesn't exist - will be created automatically")
        else:
            session_files = list(sessions_dir.glob("*.json"))
            print(f"ℹ️  Found {len(session_files)} existing session files")
        
        print("✅ Sessions directory setup OK")
        return True
        
    except Exception as e:
        print(f"❌ Sessions directory test error: {e}")
        return False

def main():
    """Run all validation tests"""
    print("🔬 Session System Validation")
    print("=" * 50)
    print(f"Project root: {project_root}")
    print("=" * 50)
    
    tests = [
        ("Imports", test_imports),
        ("Sessions Directory", test_sessions_directory),
        ("Session Context", test_session_context), 
        ("Session Creation", test_session_creation),
        ("KB Manager", test_kb_manager),
        ("Core Module Fallback", test_core_module_fallback)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Session system is working correctly.")
        print("\n📋 What this means:")
        print("✅ Session imports work")
        print("✅ Context switching prevents unwanted session creation") 
        print("✅ KB operations won't create session files")
        print("✅ Conversations will create session files properly")
        print("✅ System works with and without Streamlit")
        
        print("\n🚀 Next steps:")
        print("1. Start your Streamlit app: streamlit run frontend_streamlit/app_sessions.py")
        print("2. Test KB operations (create/delete KB - should not create sessions)")
        print("3. Test conversations (start chat - should create sessions)")
        print("4. Monitor the sessions/ directory to verify behavior")
        
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        print("\n🔍 Troubleshooting:")
        print("- Check that all files are updated correctly")
        print("- Verify imports in __init__.py files")
        print("- Check for any missing dependencies")
        
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)