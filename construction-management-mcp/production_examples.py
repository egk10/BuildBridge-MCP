#!/usr/bin/env python3
"""
Production Integration Examples and Usage Guide

This demonstrates how to integrate the Construction MCP into production systems
using various methods: HTTP API, WebSocket, and direct Python integration.
"""

import asyncio
import aiohttp
import json
import websockets
from typing import Dict, Any
import sys
from pathlib import Path

# Add the production integration
sys.path.insert(0, str(Path(__file__).parent))
from production_mcp_integration import ConstructionMCPClient

class ProductionExamples:
    """Examples of production integration patterns"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws") + "/ws"
    
    async def example_http_api_integration(self):
        """Example: HTTP REST API integration"""
        print("🌐 HTTP API Integration Example")
        print("-" * 40)
        
        async with aiohttp.ClientSession() as session:
            
            # 1. Health check
            async with session.get(f"{self.base_url}/health") as response:
                health = await response.json()
                print(f"✅ Health check: {health['status']}")
            
            # 2. Search projects
            query_data = {
                "query": "What projects are over budget?",
                "type": "search_projects",
                "parameters": {"filters": {"status": "active"}},
                "user_id": "user123"
            }
            
            async with session.post(f"{self.base_url}/query", json=query_data) as response:
                result = await response.json()
                print(f"📊 Search projects result: {result['success']}")
                print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
                if result['enhanced_context']:
                    print(f"   Enhanced context: {result['enhanced_context']}")
            
            # 3. Budget analysis
            budget_data = {
                "query": "Analyze budget performance",
                "type": "analyze_budget",
                "parameters": {"period": "current_quarter"},
                "user_id": "user123"
            }
            
            async with session.post(f"{self.base_url}/query", json=budget_data) as response:
                result = await response.json()
                print(f"💰 Budget analysis result: {result['success']}")
    
    async def example_websocket_integration(self):
        """Example: WebSocket real-time integration"""
        print("\n🔌 WebSocket Integration Example")
        print("-" * 40)
        
        try:
            async with websockets.connect(self.ws_url) as websocket:
                
                # Send queries and receive real-time responses
                queries = [
                    {"query": "Show me project status", "type": "search_projects"},
                    {"query": "Any safety incidents?", "type": "search_documents", "parameters": {"doc_type": "safety"}},
                    {"query": "Budget variance analysis", "type": "analyze_budget"}
                ]
                
                for query in queries:
                    # Send query
                    await websocket.send(json.dumps(query))
                    
                    # Receive response
                    response = await websocket.recv()
                    result = json.loads(response)
                    
                    print(f"📨 Query: {query['query']}")
                    print(f"   Response success: {result['success']}")
                    print(f"   Processing time: {result['processing_time_ms']:.2f}ms")
                    
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
    
    async def example_python_client_integration(self):
        """Example: Direct Python client integration"""
        print("\n🐍 Python Client Integration Example")
        print("-" * 40)
        
        # Initialize client
        client = ConstructionMCPClient()
        await client.initialize()
        
        # Example usage patterns
        
        # 1. Project search
        print("1. 🔍 Searching projects...")
        projects = await client.search_projects(
            "projects behind schedule",
            filters={"status": "active", "priority": "high"}
        )
        print(f"   Found {projects.get('count', 0)} projects")
        
        # 2. Budget analysis
        print("2. 💰 Analyzing budget...")
        budget = await client.analyze_budget(period="current_month")
        if "error" not in budget:
            print(f"   Budget analysis completed")
        
        # 3. Enhanced query processing
        print("3. 🤖 Enhanced query processing...")
        enhanced = await client.enhance_query(
            "Why are we over budget?", 
            prompt_type="budget_analysis"
        )
        if "error" not in enhanced:
            print(f"   Original: {enhanced.get('original_query', '')}")
            print(f"   Enhanced: {enhanced.get('enhanced_query', '')}")
    
    async def example_microservice_integration(self):
        """Example: Microservice architecture integration"""
        print("\n🏗️ Microservice Integration Pattern")
        print("-" * 40)
        
        # This would be your main application service
        class ConstructionManagementService:
            def __init__(self):
                self.mcp_client = ConstructionMCPClient()
            
            async def initialize(self):
                return await self.mcp_client.initialize()
            
            async def get_dashboard_data(self, user_id: str) -> Dict[str, Any]:
                """Get dashboard data for a user"""
                
                # Parallel requests for dashboard efficiency
                tasks = [
                    self.mcp_client.search_projects("active projects"),
                    self.mcp_client.analyze_budget(),
                    self.mcp_client.get_project_status("default"),  # This would fail but shows pattern
                ]
                
                # Execute in parallel
                try:
                    projects, budget, status = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    return {
                        "user_id": user_id,
                        "projects": projects if not isinstance(projects, Exception) else {"error": str(projects)},
                        "budget": budget if not isinstance(budget, Exception) else {"error": str(budget)},
                        "status": status if not isinstance(status, Exception) else {"error": str(status)},
                        "timestamp": "2025-09-18T23:00:00Z"
                    }
                except Exception as e:
                    return {"error": f"Dashboard error: {e}"}
            
            async def process_natural_language_query(self, query: str, user_id: str) -> Dict[str, Any]:
                """Process natural language queries from users"""
                
                # Determine query type based on keywords
                if "budget" in query.lower():
                    result = await self.mcp_client.analyze_budget()
                    enhanced = await self.mcp_client.enhance_query(query, "budget_analysis")
                elif "project" in query.lower():
                    result = await self.mcp_client.search_projects(query)
                    enhanced = await self.mcp_client.enhance_query(query, "general")
                else:
                    result = await self.mcp_client.enhance_query(query)
                    enhanced = result
                
                return {
                    "query": query,
                    "user_id": user_id,
                    "result": result,
                    "enhanced_context": enhanced,
                    "processed_at": "2025-09-18T23:00:00Z"
                }
        
        # Demo the service
        service = ConstructionManagementService()
        await service.initialize()
        
        print("📊 Getting dashboard data...")
        dashboard = await service.get_dashboard_data("user123")
        print(f"   Dashboard sections: {list(dashboard.keys())}")
        
        print("🗣️ Processing natural language query...")
        nl_result = await service.process_natural_language_query(
            "What's the budget status for this month?", 
            "user123"
        )
        print(f"   Query processed: {nl_result['query']}")

async def run_production_examples():
    """Run all production integration examples"""
    
    print("🚀 Construction MCP Production Integration Examples")
    print("=" * 60)
    print("Note: These examples assume the MCP server is running on localhost:8000")
    print("Start it with: python production_mcp_integration.py --mode server")
    print()
    
    examples = ProductionExamples()
    
    # Try each integration method
    try:
        await examples.example_python_client_integration()
        # await examples.example_http_api_integration()  # Requires server running
        # await examples.example_websocket_integration()  # Requires server running
        await examples.example_microservice_integration()
        
    except Exception as e:
        print(f"❌ Example error: {e}")
        print("💡 Make sure to start the server first with:")
        print("   python production_mcp_integration.py --mode server")

def create_production_deployment_guide():
    """Create production deployment guide"""
    
    guide = """
