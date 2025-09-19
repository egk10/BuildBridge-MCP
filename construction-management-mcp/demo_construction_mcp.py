#!/usr/bin/env python3
"""
Demo script showing how to interact with the Construction MCP server
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import initialize_connectors, excel_connector, query_processor

def demo_construction_mcp():
    """Demonstrate the enhanced construction MCP capabilities"""
    
    print("🏗️  BuildBridge Construction MCP Demo")
    print("=" * 50)
    
    # Initialize the system
    print("📋 Initializing connectors...")
    try:
        initialize_connectors()
        print("✅ Connectors initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing: {e}")
        return
    
    # Demo 1: Enhanced AI Prompts
    print("\n🤖 Demo 1: Enhanced Construction AI Prompts")
    print("-" * 40)
    
    from construction_prompts import get_construction_prompt, enhance_query_with_construction_context
    
    print("Budget Analysis Prompt:")
    budget_prompt = get_construction_prompt('budget_analysis')
    print(f"📝 {budget_prompt[:200]}...")
    
    print("\nQuery Enhancement:")
    original_query = "show me budget status"
    enhanced_query = enhance_query_with_construction_context(original_query)
    print(f"📝 Original: {original_query}")
    print(f"🔧 Enhanced: {enhanced_query}")
    
    # Demo 2: Sample Data Access
    print("\n📊 Demo 2: Sample Data Access")
    print("-" * 40)
    
    try:
        # Try to load sample project data
        projects_df = excel_connector.get_project_data()
        print(f"✅ Found {len(projects_df)} projects in sample data")
        
        if len(projects_df) > 0:
            print("📋 Sample project columns:")
            for col in projects_df.columns[:5]:  # Show first 5 columns
                print(f"   - {col}")
    except Exception as e:
        print(f"📝 Note: Sample data not available ({e})")
        print("   This is normal - add sample Excel files to data/sample/ for full demo")
    
    # Demo 3: Available Tools
    print("\n🛠️  Demo 3: Available MCP Tools")
    print("-" * 40)
    
    tools = [
        "search_projects - Search for projects by natural language",
        "get_project_status - Get detailed project status", 
        "analyze_budget - Analyze budget performance",
        "get_schedule_updates - Get schedule milestones and delays",
        "search_documents - Search construction documents",
        "generate_report - Generate various reports"
    ]
    
    for tool in tools:
        print(f"🔧 {tool}")
    
    # Demo 4: Construction Context
    print("\n🏗️  Demo 4: Construction-Specific Context")
    print("-" * 40)
    
    from construction_prompts import CONSTRUCTION_SYSTEM_PROMPTS
    
    print("Available specialized prompts:")
    for prompt_type in CONSTRUCTION_SYSTEM_PROMPTS.keys():
        print(f"   - {prompt_type}")
    
    print("\n📚 Construction Examples:")
    from construction_prompts import get_construction_examples
    examples = get_construction_examples()
    for i, example in enumerate(examples[:2]):  # Show first 2 examples
        print(f"   Example {i+1}: {example['query']}")
        print(f"   Response: {example['response'][:100]}...")
    
    print("\n" + "=" * 50)
    print("🎉 Demo completed! Your Construction MCP is ready to use.")
    print("\n📋 Next Steps:")
    print("   1. Start the MCP server: source construction_env/bin/activate && python src/main.py")
    print("   2. Connect using VS Code MCP extension or other MCP clients")
    print("   3. Ask construction-specific questions and get enhanced AI responses")
    print("   4. Add your real Excel files to data/sample/ for live data analysis")

if __name__ == "__main__":
    demo_construction_mcp()