#!/usr/bin/env python3
"""
Production-Ready Custom MCP Integration Framework

This provides a robust, scalable interface for integrating the Construction MCP
into production systems via HTTP REST API, WebSocket, or direct Python integration.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import traceback

# Production imports
try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    print("FastAPI not available. Run: pip install fastapi uvicorn websockets")

# MCP Integration
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import initialize_connectors
from construction_prompts import enhance_query_with_construction_context, get_construction_prompt

def get_mcp_connectors():
    """Get the initialized MCP connectors"""
    try:
        from main import excel_connector, sharepoint_connector, document_indexer, query_processor
        return excel_connector, sharepoint_connector, document_indexer, query_processor
    except ImportError:
        return None, None, None, None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RequestType(Enum):
    """Types of requests supported by the MCP"""
    SEARCH_PROJECTS = "search_projects"
    PROJECT_STATUS = "get_project_status"
    ANALYZE_BUDGET = "analyze_budget"
    SCHEDULE_UPDATES = "get_schedule_updates"
    SEARCH_DOCUMENTS = "search_documents"
    GENERATE_REPORT = "generate_report"
    ENHANCED_QUERY = "enhanced_query"

@dataclass
class MCPRequest:
    """Standardized MCP request structure"""
    id: str
    type: RequestType
    query: str
    parameters: Dict[str, Any]
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None

@dataclass
class MCPResponse:
    """Standardized MCP response structure"""
    id: str
    request_id: str
    success: bool
    data: Any
    message: str
    timestamp: datetime
    processing_time_ms: float
    enhanced_context: Optional[str] = None

class ConstructionMCPEngine:
    """Core MCP processing engine for production use"""
    
    def __init__(self):
        """Initialize the MCP engine"""
        self.initialized = False
        self.request_handlers = {}
        self.excel_connector = None
        self.sharepoint_connector = None
        self.document_indexer = None
        self.query_processor = None
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup request handlers for each MCP tool"""
        self.request_handlers = {
            RequestType.SEARCH_PROJECTS: self._handle_search_projects,
            RequestType.PROJECT_STATUS: self._handle_project_status,
            RequestType.ANALYZE_BUDGET: self._handle_analyze_budget,
            RequestType.SCHEDULE_UPDATES: self._handle_schedule_updates,
            RequestType.SEARCH_DOCUMENTS: self._handle_search_documents,
            RequestType.GENERATE_REPORT: self._handle_generate_report,
            RequestType.ENHANCED_QUERY: self._handle_enhanced_query,
        }
    
    async def initialize(self) -> bool:
        """Initialize MCP connectors and services"""
        try:
            logger.info("Initializing Construction MCP Engine...")
            initialize_connectors()
            
            # Get the initialized connectors
            self.excel_connector, self.sharepoint_connector, self.document_indexer, self.query_processor = get_mcp_connectors()
            
            if self.query_processor is None:
                raise Exception("Failed to initialize query processor")
                
            self.initialized = True
            logger.info("✅ Construction MCP Engine initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize MCP Engine: {e}")
            return False
    
    async def process_request(self, request: MCPRequest) -> MCPResponse:
        """Process a standardized MCP request"""
        start_time = datetime.now()
        
        try:
            if not self.initialized:
                raise Exception("MCP Engine not initialized")
            
            if request.type not in self.request_handlers:
                raise Exception(f"Unsupported request type: {request.type}")
            
            # Add construction context enhancement
            enhanced_query = enhance_query_with_construction_context(request.query)
            
            # Process the request
            handler = self.request_handlers[request.type]
            result = await handler(request)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return MCPResponse(
                id=str(uuid.uuid4()),
                request_id=request.id,
                success=True,
                data=result,
                message="Request processed successfully",
                timestamp=datetime.now(),
                processing_time_ms=processing_time,
                enhanced_context=enhanced_query if enhanced_query != request.query else None
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error processing request {request.id}: {e}")
            
            return MCPResponse(
                id=str(uuid.uuid4()),
                request_id=request.id,
                success=False,
                data=None,
                message=str(e),
                timestamp=datetime.now(),
                processing_time_ms=processing_time
            )
    
    async def _handle_search_projects(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle project search requests"""
        try:
            if not self.query_processor:
                raise Exception("Query processor not initialized")
                
            filters = request.parameters.get('filters', {})
            results = self.query_processor.search_projects(request.query, filters)
            return {
                "query": request.query,
                "results": results,
                "count": len(results) if results else 0
            }
        except Exception as e:
            logger.error(f"Error in search_projects: {e}")
            return {"error": str(e), "results": []}
    
    async def _handle_project_status(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle project status requests"""
        try:
            if not self.query_processor:
                raise Exception("Query processor not initialized")
                
            project_id = request.parameters.get('project_id')
            if not project_id:
                raise ValueError("project_id is required")
            
            status = self.query_processor.get_project_status(project_id)
            return status
        except Exception as e:
            logger.error(f"Error in get_project_status: {e}")
            return {"error": str(e)}
    
    async def _handle_analyze_budget(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle budget analysis requests"""
        try:
            if not self.query_processor:
                raise Exception("Query processor not initialized")
                
            project_id = request.parameters.get('project_id')
            period = request.parameters.get('period', 'current_month')
            
            analysis = self.query_processor.analyze_budget(project_id, period)
            return analysis
        except Exception as e:
            logger.error(f"Error in analyze_budget: {e}")
            return {"error": str(e)}
    
    async def _handle_schedule_updates(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle schedule update requests"""
        try:
            if not self.query_processor:
                raise Exception("Query processor not initialized")
                
            days_ahead = request.parameters.get('days_ahead', 30)
            updates = self.query_processor.get_schedule_updates(days_ahead)
            return updates
        except Exception as e:
            logger.error(f"Error in get_schedule_updates: {e}")
            return {"error": str(e)}
    
    async def _handle_search_documents(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle document search requests"""
        try:
            if not self.document_indexer:
                raise Exception("Document indexer not initialized")
                
            doc_type = request.parameters.get('doc_type')
            results = self.document_indexer.search_documents(request.query, doc_type)
            return {
                "query": request.query,
                "doc_type": doc_type,
                "results": results,
                "count": len(results)
            }
        except Exception as e:
            logger.error(f"Error in search_documents: {e}")
            return {"error": str(e), "results": []}
    
    async def _handle_generate_report(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle report generation requests"""
        try:
            if not self.query_processor:
                raise Exception("Query processor not initialized")
                
            report_type = request.parameters.get('report_type', 'status')
            project_id = request.parameters.get('project_id')
            
            report = self.query_processor.generate_report(report_type, project_id, **request.parameters)
            return report
        except Exception as e:
            logger.error(f"Error in generate_report: {e}")
            return {"error": str(e)}
    
    async def _handle_enhanced_query(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle enhanced query processing"""
        try:
            enhanced = enhance_query_with_construction_context(request.query)
            prompt_type = request.parameters.get('prompt_type', 'general')
            system_prompt = get_construction_prompt(prompt_type)
            
            return {
                "original_query": request.query,
                "enhanced_query": enhanced,
                "system_prompt": system_prompt,
                "prompt_type": prompt_type
            }
        except Exception as e:
            logger.error(f"Error in enhanced_query: {e}")
            return {"error": str(e)}

# FastAPI Production Interface
if FASTAPI_AVAILABLE:
    
    # Pydantic models for API
    class APIRequest(BaseModel):
        query: str = Field(..., description="The construction management query")
        type: str = Field(..., description="Type of request")
        parameters: Dict[str, Any] = Field(default_factory=dict, description="Additional parameters")
        user_id: Optional[str] = Field(None, description="User identifier")
        session_id: Optional[str] = Field(None, description="Session identifier")
    
    class APIResponse(BaseModel):
        success: bool
        data: Any
        message: str
        request_id: str
        processing_time_ms: float
        enhanced_context: Optional[str] = None
        timestamp: datetime
    
    from contextlib import asynccontextmanager
    
    # Global MCP engine instance
    mcp_engine = ConstructionMCPEngine()
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifespan manager"""
        # Startup
        await mcp_engine.initialize()
        yield
        # Shutdown (if needed)
        pass
    
    # Create FastAPI app with lifespan
    app = FastAPI(
        title="Construction Management MCP API",
        description="Production API for Construction Management Model Context Protocol",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.get("/")
    async def root():
        """API root endpoint"""
        return {
            "name": "Construction Management MCP API",
            "version": "1.0.0",
            "status": "running" if mcp_engine.initialized else "initializing"
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy" if mcp_engine.initialized else "unhealthy",
            "timestamp": datetime.now(),
            "services": {
                "mcp_engine": mcp_engine.initialized,
                "excel_connector": mcp_engine.excel_connector is not None,
                "sharepoint_connector": mcp_engine.sharepoint_connector is not None,
                "document_indexer": mcp_engine.document_indexer is not None,
                "query_processor": mcp_engine.query_processor is not None
            }
        }
    
    @app.post("/query", response_model=APIResponse)
    async def process_query(request: APIRequest):
        """Process a construction management query"""
        
        # Convert to internal request format
        mcp_request = MCPRequest(
            id=str(uuid.uuid4()),
            type=RequestType(request.type),
            query=request.query,
            parameters=request.parameters,
            timestamp=datetime.now(),
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Process the request
        response = await mcp_engine.process_request(mcp_request)
        
        # Convert to API response format
        return APIResponse(
            success=response.success,
            data=response.data,
            message=response.message,
            request_id=response.request_id,
            processing_time_ms=response.processing_time_ms,
            enhanced_context=response.enhanced_context,
            timestamp=response.timestamp
        )
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time interactions"""
        await websocket.accept()
        session_id = str(uuid.uuid4())
        
        try:
            while True:
                # Receive message
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Create MCP request
                mcp_request = MCPRequest(
                    id=str(uuid.uuid4()),
                    type=RequestType(message.get('type', 'enhanced_query')),
                    query=message.get('query', ''),
                    parameters=message.get('parameters', {}),
                    timestamp=datetime.now(),
                    session_id=session_id
                )
                
                # Process request
                response = await mcp_engine.process_request(mcp_request)
                
                # Send response
                await websocket.send_text(json.dumps(asdict(response), default=str))
                
        except WebSocketDisconnect:
            logger.info(f"WebSocket session {session_id} disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await websocket.close()

# Direct Python Integration Class
class ConstructionMCPClient:
    """Direct Python client for MCP integration"""
    
    def __init__(self):
        self.engine = ConstructionMCPEngine()
    
    async def initialize(self):
        """Initialize the MCP client"""
        return await self.engine.initialize()
    
    async def search_projects(self, query: str, filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search for construction projects"""
        request = MCPRequest(
            id=str(uuid.uuid4()),
            type=RequestType.SEARCH_PROJECTS,
            query=query,
            parameters={'filters': filters or {}},
            timestamp=datetime.now()
        )
        response = await self.engine.process_request(request)
        return response.data if response.success else {"error": response.message}
    
    async def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get project status"""
        request = MCPRequest(
            id=str(uuid.uuid4()),
            type=RequestType.PROJECT_STATUS,
            query=f"Status for project {project_id}",
            parameters={'project_id': project_id},
            timestamp=datetime.now()
        )
        response = await self.engine.process_request(request)
        return response.data if response.success else {"error": response.message}
    
    async def analyze_budget(self, project_id: str = None, period: str = "current_month") -> Dict[str, Any]:
        """Analyze budget performance"""
        request = MCPRequest(
            id=str(uuid.uuid4()),
            type=RequestType.ANALYZE_BUDGET,
            query=f"Budget analysis for {period}",
            parameters={'project_id': project_id, 'period': period},
            timestamp=datetime.now()
        )
        response = await self.engine.process_request(request)
        return response.data if response.success else {"error": response.message}
    
    async def enhance_query(self, query: str, prompt_type: str = "general") -> Dict[str, Any]:
        """Enhance query with construction context"""
        request = MCPRequest(
            id=str(uuid.uuid4()),
            type=RequestType.ENHANCED_QUERY,
            query=query,
            parameters={'prompt_type': prompt_type},
            timestamp=datetime.now()
        )
        response = await self.engine.process_request(request)
        return response.data if response.success else {"error": response.message}

# Production deployment function
def run_production_server(host: str = "0.0.0.0", port: int = 8000, workers: int = 1):
    """Run the production MCP server"""
    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI required for production server. Install with:")
        print("pip install fastapi uvicorn websockets")
        return
    
    print(f"🚀 Starting Construction MCP Production Server")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Workers: {workers}")
    print(f"   API Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "production_mcp_integration:app",
        host=host,
        port=port,
        workers=workers,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Construction MCP Production Integration")
    parser.add_argument("--mode", choices=["server", "client", "test", "engine"], default="test",
                       help="Run mode: server (FastAPI), client (Python), test, or engine (Direct)")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers")
    
    args = parser.parse_args()
    
    if args.mode == "server":
        run_production_server(args.host, args.port, args.workers)
    
    elif args.mode == "client":
        # Demo Python client usage
        async def demo_client():
            client = ConstructionMCPClient()
            await client.initialize()
            
            print("🔧 Testing Python client...")
            result = await client.search_projects("projects over budget")
            print(f"Search result: {result}")
            
            enhanced = await client.enhance_query("show budget status", "budget_analysis")
            print(f"Enhanced query: {enhanced}")
        
        asyncio.run(demo_client())
    
    elif args.mode == "engine":
        # Demo direct engine usage
        async def demo_engine():
            engine = ConstructionMCPEngine()
            await engine.initialize()
            
            print("⚙️ Testing Direct Engine...")
            
            # Test enhanced query processing
            request = MCPRequest(
                id="engine-test-001",
                type=RequestType.ENHANCED_QUERY,
                query="Show me all high-risk projects",
                parameters={"prompt_type": "safety_analysis"},
                timestamp=datetime.now()
            )
            
            response = await engine.process_request(request)
            
            print(f"✅ Engine test completed:")
            print(f"   Success: {response.success}")
            print(f"   Processing time: {response.processing_time_ms:.2f}ms")
            print(f"   Message: {response.message}")
            print(f"   Data length: {len(response.data) if response.data else 0}")
        
        asyncio.run(demo_engine())
    
    else:  # test mode
        print("🧪 Testing Production MCP Integration...")
        
        async def test_integration():
            engine = ConstructionMCPEngine()
            await engine.initialize()
            
            # Test request
            request = MCPRequest(
                id="test-001",
                type=RequestType.ENHANCED_QUERY,
                query="What projects are over budget?",
                parameters={"prompt_type": "budget_analysis"},
                timestamp=datetime.now()
            )
            
            response = await engine.process_request(request)
            
            print(f"✅ Test completed:")
            print(f"   Success: {response.success}")
            print(f"   Processing time: {response.processing_time_ms:.2f}ms")
            print(f"   Message: {response.message}")
        
        asyncio.run(test_integration())