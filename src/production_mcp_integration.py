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
from collections import deque

# Production imports
try:
    from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import FileResponse, Response, RedirectResponse, HTMLResponse
    from fastapi.staticfiles import StaticFiles
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
try:
    from construction_prompts import enhance_query_with_construction_context, get_construction_prompt
    from ai_service import create_ai_service, AIService
except ImportError:
    # Try alternative import paths
    sys.path.append(str(Path(__file__).parent))
    from construction_prompts import enhance_query_with_construction_context, get_construction_prompt
    from ai_service import create_ai_service, AIService

def get_mcp_connectors():
    """Get the initialized MCP connectors"""
    try:
        from main import excel_connector, sharepoint_connector, document_indexer, query_processor
        return excel_connector, sharepoint_connector, document_indexer, query_processor
    except ImportError:
        return None, None, None, None

def load_config():
    """Load configuration from credentials.json and .env file"""
    # Load environment variables from .env file
    from dotenv import load_dotenv
    import os
    
    # Load .env file if it exists
    env_path = Path(__file__).parent.parent / ".env"  # Project root .env file
    if env_path.exists():
        load_dotenv(env_path)
        logger.info("✅ Loaded environment variables from .env file")
    
    config_path = Path(__file__).parent.parent / "config" / "credentials.json"
    try:
        with open(config_path, 'r') as f:
            config_content = f.read()
            # Handle environment variable substitution
            config_content = config_content.replace('${OPENAI_API_KEY}', os.getenv('OPENAI_API_KEY', ''))
            config = json.loads(config_content)
            
            # Override with environment variables if set
            if 'ai_service' in config:
                ai_config = config['ai_service']
                ai_config['openai_api_key'] = os.getenv('OPENAI_API_KEY', ai_config.get('openai_api_key', ''))
                ai_config['model'] = os.getenv('AI_MODEL', ai_config.get('model', 'gpt-4-turbo'))
                ai_config['max_tokens'] = int(os.getenv('AI_MAX_TOKENS', ai_config.get('max_tokens', 2000)))
                ai_config['temperature'] = float(os.getenv('AI_TEMPERATURE', ai_config.get('temperature', 0.1)))
                ai_config['max_retries'] = int(os.getenv('AI_MAX_RETRIES', ai_config.get('max_retries', 3)))
            
            # Override other settings
            config['local_mode'] = os.getenv('LOCAL_MODE', str(config.get('local_mode', True))).lower() == 'true'
            
            return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}

# Configure logging with real-time support
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)

# Global log storage for real-time viewing
log_buffer = deque(maxlen=100)  # Keep last 100 log messages
websocket_connections = set()

class LogHandler(logging.Handler):
    """Custom log handler that stores logs for real-time viewing"""
    
    def emit(self, record):
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
        }
        
        # Add to buffer
        log_buffer.append(log_entry)
        
        # Send to connected WebSocket clients
        if websocket_connections:
            message = json.dumps(log_entry)
            for websocket in websocket_connections.copy():
                try:
                    asyncio.create_task(websocket.send_text(message))
                except Exception:
                    websocket_connections.discard(websocket)

# Add custom handler to root logger
log_handler = LogHandler()
logging.getLogger().addHandler(log_handler)

