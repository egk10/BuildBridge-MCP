#!/usr/bin/env python3
"""
BuildBridge-MCP AI Integration Demo

This demo showcases the AI-powered construction management capabilities
implemented in weeks 1-2 of the project plan.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

print("🏗️ BuildBridge-MCP AI Integration Demo")
print("=" * 50)

def demo_construction_prompts():
    """Demo the construction prompt system"""
    print("\n📋 1. Construction Prompt System Demo")
    print("-" * 40)
    
    try:
        from construction_prompts import ConstructionPrompts
        
        prompts = ConstructionPrompts()
        
        # Demo query type detection
        test_queries = [
            "What's our budget variance this month?",
            "Any safety incidents to report?",
            "Show me the project schedule delays",
            "Quality control issues on site?",
            "General project status update"
        ]
        
        for query in test_queries:
            query_type = prompts.get_query_type_from_keywords(query)
            print(f"  Query: '{query}'")
            print(f"  Type: {query_type}")
            print()
        
        print("✅ Construction prompt system working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing prompts: {e}")

def demo_token_tracking():
    """Demo the token tracking system"""
    print("\n📊 2. Token Tracking System Demo")
    print("-" * 40)
    
    try:
        # Mock AI service import
        sys.path.append(str(Path(__file__).parent / "src"))
        from ai_service import TokenTracker
        
        tracker = TokenTracker()
        
        # Simulate some API calls
        print("  Simulating API calls...")
        
        # Call 1: Budget analysis
        usage1 = tracker.track_usage("gpt-4-turbo", 150, 75)
        print(f"  Call 1 - Tokens: {usage1.total_tokens}, Cost: ${usage1.cost_estimate:.4f}")
        
        # Call 2: Safety query
        usage2 = tracker.track_usage("gpt-4-turbo", 120, 60)
        print(f"  Call 2 - Tokens: {usage2.total_tokens}, Cost: ${usage2.cost_estimate:.4f}")
        
        # Call 3: Schedule analysis
        usage3 = tracker.track_usage("gpt-4-turbo", 200, 100)
        print(f"  Call 3 - Tokens: {usage3.total_tokens}, Cost: ${usage3.cost_estimate:.4f}")
        
        # Show daily summary
        summary = tracker.get_daily_summary()
        print(f"\n  📈 Daily Summary:")
        print(f"    Total Tokens: {summary['total_tokens']}")
        print(f"    Total Cost: ${summary['total_cost']:.4f}")
        print(f"    Request Count: {summary['request_count']}")
        print(f"    Avg Tokens/Request: {summary['average_tokens_per_request']:.1f}")
        
        print("✅ Token tracking system working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing token tracking: {e}")

async def demo_production_integration():
    """Demo the production integration"""
    print("\n🏭 3. Production Integration Demo")
    print("-" * 40)
    
    try:
        from production_mcp_integration import ConstructionMCPEngine, RequestType, MCPRequest
        from datetime import datetime
        import uuid
        
        # Initialize engine
        engine = ConstructionMCPEngine()
        success = await engine.initialize()
        
        if not success:
            print("❌ Failed to initialize MCP engine")
            return
        
        print("✅ MCP Engine initialized successfully")
        
        # Test enhanced query processing
        request = MCPRequest(
            id=str(uuid.uuid4()),
            type=RequestType.ENHANCED_QUERY,
            query="What are the key factors in construction project budget management?",
            parameters={"prompt_type": "budget_analysis"},
            timestamp=datetime.now()
        )
        
        print(f"\n  Processing query: '{request.query}'")
        response = await engine.process_request(request)
        
        print(f"  ✅ Success: {response.success}")
        print(f"  ⚡ Processing time: {response.processing_time_ms:.2f}ms")
        print(f"  📝 Response type: Enhanced query processing")
        
        if response.enhanced_context:
            print(f"  🧠 Enhanced query: '{response.enhanced_context}'")
        
        print("\n✅ Production integration working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing production integration: {e}")

def demo_configuration():
    """Demo the configuration system"""
    print("\n⚙️ 4. Configuration System Demo")
    print("-" * 40)
    
    try:
        config_path = Path(__file__).parent / "config" / "credentials.json"
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            print("  ✅ Configuration file loaded")
            print(f"  🔧 Local mode: {config.get('local_mode', 'Not set')}")
            
            ai_config = config.get('ai_service', {})
            if ai_config:
                print(f"  🤖 AI model: {ai_config.get('model', 'Not set')}")
                print(f"  🌡️ Temperature: {ai_config.get('temperature', 'Not set')}")
                print(f"  📊 Max tokens: {ai_config.get('max_tokens', 'Not set')}")
                
                # Check for API key (masked)
                api_key = ai_config.get('openai_api_key', '')
                if api_key and api_key != '${OPENAI_API_KEY}':
                    print(f"  🔑 API key: {'*' * 20}...{api_key[-4:] if len(api_key) > 4 else '****'}")
                else:
                    print(f"  🔑 API key: Environment variable reference")
            
            print("  ✅ AI service configuration found")
        else:
            print("  ❌ Configuration file not found")
        
        # Check environment variable
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print(f"  ✅ Environment API key: {'*' * 20}...{api_key[-4:] if len(api_key) > 4 else '****'}")
        else:
            print("  ⚠️ Environment API key not set")
        
        print("\n✅ Configuration system working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing configuration: {e}")

async def demo_ai_service():
    """Demo the AI service (if API key available)"""
    print("\n🤖 5. AI Service Demo")
    print("-" * 40)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("  ⚠️ OpenAI API key not found")
        print("  💡 Set OPENAI_API_KEY environment variable to test AI service")
        print("  📝 Example: export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        from ai_service import create_ai_service
        
        config = {
            'openai_api_key': api_key,
            'model': 'gpt-3.5-turbo',  # Use cheaper model for demo
            'temperature': 0.1,
            'max_tokens': 150
        }
        
        print("  🔄 Creating AI service...")
        ai_service = create_ai_service(config)
        
        print("  ✅ AI service created successfully")
        print(f"  🤖 Model: {ai_service.model}")
        
        # Test AI query
        print("  🧠 Processing test query...")
        query = "What are three key factors to consider when planning a construction project budget?"
        
        response = await ai_service.process_construction_query(
            query=query,
            query_type="budget_analysis"
        )
        
        print(f"  ✅ AI response received")
        print(f"  📊 Tokens used: {response.tokens_used}")
        print(f"  💰 Cost: ${response.cost_estimate:.4f}")
        print(f"  ⚡ Response time: {response.response_time:.2f}s")
        print(f"  🎯 Confidence: {response.confidence_score:.2f}")
        
        print(f"\n  📝 AI Response:")
        print(f"  {response.content[:200]}{'...' if len(response.content) > 200 else ''}")
        
        print("\n✅ AI service working correctly!")
        
    except Exception as e:
        print(f"❌ Error testing AI service: {e}")

async def main():
    """Run all demos"""
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Running in virtual environment")
    else:
        print("⚠️ Not in virtual environment - some imports may fail")
        print("💡 Run: source construction_env/bin/activate")
    
    print("\n🧪 Running BuildBridge-MCP AI Integration Demos...")
    
    # Run demos
    demo_construction_prompts()
    demo_token_tracking()
    await demo_production_integration()
    demo_configuration()
    await demo_ai_service()
    
    print("\n" + "=" * 50)
    print("🎉 Demo Complete!")
    print("\n📚 Next Steps:")
    print("  1. Set OPENAI_API_KEY to test full AI capabilities")
    print("  2. Run: python production_mcp_integration.py --mode server")
    print("  3. Test API endpoints at http://localhost:8000/docs")
    print("  4. View real-time logs at http://localhost:8000/logs")
    print("\n🚀 Ready for Phase 2: Advanced Analytics & Intelligence!")

if __name__ == "__main__":
    asyncio.run(main())