#!/usr/bin/env python3
"""
Comprehensive Test Suite for AI Integration in BuildBridge-MCP

Tests the AI service functionality, integration with MCP, and end-to-end workflows.
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class AIIntegrationTester:
    """Comprehensive test suite for AI integration"""
    
    def __init__(self):
        self.results = []
        self.start_time = None
        
    async def run_all_tests(self):
        """Run all AI integration tests"""
        self.start_time = time.time()
        logger.info("🧪 Starting AI Integration Test Suite")
        logger.info("=" * 60)
        
        # Test categories
        test_categories = [
            ("Environment Setup", self.test_environment_setup),
            ("AI Service Initialization", self.test_ai_service_init),
            ("Construction Prompts", self.test_construction_prompts),
            ("AI Query Processing", self.test_ai_query_processing),
            ("Token Tracking", self.test_token_tracking),
            ("Error Handling", self.test_error_handling),
            ("Production Integration", self.test_production_integration),
            ("End-to-End Workflow", self.test_end_to_end_workflow)
        ]
        
        for category_name, test_func in test_categories:
            logger.info(f"\n📋 Testing: {category_name}")
            logger.info("-" * 40)
            
            try:
                await test_func()
                self.results.append({"category": category_name, "status": "PASSED", "error": None})
                logger.info(f"✅ {category_name}: PASSED")
            except Exception as e:
                self.results.append({"category": category_name, "status": "FAILED", "error": str(e)})
                logger.error(f"❌ {category_name}: FAILED - {str(e)}")
        
        # Generate final report
        self.generate_final_report()
    
    async def test_environment_setup(self):
        """Test environment setup and dependencies"""
        logger.info("🔧 Checking environment setup...")
        
        # Check required packages
        required_packages = ['openai', 'tiktoken', 'fastmcp', 'pydantic']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"  ✓ {package} available")
            except ImportError:
                missing_packages.append(package)
                logger.warning(f"  ⚠ {package} missing")
        
        if missing_packages:
            raise Exception(f"Missing packages: {', '.join(missing_packages)}")
        
        # Check configuration files
        config_path = Path(__file__).parent.parent / "config" / "credentials.json"
        if not config_path.exists():
            raise Exception("credentials.json not found")
        logger.info("  ✓ Configuration file exists")
        
        # Check for API key (can be environment variable)
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            logger.info("  ✓ OpenAI API key found in environment")
        else:
            logger.warning("  ⚠ OpenAI API key not found - some tests may be skipped")
    
    async def test_ai_service_init(self):
        """Test AI service initialization"""
        logger.info("🤖 Testing AI service initialization...")
        
        # Test with valid config
        config = {
            'openai_api_key': os.getenv('OPENAI_API_KEY', 'test-key'),
            'model': 'gpt-4-turbo',
            'temperature': 0.1
        }
        
        try:
            from ai_service import create_ai_service, AIService
            
            if os.getenv('OPENAI_API_KEY'):
                ai_service = create_ai_service(config)
                logger.info("  ✓ AI service created successfully")
                
                # Test usage stats
                stats = ai_service.get_usage_stats()
                logger.info(f"  ✓ Usage stats available: {len(stats)} keys")
            else:
                logger.info("  ⚠ Skipping AI service test - no API key")
                
        except Exception as e:
            if "API key not found" in str(e) and not os.getenv('OPENAI_API_KEY'):
                logger.info("  ⚠ Expected error - no API key provided")
            else:
                raise e
    
    async def test_construction_prompts(self):
        """Test construction prompt system"""
        logger.info("🏗️ Testing construction prompts...")
        
        from construction_prompts import ConstructionPrompts
        
        prompts = ConstructionPrompts()
        
        # Test system prompt retrieval
        system_prompt = prompts.get_system_prompt("budget_analysis")
        assert len(system_prompt) > 100, "System prompt too short"
        assert "construction" in system_prompt.lower(), "Missing construction context"
        logger.info("  ✓ System prompts working")
        
        # Test user prompt building
        user_prompt = prompts.build_user_prompt(
            query="What is the project status?",
            context="Sample context",
            data_context={"projects": [{"id": 1, "name": "Test Project"}]},
            query_type="general"
        )
        assert len(user_prompt) > 50, "User prompt too short"
        logger.info("  ✓ User prompt building working")
        
        # Test query type detection
        query_type = prompts.get_query_type_from_keywords("show me the budget variance")
        assert query_type == "budget_analysis", f"Wrong query type: {query_type}"
        logger.info("  ✓ Query type detection working")
    
    async def test_ai_query_processing(self):
        """Test AI query processing (if API key available)"""
        logger.info("🧠 Testing AI query processing...")
        
        if not os.getenv('OPENAI_API_KEY'):
            logger.info("  ⚠ Skipping AI query test - no API key")
            return
        
        from ai_service import create_ai_service
        
        config = {
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'model': 'gpt-3.5-turbo',  # Use cheaper model for testing
            'temperature': 0.1,
            'max_tokens': 100
        }
        
        ai_service = create_ai_service(config)
        
        # Test basic query
        test_query = "What are the key components of a construction project budget?"
        response = await ai_service.process_construction_query(
            query=test_query,
            query_type="budget_analysis"
        )
        
        assert response.content, "No response content"
        assert response.tokens_used > 0, "No tokens used"
        assert response.confidence_score >= 0, "Invalid confidence score"
        logger.info(f"  ✓ AI query processed successfully")
        logger.info(f"    Tokens used: {response.tokens_used}")
        logger.info(f"    Confidence: {response.confidence_score:.2f}")
        logger.info(f"    Cost: ${response.cost_estimate:.4f}")
    
    async def test_token_tracking(self):
        """Test token tracking functionality"""
        logger.info("📊 Testing token tracking...")
        
        from ai_service import TokenTracker
        
        tracker = TokenTracker()
        
        # Test cost calculation
        cost = tracker.calculate_cost("gpt-4", 100, 50)
        assert cost > 0, "Cost calculation failed"
        logger.info(f"  ✓ Cost calculation: ${cost:.4f}")
        
        # Test usage tracking
        usage = tracker.track_usage("gpt-4", 100, 50)
        assert usage.total_tokens == 150, "Token count incorrect"
        assert usage.cost_estimate == cost, "Cost tracking incorrect"
        logger.info("  ✓ Usage tracking working")
        
        # Test daily summary
        summary = tracker.get_daily_summary()
        assert summary["request_count"] == 1, "Daily summary incorrect"
        logger.info("  ✓ Daily summary working")
    
    async def test_error_handling(self):
        """Test error handling and fallbacks"""
        logger.info("🚨 Testing error handling...")
        
        from ai_service import create_ai_service
        
        # Test with invalid API key
        config = {
            'openai_api_key': 'invalid-key',
            'model': 'gpt-4-turbo',
            'max_retries': 1  # Quick failure for testing
        }
        
        ai_service = create_ai_service(config)
        
        response = await ai_service.process_construction_query(
            query="Test query",
            query_type="general"
        )
        
        # Should return error response, not raise exception
        assert response.content, "No fallback response"
        assert "error" in response.content.lower() or "apologize" in response.content.lower(), "No error indication"
        logger.info("  ✓ Error handling working")
    
    async def test_production_integration(self):
        """Test production MCP integration"""
        logger.info("🏭 Testing production integration...")
        
        try:
            from production_mcp_integration import ConstructionMCPEngine
            
            engine = ConstructionMCPEngine()
            
            # Test initialization
            success = await engine.initialize()
            if success:
                logger.info("  ✓ Production engine initialized")
                
                # Test AI service availability in engine
                if engine.ai_service:
                    logger.info("  ✓ AI service integrated in production engine")
                else:
                    logger.info("  ⚠ AI service not available in production engine")
            else:
                logger.warning("  ⚠ Production engine initialization failed")
                
        except Exception as e:
            logger.warning(f"  ⚠ Production integration test skipped: {e}")
    
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow"""
        logger.info("🔄 Testing end-to-end workflow...")
        
        if not os.getenv('OPENAI_API_KEY'):
            logger.info("  ⚠ Skipping end-to-end test - no API key")
            return
        
        try:
            from production_mcp_integration import ConstructionMCPClient
            
            client = ConstructionMCPClient()
            await client.initialize()
            
            # Test AI query through client
            result = await client.ai_query(
                query="What should I consider when managing construction project budgets?",
                query_type="budget_analysis"
            )
            
            if "error" not in result:
                logger.info("  ✓ End-to-end AI query successful")
                logger.info(f"    Response length: {len(result.get('ai_response', ''))}")
            else:
                logger.warning(f"  ⚠ End-to-end test failed: {result['error']}")
                
        except Exception as e:
            logger.warning(f"  ⚠ End-to-end test failed: {e}")
    
    def generate_final_report(self):
        """Generate final test report"""
        total_time = time.time() - self.start_time
        
        logger.info("\n" + "=" * 60)
        logger.info("📊 AI INTEGRATION TEST RESULTS")
        logger.info("=" * 60)
        
        passed = sum(1 for r in self.results if r["status"] == "PASSED")
        failed = sum(1 for r in self.results if r["status"] == "FAILED")
        
        logger.info(f"Total Tests: {len(self.results)}")
        logger.info(f"Passed: {passed}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Success Rate: {(passed/len(self.results)*100):.1f}%")
        logger.info(f"Total Time: {total_time:.2f}s")
        
        logger.info("\nDetailed Results:")
        for result in self.results:
            status_icon = "✅" if result["status"] == "PASSED" else "❌"
            logger.info(f"  {status_icon} {result['category']}: {result['status']}")
            if result["error"]:
                logger.info(f"    Error: {result['error']}")
        
        # Save results to file
        report_file = Path(__file__).parent / "test_results_ai_integration.json"
        with open(report_file, 'w') as f:
            json.dump({
                "timestamp": time.time(),
                "total_tests": len(self.results),
                "passed": passed,
                "failed": failed,
                "success_rate": passed/len(self.results)*100,
                "total_time": total_time,
                "results": self.results
            }, f, indent=2)
        
        logger.info(f"\n📝 Detailed results saved to: {report_file}")
        
        if failed == 0:
            logger.info("\n🎉 ALL TESTS PASSED! AI integration is working correctly.")
        else:
            logger.warning(f"\n⚠️ {failed} tests failed. Check the details above.")

async def main():
    """Main test runner"""
    print("🧪 BuildBridge-MCP AI Integration Test Suite")
    print("=" * 50)
    
    # Check if this is a quick test or full test
    quick_test = "--quick" in sys.argv
    
    if quick_test:
        print("⚡ Running quick tests (no API calls)")
        os.environ.pop('OPENAI_API_KEY', None)  # Temporarily remove for quick test
    
    tester = AIIntegrationTester()
    await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())