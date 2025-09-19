#!/usr/bin/env python3
"""
Simple Demo of Enhanced Construction MCP

Shows how the enhanced prompt engineering improves construction queries.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from construction_prompts import get_construction_prompt, enhance_query_with_construction_context

def demo_enhanced_prompts():
    """Demonstrate enhanced prompt engineering"""

    print("🏗️ Enhanced Construction MCP Prompt Engineering Demo")
    print("=" * 60)

    test_queries = [
        "What's the budget status?",
        "How do you handle safety incidents?",
        "What are the main project phases?",
        "Why do construction projects go over budget?",
        "How do you manage construction schedules?"
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        print("-" * 50)

        # Enhance query with construction context
        enhanced_query = enhance_query_with_construction_context(query)
        print(f"🔧 Enhanced: {enhanced_query}")

        # Determine query type (simplified)
        if "budget" in query.lower():
            query_type = "budget_analysis"
        elif "safety" in query.lower():
            query_type = "safety_compliance"
        elif "schedule" in query.lower():
            query_type = "schedule_management"
        elif "project" in query.lower():
            query_type = "project_status"
        else:
            query_type = "general"

        # Get construction-specific prompt
        construction_prompt = get_construction_prompt(query_type)
        print(f"📋 Query Type: {query_type}")
        print(f"🎯 Construction Context: {construction_prompt[:200]}...")

        print("\n" + "=" * 60)

if __name__ == "__main__":
    demo_enhanced_prompts()

    print("\n✅ Demo complete!")
    print("\n📋 What you just saw:")
    print("1. ✅ Query enhancement with construction context")
    print("2. ✅ Automatic query type detection")
    print("3. ✅ Construction-specific prompt generation")
    print("4. ✅ Industry terminology and standards integration")

    print("\n🚀 Next steps:")
    print("1. Integrate these prompts into your MCP server")
    print("2. Test with real construction queries")
    print("3. Customize prompts for your specific projects")
    print("4. Consider fine-tuning for even better results")

if __name__ == "__main__":
    demo_enhanced_prompts()</content>
<parameter name="filePath">/home/egk/buildbridge-MCP/BuildBridge-MCP/construction-management-mcp/demo_enhanced_prompts.py