# 🚀 Production Deployment Guide

## Quick Start

### 1. Install Production Dependencies
```bash
pip install -r requirements-production.txt
```

### 2. Start Development Server
```bash
python production_mcp_integration.py --mode server
```

### 3. Test the API
```bash
curl http://localhost:8000/health
```

## Production Deployment Options

### Option 1: Docker (Recommended)
```bash
# Build and run with Docker Compose
docker-compose up -d

# Access services:
# - API: http://localhost:8000
# - Grafana: http://localhost:3000
# - Prometheus: http://localhost:9090
```

### Option 2: Kubernetes
```bash
# Create Kubernetes deployment
kubectl apply -f k8s/
```

### Option 3: Cloud Services
- **AWS**: ECS, EKS, or Lambda
- **Azure**: Container Instances, AKS, or Functions
- **GCP**: Cloud Run, GKE, or Cloud Functions

## Integration Methods

### 1. HTTP REST API
- **URL**: `POST /query`
- **Format**: JSON requests/responses
- **Best for**: Web applications, microservices

### 2. WebSocket
- **URL**: `ws://host:port/ws`
- **Format**: Real-time JSON messages
- **Best for**: Real-time dashboards, chat interfaces

### 3. Python Client
```python
from production_mcp_integration import ConstructionMCPClient

client = ConstructionMCPClient()
await client.initialize()
result = await client.search_projects("projects over budget")
```

### 4. Direct Integration
```python
from production_mcp_integration import ConstructionMCPEngine

engine = ConstructionMCPEngine()
await engine.initialize()
response = await engine.process_request(request)
```

## Security Considerations

### Authentication
- Implement JWT tokens
- Use API keys for service-to-service
- Configure OAuth for user authentication

### Authorization
- Role-based access control
- Project-level permissions
- Data filtering by user access

### Network Security
- HTTPS/TLS encryption
- VPN or private networks
- Firewall rules

## Monitoring & Observability

### Health Checks
- `/health` endpoint
- Database connectivity
- External service availability

### Metrics
- Request/response times
- Error rates
- Resource utilization

### Logging
- Structured logging
- Request tracing
- Error tracking

## Scaling Strategies

### Horizontal Scaling
- Load balancer
- Multiple API instances
- Database read replicas

### Vertical Scaling
- Increase CPU/memory
- Optimize database queries
- Cache frequently accessed data

### Performance Optimization
- Connection pooling
- Async/await patterns
- Background task processing
"""
    
    with open("/home/egk/buildbridge-MCP/BuildBridge-MCP/construction-management-mcp/docs/production_deployment_guide.md", "w") as f:
        f.write(guide)
    
    print("📚 Created production deployment guide at docs/production_deployment_guide.md")

if __name__ == "__main__":
    # Create deployment guide
    create_production_deployment_guide()
    
    # Run examples
    asyncio.run(run_production_examples())