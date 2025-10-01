#!/usr/bin/env python3
"""Quick test script to verify MCP server functionality."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


RUN_SERVER_TESTS = os.getenv("RUN_SERVER_TESTS") == "1" or os.getenv("RUN_INTEGRATION_TESTS") == "1"
pytestmark = pytest.mark.skipif(
    not RUN_SERVER_TESTS,
    reason="Server integration tests disabled. Set RUN_SERVER_TESTS=1 to enable.",
)

def test_server_startup():
    """Test that the server starts successfully"""
    print("🧪 Testing MCP Server Startup...")
    
    # Change to the correct directory
    project_dir = Path(__file__).parent
    
    try:
        # Start the server process
        cmd = [
            "bash",
            "-c",
            f"cd {project_dir} && source buildbridge_env/bin/activate && python src/main.py",
        ]
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            preexec_fn=None
        )
        
        # Wait a few seconds for startup
        time.sleep(3)
        
        # Check if process is still running (good sign)
        if process.poll() is None:
            print("✅ Server started successfully and is running!")
            print("✅ Server is waiting for MCP client connections")
            
            # Terminate the process gracefully
            process.send_signal(signal.SIGINT)
            try:
                stdout, stderr = process.communicate(timeout=5)
                print(f"📋 Server output: {stdout[:200]}...")
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
            
            assert True
        else:
            # Process died quickly - there's an error
            stdout, stderr = process.communicate()
            print(f"❌ Server failed to start!")
            print(f"📋 Error output: {stderr}")
            assert False, "Server failed to start"
            
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        assert False, f"Error testing server: {e}"

def test_imports():
    """Test that all imports work correctly"""
    print("\n🧪 Testing Module Imports...")
    
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        # Test individual imports
        from construction_prompts import get_construction_prompt, enhance_query_with_construction_context
        print("✅ Construction prompts imported successfully")
        
        from connectors.excel_connector import ExcelConnector
        print("✅ Excel connector imported successfully")
        
        from connectors.sharepoint_connector import SharePointConnector  
        print("✅ SharePoint connector imported successfully")
        
        from connectors.document_indexer import DocumentIndexer
        print("✅ Document indexer imported successfully")
        
        from query_processor import QueryProcessor
        print("✅ Query processor imported successfully")
        
        assert True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        assert False, f"Import error: {e}"

def test_enhanced_prompts():
    """Test the enhanced construction prompts"""
    print("\n🧪 Testing Enhanced Construction Prompts...")
    
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from construction_prompts import get_construction_prompt, enhance_query_with_construction_context
        
        # Test getting a prompt
        budget_prompt = get_construction_prompt('budget_analysis')
        if 'construction cost management expert' in budget_prompt.lower():
            print("✅ Budget analysis prompt working")
        else:
            print("❌ Budget analysis prompt not working correctly")
            return False
            
        # Test query enhancement
        enhanced = enhance_query_with_construction_context("show budget status")
        if enhanced:
            print("✅ Query enhancement working")
        else:
            print("❌ Query enhancement not working")
            assert False, "Query enhancement not working"
            
        assert True
        
    except Exception as e:
        print(f"❌ Enhanced prompts error: {e}")
        assert False, f"Enhanced prompts error: {e}"

def main():
    """Run all tests"""
    print("🚀 BuildBridge MCP Server Test Suite")
    print("=" * 50)
    
    # Test imports first
    imports_ok = test_imports()
    
    # Test enhanced prompts
    prompts_ok = test_enhanced_prompts()
    
    # Test server startup
    server_ok = test_server_startup()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Enhanced Prompts: {'✅ PASS' if prompts_ok else '❌ FAIL'}")
    print(f"   Server Startup: {'✅ PASS' if server_ok else '❌ FAIL'}")
    
    if imports_ok and prompts_ok and server_ok:
        print("\n🎉 All tests passed! Your enhanced MCP server is ready to use.")
        print("\n📋 Usage Instructions:")
        print("   1. Start server: source construction_env/bin/activate && python src/main.py")
        print("   2. The server will wait for MCP client connections")
        print("   3. Use VS Code MCP extension or other MCP clients to connect")
        print("   4. Try queries like: 'What projects are over budget?'")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")
        
    return 0 if (imports_ok and prompts_ok and server_ok) else 1

if __name__ == "__main__":
    sys.exit(main())