class RequestType(Enum):
    """Types of requests supported by the MCP"""
    SEARCH_PROJECTS = "search_projects"
    PROJECT_STATUS = "get_project_status"
    ANALYZE_BUDGET = "analyze_budget"
    SCHEDULE_UPDATES = "get_schedule_updates"
    SEARCH_DOCUMENTS = "search_documents"
    GENERATE_REPORT = "generate_report"
    ENHANCED_QUERY = "enhanced_query"
    AI_QUERY = "ai_query"  # New AI-powered query processing

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
        self.ai_service = None  # Add AI service
        self.config = {}
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
            RequestType.AI_QUERY: self._handle_ai_query,  # Add AI query handler
        }
    
    async def initialize(self) -> bool:
        """Initialize MCP connectors and services"""
        try:
            logger.info("Initializing Construction MCP Engine...")
            
            # Load configuration
            self.config = load_config()
            
            # Initialize MCP connectors
            initialize_connectors()
            
            # Get the initialized connectors
            self.excel_connector, self.sharepoint_connector, self.document_indexer, self.query_processor = get_mcp_connectors()
            
            if self.query_processor is None:
                raise Exception("Failed to initialize query processor")
            
            # Initialize AI service if API key is available
            ai_config = self.config.get('ai_service', {})
            if ai_config.get('openai_api_key'):
                try:
                    logger.info("🤖 Initializing AI service...")
                    self.ai_service = create_ai_service(ai_config)
                    logger.info("✅ AI service initialized successfully")
                except Exception as e:
                    logger.warning(f"⚠️ AI service initialization failed: {e}")
                    logger.info("🔄 Continuing without AI service - set OPENAI_API_KEY to enable")
            else:
                logger.info("ℹ️ No OpenAI API key found - AI service disabled")
                
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
            logger.info(f"🔍 Processing query: '{request.query}' with type: {request.type}")
            logger.info(f"📋 Parameters: {request.parameters}")
            
            if not self.initialized:
                logger.error("❌ MCP Engine not initialized")
                raise Exception("MCP Engine not initialized")
            
            if request.type not in self.request_handlers:
                logger.error(f"❌ Unsupported request type: {request.type}")
                raise Exception(f"Unsupported request type: {request.type}")
            
            # Add construction context enhancement
            logger.info("🧠 Enhancing query with construction context...")
            enhanced_query = enhance_query_with_construction_context(request.query)
            if enhanced_query != request.query:
                logger.info(f"✨ Enhanced query: {enhanced_query}")
            
            # Process the request
            logger.info(f"🔄 Executing handler for {request.type.value}...")
            handler = self.request_handlers[request.type]
            result = await handler(request)
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"⚡ Processing completed in {processing_time:.2f}ms")
            
            if isinstance(result, dict) and 'count' in result:
                logger.info(f"📊 Results: {result['count']} items found")
            
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
        """Handle enhanced query processing with AI response"""
        try:
            enhanced = enhance_query_with_construction_context(request.query)
            prompt_type = request.parameters.get('prompt_type', 'general')
            system_prompt = get_construction_prompt(prompt_type)
            
            # If this looks like a calculation or analysis query, process it with AI
            query_lower = request.query.lower()
            needs_ai_processing = any(keyword in query_lower for keyword in [
                'calculate', 'what is', 'how much', 'current value', 'budget', 'cost', 'progress'
            ])
            
            if needs_ai_processing and self.ai_service:
                # Get all project data for context - use the most relevant search
                search_result = await self._handle_search_projects(
                    MCPRequest(
                        id=f"{request.id}-context",
                        type=RequestType.SEARCH_PROJECTS,
                        query="all projects",
                        parameters={'filters': {}},
                        timestamp=request.timestamp
                    )
                )
                
                data_context = None
                if search_result and 'results' in search_result:
                    # Pass all projects, not just the first few
                    data_context = {"projects": search_result['results']}
                
                # Process with AI
                ai_response = await self.ai_service.process_construction_query(
                    query=request.query,
                    context=None,
                    data_context=data_context,
                    query_type=prompt_type
                )
                
                return {
                    "original_query": request.query,
                    "enhanced_query": enhanced,
                    "system_prompt": system_prompt,
                    "prompt_type": prompt_type,
                    "ai_response": ai_response.content,
                    "ai_metadata": {
                        "confidence_score": ai_response.confidence_score,
                        "tokens_used": ai_response.tokens_used,
                        "cost_estimate": ai_response.cost_estimate,
                        "response_time": ai_response.response_time,
                        "model_used": ai_response.model_used
                    },
                    "has_ai_response": True
                }
            else:
                # Just return enhancement metadata
                return {
                    "original_query": request.query,
                    "enhanced_query": enhanced,
                    "system_prompt": system_prompt,
                    "prompt_type": prompt_type,
                    "has_ai_response": False
                }
        except Exception as e:
            logger.error(f"Error in enhanced_query: {e}")
            return {"error": str(e)}
    
    async def _get_all_project_data(self) -> str:
        """Get all project data as formatted string for AI context"""
        try:
            # Create a search request to get all projects
            search_request = MCPRequest(
                id=str(uuid.uuid4()),
                type=RequestType.SEARCH_PROJECTS,
                query="all projects",
                parameters={},
                timestamp=datetime.now()
            )
            
            # Get project data
            result = await self._handle_search_projects(search_request)
            if result.get('results'):
                projects = result['results']
                # Format project data for AI context
                formatted_data = []
                for project in projects:
                    project_info = f"Project: {project.get('Project_Name', 'Unknown')} (ID: {project.get('Project_ID', 'Unknown')})"
                    project_info += f", Budget: ${project.get('Total_Budget', 0):,}, Progress: {project.get('Progress_Percent', 0)}%"
                    project_info += f", Status: {project.get('Status', 'Unknown')}, Manager: {project.get('Project_Manager', 'Unknown')}"
                    formatted_data.append(project_info)
                return "\n".join(formatted_data)
            else:
                return "No project data available"
        except Exception as e:
            logger.error(f"Error getting project data: {e}")
            return f"Error retrieving project data: {str(e)}"
    
    async def _handle_ai_query(self, request: MCPRequest) -> Dict[str, Any]:
        """Handle AI-powered query processing"""
        try:
            if not self.ai_service:
                return {
                    "error": "AI service not available",
                    "message": "AI service not initialized. Please set OPENAI_API_KEY environment variable.",
                    "fallback_data": await self._handle_enhanced_query(request)
                }
            
            # Extract context parameters
            query_type = request.parameters.get('query_type', 'general')
            include_data_context = request.parameters.get('include_data_context', True)
            
            # Gather context data if requested
            context = None
            data_context = None
            
            if include_data_context:
                try:
                    # Always gather project data for project-related queries
                    query_lower = request.query.lower()
                    if any(keyword in query_lower for keyword in ['project', 'budget', 'cost', 'schedule', 'status']) or \
                       ('all' in query_lower and 'project' in query_lower) or \
                       ('list' in query_lower and 'project' in query_lower) or \
                       ('show' in query_lower and 'project' in query_lower):
                        # Get all project data for context
                        search_result = await self._handle_search_projects(
                            MCPRequest(
                                id=f"{request.id}-context",
                                type=RequestType.SEARCH_PROJECTS,
                                query="all projects",  # Always search for all projects to get complete data
                                parameters={'filters': {}},
                                timestamp=request.timestamp
                            )
                        )
                        if search_result and 'results' in search_result:
                            # Pass all projects from the data
                            data_context = {"projects": search_result['results']}
                            logger.info(f"🤖 Gathered context data for {len(search_result['results'])} projects")
                except Exception as e:
                    logger.warning(f"Failed to gather data context: {e}")
            
            # Process with AI service
            logger.info(f"🤖 Processing AI query: {request.query}")
            ai_response = await self.ai_service.process_construction_query(
                query=request.query,
                context=context,
                data_context=data_context,
                query_type=query_type
            )
            
            return {
                "ai_response": ai_response.content,
                "confidence_score": ai_response.confidence_score,
                "tokens_used": ai_response.tokens_used,
                "cost_estimate": ai_response.cost_estimate,
                "response_time": ai_response.response_time,
                "model_used": ai_response.model_used,
                "query_type": query_type,
                "metadata": ai_response.metadata,
                "has_context": data_context is not None
            }
            
        except Exception as e:
            logger.error(f"Error in ai_query: {e}")
            return {
                "error": str(e),
                "fallback_data": await self._handle_enhanced_query(request)
            }

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
    
    # Mount static files
    import os
    static_dir = os.path.join(os.path.dirname(__file__), "..", "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        print(f"📁 Static files mounted from: {static_dir}")
    else:
        print(f"⚠️  Static directory not found: {static_dir}")
    
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
                "query_processor": mcp_engine.query_processor is not None,
                "ai_service": mcp_engine.ai_service is not None
            },
            "ai_service_info": {
                "enabled": mcp_engine.ai_service is not None,
                "model": mcp_engine.config.get('ai_service', {}).get('model', 'N/A') if mcp_engine.ai_service else None,
                "usage_stats": mcp_engine.ai_service.get_usage_stats() if mcp_engine.ai_service else None
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
    
    @app.post("/process")
    async def process_ai_query(request: dict):
        """Process a query using AI for natural language responses"""
        try:
            query = request.get('query', '')
            if not query:
                return {"success": False, "response": "Please provide a query"}
            
            # Log the incoming query
            logger.info(f"📝 USER QUERY: '{query}'")
            
            # Get data source information
            data_sources = [
                "📊 Construction_Management_Data.xlsx",
                "💰 Budget_Tracking.xlsx", 
                "📅 Master_Schedule.xlsx",
                "👥 Resource_Allocation.xlsx",
                "🗂️ Project_Database.xlsx"
            ]
            
            # Gather actual project data for AI context
            data_context = None
            query_lower = query.lower()
            
            # Always gather project data for project-related queries
            if any(keyword in query_lower for keyword in ['project', 'budget', 'cost', 'schedule', 'status', 'all', 'list', 'show']):
                try:
                    # Get all project data
                    search_result = await mcp_engine._handle_search_projects(
                        MCPRequest(
                            id="process-context",
                            type=RequestType.SEARCH_PROJECTS,
                            query="all projects",
                            parameters={'filters': {}},
                            timestamp=datetime.now()
                        )
                    )
                    if search_result and 'results' in search_result:
                        data_context = {"projects": search_result['results']}
                        logger.info(f"📊 Gathered {len(search_result['results'])} projects for AI context")
                except Exception as e:
                    logger.warning(f"Failed to gather project data: {e}")
            
            # Enhanced context with data source information
            enhanced_context = f"""Construction project management context.
            
Data Sources Being Used:
{chr(10).join(data_sources)}

This system manages multiple construction projects with comprehensive tracking of budgets, schedules, and resources."""
            
            # Use AI service for natural language response
            if mcp_engine.ai_service:
                ai_response = await mcp_engine.ai_service.process_construction_query(
                    query=query,
                    data_context=data_context,  # Now includes actual project data
                    context=enhanced_context,
                    query_type="general"
                )
                
                response_text = ai_response.content if hasattr(ai_response, 'content') else str(ai_response)
                
                # Add data source footer to response
                response_with_sources = f"""{response_text}

---
📂 **Data Sources Used:**
{chr(10).join(['• ' + source for source in data_sources])}"""
                
                # Log the AI response
                logger.info(f"🤖 AI RESPONSE: '{response_text[:200]}{'...' if len(response_text) > 200 else ''}'")
                logger.info(f"📂 DATA SOURCES: {', '.join([s.split(' ', 1)[1] for s in data_sources])}")
                
                return {
                    "success": True, 
                    "response": response_with_sources
                }
            else:
                return {"success": False, "response": "AI service not available"}
                
        except Exception as e:
            return {"success": False, "response": f"Error: {str(e)}"}
    
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
    
    @app.websocket("/ws/logs")
    async def logs_websocket(websocket: WebSocket):
        """WebSocket endpoint for real-time log streaming"""
        await websocket.accept()
        websocket_connections.add(websocket)
        
        try:
            # Send recent logs immediately
            for log_entry in list(log_buffer):
                await websocket.send_text(json.dumps(log_entry))
            
            # Keep connection alive and wait for client messages
            while True:
                try:
                    # Wait for ping or any message to keep connection alive
                    await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await websocket.send_text(json.dumps({"type": "ping", "timestamp": datetime.now().isoformat()}))
                
        except WebSocketDisconnect:
            logger.info("Log streaming WebSocket disconnected")
        except Exception as e:
            logger.error(f"Log WebSocket error: {e}")
        finally:
            websocket_connections.discard(websocket)

    @app.get("/logs")
    async def get_recent_logs():
        """Get recent log entries via HTTP"""
        return {"logs": list(log_buffer)}

    # Static file serving and chat interface
    @app.get("/chat_interface.html")
    async def get_chat_interface():
        """Serve the chat interface HTML file"""
        import os
        
        # Get the project root directory (parent of src)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Try multiple possible locations for the chat interface file
        possible_paths = [
            os.path.join(project_root, "static", "chat_interface.html"),
            os.path.join(project_root, "chat_interface.html"),
            "static/chat_interface.html",
            "chat_interface.html"
        ]
        
        for file_path in possible_paths:
            if os.path.exists(file_path):
                print(f"📄 Serving chat interface from: {file_path}")
                # Add cache control headers to prevent caching issues
                response = FileResponse(file_path, media_type="text/html")
                response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response.headers["Pragma"] = "no-cache"
                response.headers["Expires"] = "0"
                return response
        
        print("⚠️ Static chat interface not found, using embedded fallback")
        # If not found, return a simple HTML page with cache-busting
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Construction MCP AI Chat Interface</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
            <meta http-equiv="Pragma" content="no-cache">
            <meta http-equiv="Expires" content="0">
            <style>
                body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .chat-container { max-width: 900px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .header { background: #2c3e50; color: white; padding: 20px; border-radius: 10px 10px 0 0; }
                .header h1 { margin: 0; font-size: 24px; }
                .header p { margin: 5px 0 0 0; opacity: 0.8; }
                .messages { height: 400px; overflow-y: auto; padding: 20px; border-bottom: 1px solid #eee; }
                .message { margin: 15px 0; padding: 12px 16px; border-radius: 8px; max-width: 80%; }
                .user { background: #3498db; color: white; text-align: right; margin-left: auto; }
                .assistant { background: #ecf0f1; color: #2c3e50; margin-right: auto; }
                .input-area { padding: 20px; display: flex; gap: 10px; }
                input[type="text"] { flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px; }
                input[type="text"]:focus { outline: none; border-color: #3498db; }
                button { padding: 12px 24px; background: #3498db; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; }
                button:hover { background: #2980b9; }
                button:disabled { background: #95a5a6; cursor: not-allowed; }
                .status { padding: 10px 20px; text-align: center; background: #e8f5e8; color: #27ae60; font-size: 14px; }
                .debug { padding: 5px 20px; text-align: center; background: #f8f9fa; color: #6c757d; font-size: 12px; }
            </style>
        </head>
        <body>
            <div class="chat-container">
                <div class="header">
                    <h1>🏗️ Construction MCP AI Assistant</h1>
                    <p>Ask about your construction projects, budgets, schedules, and more</p>
                </div>
                <div class="status">
                    ✅ Connected to AI Service - Using /process endpoint for consistent responses
                </div>
                <div class="debug">
                    Debug: All queries will be processed by AI service for consistent responses
                </div>
                <div id="messages" class="messages">
                    <div class="message assistant">
                        Hi! I'm your AI construction management assistant. I can help you with information about your projects, including the EGK HAMILTON project ($54M budget, 20% complete). All questions will get consistent AI-powered responses. What would you like to know?
                    </div>
                </div>
                <div class="input-area">
                    <input type="text" id="messageInput" placeholder="Ask about project status, budgets, earned value, schedules...">
                    <button onclick="sendMessage()" id="sendBtn">Send</button>
                </div>
            </div>
            <script>
                async function sendMessage() {
                    const input = document.getElementById('messageInput');
                    const sendBtn = document.getElementById('sendBtn');
                    const message = input.value.trim();
                    if (!message) return;
                    
                    addMessage(message, 'user');
                    input.value = '';
                    sendBtn.disabled = true;
                    sendBtn.textContent = 'AI Thinking...';
                    
                    try {
                        console.log('Sending to /process endpoint:', message);
                        const response = await fetch('/process', {
                            method: 'POST',
                            headers: { 
                                'Content-Type': 'application/json',
                                'Cache-Control': 'no-cache'
                            },
                            body: JSON.stringify({ query: message })
                        });
                        const data = await response.json();
                        console.log('Response from /process:', data);
                        
                        if (data.success && data.response) {
                            addMessage(data.response, 'assistant');
                        } else {
                            addMessage(data.response || 'Sorry, I could not process your request. The AI service may be unavailable.', 'assistant');
                        }
                    } catch (error) {
                        console.error('Error calling /process:', error);
                        addMessage('Error connecting to AI service: ' + error.message, 'assistant');
                    } finally {
                        sendBtn.disabled = false;
                        sendBtn.textContent = 'Send';
                    }
                }
                
                function addMessage(text, type) {
                    const messages = document.getElementById('messages');
                    const div = document.createElement('div');
                    div.className = 'message ' + type;
                    div.textContent = text;
                    messages.appendChild(div);
                    messages.scrollTop = messages.scrollHeight;
                }
                
                document.getElementById('messageInput').addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') sendMessage();
                });
                
                // Auto-focus input
                document.getElementById('messageInput').focus();
                
                // Add debug info
                console.log('Chat interface loaded - using /process endpoint for all queries');
            </script>
        </body>
        </html>
        """
        response = HTMLResponse(content=html_content)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response
    
    @app.get("/logs_viewer.html")
    async def get_logs_viewer():
        """Serve the logs viewer HTML file"""
        import os
        
        static_file = os.path.join("static", "logs_viewer.html")
        if os.path.exists(static_file):
            return FileResponse(static_file, media_type="text/html")
        else:
            raise HTTPException(status_code=404, detail="Logs viewer not found")
    
    @app.get("/")
    async def root():
        """Redirect to chat interface"""
        return RedirectResponse(url="/chat_interface.html")
    
    @app.get("/favicon.ico")
    async def get_favicon():
        """Return a basic favicon to avoid 404 errors"""
        # Return a simple 1x1 transparent PNG
        favicon_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x1aiTXtComment\x00\x00\x00\x00\x00Created with GIMPW\x81\x0e\x17\x00\x00\x00\x0bIDATx\x9cc```\x00\x00\x00\x02\x00\x01\xe5\'\xde\xfc\x00\x00\x00\x00IEND\xaeB`\x82'
        return Response(content=favicon_data, media_type="image/x-icon")

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
    
    async def ai_query(self, query: str, query_type: str = "general", include_data_context: bool = True) -> Dict[str, Any]:
        """Process query with AI service"""
        request = MCPRequest(
            id=str(uuid.uuid4()),
            type=RequestType.AI_QUERY,
            query=query,
            parameters={'query_type': query_type, 'include_data_context': include_data_context},
            timestamp=datetime.now()
        )
        response = await self.engine.process_request(request)
        return response.data if response.success else {"error": response.message}
    
    async def get_ai_usage_stats(self) -> Dict[str, Any]:
        """Get AI service usage statistics"""
        if self.engine.ai_service:
            return self.engine.ai_service.get_usage_stats()
        return {"error": "AI service not available"}

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