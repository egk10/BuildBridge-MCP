#!/usr/bin/env python3
"""
Interactive demo of your Construction MCP capabilities
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def interactive_demo():
    """Interactive demo of construction MCP features"""
    
    print("🏗️  Interactive Construction MCP Demo")
    print("=" * 50)
    print("This simulates what you'd experience with an MCP client")
    print()
    
    # Initialize the system
    try:
        from main import initialize_connectors
        from query_processor import QueryProcessor
        from construction_prompts import enhance_query_with_construction_context, get_construction_prompt
        
        print("📋 Initializing Construction MCP...")
        initialize_connectors()
        print("✅ Ready to process construction queries!")
        print()
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return
    
    # Demo queries
    demo_queries = [
        "What projects are over budget?",
        "Show me schedule delays",
        "Analyze safety incidents", 
        "Generate a budget report",
        "Search for specification documents"
    ]
    
    print("🤖 Available Construction AI Features:")
    print("-" * 40)
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        
        # Show enhanced context
        enhanced = enhance_query_with_construction_context(query)
        if enhanced != query:
            print(f"   🔧 Enhanced: {enhanced}")
        
        # Show which prompt would be used
        if "budget" in query.lower():
            prompt_type = "budget_analysis"
        elif "safety" in query.lower():
            prompt_type = "safety_compliance"
        elif "schedule" in query.lower():
            prompt_type = "schedule_management"
        else:
            prompt_type = "general"
            
        prompt = get_construction_prompt(prompt_type)
        print(f"   🧠 AI Context: {prompt_type} specialist")
        print(f"   📝 Response would include: {prompt.split('.')[0]}...")
    
    print("\n" + "=" * 50)
    print("🎯 How to Connect MCP Clients:")
    print()
    print("1. 📱 VS Code MCP Extension:")
    print("   - Install MCP extension")
    print("   - Add server config (see config/vscode_settings_example.json)")
    print("   - Connect and start asking questions!")
    print()
    print("2. 🔧 Command Line:")
    print("   - Use MCP-compatible tools")
    print("   - Connect to stdio interface")
    print("   - Server runs on: python src/main.py")
    print()
    print("3. 🌐 Web Interface:")
    print("   - Some MCP tools provide web UIs")
    print("   - Check MCP ecosystem for options")
    print()
    print("4. 🔌 Custom Integration:")
    print("   - Build your own MCP client")
    print("   - Use MCP protocol specification")
    print("   - Connect via JSON-RPC over stdio")

def show_sample_mcp_interaction():
    """Show what an MCP interaction would look like"""
    
    print("\n📋 Sample MCP Client Interaction:")
    print("-" * 40)
    
    sample_conversation = [
        ("User", "What projects are currently over budget?"),
        ("MCP Client", "Calling search_projects tool with budget filter..."),
        ("Construction AI", "Based on current budget analysis, I found 3 projects over budget:\n- Downtown Office: 15% over budget due to material cost increases\n- Shopping Center: 8% over budget from change orders\n- Residential Complex: 12% over budget from weather delays"),
        ("User", "Generate a budget variance report for these projects"),
        ("MCP Client", "Calling generate_report tool with budget variance parameters..."),
        ("Construction AI", "Budget Variance Report generated with detailed analysis including:\n- Root cause analysis for each project\n- Recommended corrective actions\n- Updated forecasts and risk assessments")
    ]
    
    for speaker, message in sample_conversation:
        if speaker == "User":
            print(f"👤 {speaker}: {message}")
        elif speaker == "MCP Client":
            print(f"🔧 {speaker}: {message}")
        else:
            print(f"🤖 {speaker}: {message}")
        print()

if __name__ == "__main__":
    interactive_demo()
    show_sample_mcp_interaction()