# 🎮 BuildBridge-MCP Interaction Guide

## 🚀 How to Use Your AI-Powered Construction Management System

### **🟢 Currently Available Interfaces:**

---

## 1. 🖥️ **Command Line Interface (CLI)** ✅ READY

### Quick Test with AI Integration:
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP/construction-management-mcp

# Set your API key (already in .env file)
export OPENAI_API_KEY="your-api-key"

# Run AI integration demo
python3 demo_ai_integration.py

# Or test specific components
python3 interactive_demo.py
```

### Direct AI Service Testing:
```bash
# Test AI service directly
python3 -c "
import asyncio
import sys
sys.path.insert(0, 'src')
from ai_service import create_ai_service
from dotenv import load_dotenv
import os

load_dotenv()

async def test():
    config = {'openai_api_key': os.getenv('OPENAI_API_KEY')}
    ai = create_ai_service(config)
    response = await ai.process_construction_query(
        'What are key budget management strategies?', 
        query_type='budget_analysis'
    )
    print(f'🤖 AI Response: {response.content}')
    print(f'💰 Cost: \${response.cost_estimate:.4f}')

asyncio.run(test())
"
```

---

## 2. 🌐 **Web Server + API** ✅ READY

### Starting the Web Server:
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP/construction-management-mcp

# Method 1: Using existing virtual environment
./construction_env/bin/python production_mcp_integration.py --mode server --host localhost --port 8000

# Method 2: Quick setup with system Python
python3 -m pip install fastapi uvicorn websockets --user
python3 production_mcp_integration.py --mode server --host localhost --port 8000
```

### Available Web Interfaces:
Once the server is running, access these URLs:

#### 🎯 **API Documentation** (Interactive)
- **URL**: `http://localhost:8000/docs`
- **Features**: Test all endpoints directly in browser
- **Swagger UI**: Complete API documentation

#### 🏠 **Main Interface**
- **URL**: `http://localhost:8000/`
- **Features**: Basic server info and health status

#### 💬 **Chat Interface** (If Available)
- **URL**: `http://localhost:8000/chat_interface.html`
- **Features**: Real-time chat with AI assistant

#### 📊 **Health Check**
- **URL**: `http://localhost:8000/health`
- **Features**: System status and AI service health

---

## 3. 🔧 **API Testing with cURL**

### Health Check:
```bash
curl -X GET "http://localhost:8000/health"
```

### AI Query Example:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the top 3 budget management challenges in construction?",
    "type": "ai_query",
    "parameters": {
      "query_type": "budget_analysis",
      "include_context": true
    }
  }'
```

### Enhanced Query:
```bash
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me project safety incidents",
    "type": "enhanced_query",
    "parameters": {
      "prompt_type": "safety_analysis"
    }
  }'
```

---

## 4. 🐍 **Python Client Integration**

### Direct Python Usage:
```python
import asyncio
import sys
sys.path.insert(0, 'src')

from production_mcp_integration import ConstructionMCPEngine, MCPRequest, RequestType
from datetime import datetime
import uuid

async def use_mcp():
    # Initialize engine
    engine = ConstructionMCPEngine()
    await engine.initialize()
    
    # Create AI request
    request = MCPRequest(
        id=str(uuid.uuid4()),
        type=RequestType.AI_QUERY,
        query="How can I optimize construction project schedules?",
        parameters={"context": "schedule_management"},
        timestamp=datetime.now()
    )
    
    # Process request
    response = await engine.process_request(request)
    
    print(f"Success: {response.success}")
    print(f"Response: {response.data}")
    print(f"Processing time: {response.processing_time_ms}ms")

# Run the demo
asyncio.run(use_mcp())
```

---

## 5. 📱 **WebSocket Real-Time Interface**

### JavaScript WebSocket Client:
```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function(event) {
    console.log('🟢 Connected to BuildBridge-MCP');
    
    // Send a query
    ws.send(JSON.stringify({
        type: 'ai_query',
        query: 'What are construction safety best practices?',
        parameters: { query_type: 'safety_compliance' }
    }));
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log('📨 Received:', response);
};

ws.onclose = function(event) {
    console.log('🔴 Disconnected from BuildBridge-MCP');
};
```

---

## 🎯 **Sample Queries to Try**

### Budget Management:
- "What are the main factors causing budget overruns?"
- "How can I track construction project expenses effectively?"
- "Analyze cost variations in our current projects"

### Safety Compliance:
- "What safety protocols should be implemented on construction sites?"
- "How can I prevent workplace accidents in construction?"
- "Generate a safety checklist for high-rise construction"

### Schedule Management:
- "What are best practices for construction project scheduling?"
- "How can I handle project delays effectively?"
- "Optimize the critical path for a 6-month project"

### Quality Control:
- "What quality standards should I implement?"
- "How can I ensure construction quality compliance?"
- "Best practices for material quality inspection"

---

## 🔧 **Troubleshooting**

### Common Issues & Solutions:

#### ❌ "Module not found" errors:
```bash
# Install dependencies
pip install openai tiktoken fastapi uvicorn websockets python-dotenv

# Or use virtual environment
source construction_env/bin/activate
```

#### ❌ "API key not found":
```bash
# Set environment variable
export OPENAI_API_KEY="your-api-key-here"

# Or create .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env
```

#### ❌ "Server won't start":
```bash
# Check if port is available
netstat -tulpn | grep :8000

# Try different port
python3 production_mcp_integration.py --mode server --port 8001
```

#### ❌ "Dependencies missing":
```bash
# Quick dependency install
pip install -r requirements.txt

# Or minimal install
pip install openai fastapi uvicorn websockets tiktoken python-dotenv
```

---

## 🚀 **Performance Tips**

### Cost Optimization:
- Use `gpt-3.5-turbo` for development (cheaper)
- Monitor token usage in responses
- Set appropriate `max_tokens` limits

### Response Speed:
- Keep queries concise and specific
- Use appropriate `temperature` settings
- Cache common responses if needed

### Reliability:
- Check `/health` endpoint regularly
- Monitor error logs
- Use fallback strategies for API failures

---

## 🎉 **Ready to Use!**

Your BuildBridge-MCP system is fully operational with:

✅ **AI-Powered Construction Intelligence**  
✅ **Multiple Interface Options**  
✅ **Real-Time Processing**  
✅ **Cost Monitoring**  
✅ **Production-Ready Architecture**  

**Start with**: `python3 demo_ai_integration.py` to see all features in action!

**Next**: Launch the web server and test the API at `http://localhost:8000/docs`