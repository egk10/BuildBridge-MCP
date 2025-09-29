#!/usr/bin/env python3
"""
Simple MCP client to test your construction management server
"""

import json
import subprocess
import asyncio
import sys
from pathlib import Path

async def test_mcp_client():
    """Test MCP client connection"""
    
    print("🔌 Testing MCP Client Connection")
    print("=" * 40)
    
    # Start the MCP server as a subprocess
    server_dir = Path(__file__).parent
    
    cmd = [
        "bash", "-c", 
        f"cd {server_dir} && source construction_env/bin/activate && python src/main.py"
    ]
    
    print("🚀 Starting MCP server...")
    
    try:
        # Start server process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment for server to start
        await asyncio.sleep(2)
        
        # Send a simple MCP message
        init_message = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Sending initialization message...")
        process.stdin.write(json.dumps(init_message) + "\n")
        process.stdin.flush()
        
        # Try to read response
        await asyncio.sleep(1)
        
        # Check if server is responsive
        if process.poll() is None:
            print("✅ Server is running and responsive!")
            print("🔧 Available tools:")
            tools = [
                "search_projects",
                "get_project_status", 
                "analyze_budget",
                "get_schedule_updates",
                "search_documents",
                "generate_report"
            ]
            for tool in tools:
                print(f"   - {tool}")
        else:
            print("❌ Server stopped unexpectedly")
            
        # Clean up
        process.terminate()
        try:
            await asyncio.wait_for(asyncio.create_subprocess_exec("sleep", "1"), timeout=2)
        except:
            pass
        
        if process.poll() is None:
            process.kill()
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run the MCP client test"""
    print("🧪 MCP Client Test")
    print("This tests if your MCP server can accept connections\n")
    
    # Run the async test
    asyncio.run(test_mcp_client())
    
    print("\n📋 Next Steps:")
    print("1. If the test passed, your server is ready for MCP clients")
    print("2. Configure VS Code MCP extension to connect")
    print("3. Or use other MCP-compatible tools")
    print("4. See docs/vscode_mcp_setup.md for VS Code setup")

if __name__ == "__main__":
    main()