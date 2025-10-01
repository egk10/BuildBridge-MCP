#!/usr/bin/env python3
"""Test script to validate Azure Road project AI query functionality."""

import asyncio
import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

try:
    from ai_service import AIService  # type: ignore
    from construction_prompts import ConstructionPrompts  # type: ignore
except ImportError as exc:  # pragma: no cover - diagnostic path
    print(f"❌ Import error: {exc}")
    sys.exit(1)

RUN_AZURE_TESTS = os.getenv("RUN_AZURE_QUERY_TESTS") == "1" or os.getenv("RUN_INTEGRATION_TESTS") == "1"


async def _async_test_azure_query():
    """Test Azure Road project query with enhanced context"""
    
    # Sample Azure Road project data (based on our earlier extraction)
    azure_project_data = {
        "projects": [{
            "Project_Name": "6071 Azure Road",
            "Location": "Richmond, British Columbia", 
            "Client": "LDHT Holdings",
            "Architect": "HNPA Architecture + Planning",
            "Total_Units": 330,
            "Building_Area_Metric": 34962.0,
            "Building_Area_Imperial": 376332.0,
            "Levels_Above_Grade": 36,
            "Project_Type": "Condo/Rental/Office/Retail",
            "Tender_Closing": "20-Dec-24",
            "Project_ID": "azure_road",
            "source": "Google Sheets: azure_road project"
        }]
    }
    
    print("🔧 Initializing AI service...")
    try:
        # Load OpenAI API key from environment
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env", override=False)
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment variables")
            return None
        
        # Configure AI service
        ai_config = {
            'openai_api_key': api_key,
            'model': 'gpt-3.5-turbo',
            'max_tokens': 2000,
            'temperature': 0.1
        }
        
        ai_service = AIService(ai_config)
        prompts = ConstructionPrompts()
        
        # Test prompt generation
        print("📝 Generating enhanced prompt...")
        prompt = prompts.build_user_prompt(
            query="How many functional units and parking spots are in the Azure Road project? Please provide specific building details.",
            query_type="project_details",
            data_context=azure_project_data
        )
        
        print("\n🎯 Generated Prompt:")
        print("="*80)
        print(prompt)
        print("="*80)
        
        # Test AI response
        print("\n🤖 Querying AI service...")
        result = await ai_service.process_construction_query(
            query="How many functional units and parking spots are in the Azure Road project? Please provide specific building details.",
            query_type="project_details",
            data_context=azure_project_data
        )
        
        print("\n✅ AI Response:")
        print("-"*60)
        print(result.content if hasattr(result, 'content') else str(result))
        print("-"*60)
        
        # Show response details
        if hasattr(result, 'tokens_used'):
            print(f"\n📊 Tokens used: {result.tokens_used}")
        if hasattr(result, 'model_used'):
            print(f"🤖 Model: {result.model_used}")
        if hasattr(result, 'response_time'):
            print(f"⏱️ Response time: {result.response_time:.2f}s")

        return result

    except Exception as exc:
        print(f"❌ Error during AI query: {exc}")
        import traceback
        traceback.print_exc()
        return None


@pytest.mark.skipif(not RUN_AZURE_TESTS, reason="Azure query integration test disabled. Set RUN_AZURE_QUERY_TESTS=1 to enable.")
def test_azure_query():
    asyncio.run(_async_test_azure_query())

if __name__ == "__main__":
    print("🚀 Testing Azure Road Project AI Query")
    print("="*60)
    
    result = asyncio.run(_async_test_azure_query())
    
    if result:
        print(f"\n🎉 Test completed successfully!")
        content_length = len(result.content) if hasattr(result, 'content') else len(str(result))
        print(f"Response length: {content_length}")
    else:
        print("\n❌ Test failed!")
        sys.exit(1)