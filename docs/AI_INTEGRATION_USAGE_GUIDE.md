# BuildBridge-MCP AI Integration Usage Guide

## 🚀 Quick Start with AI Features

### 1. Environment Setup
```bash
# Activate the virtual environment
source construction_env/bin/activate

# Set your OpenAI API key
export OPENAI_API_KEY='your-openai-api-key-here'

# Run the demo to verify everything works
python demo_ai_integration.py

# Start the production server
python production_mcp_integration.py --mode server
```

### 2. Using the AI Service

#### Python Client API
```python
from production_mcp_integration import ConstructionMCPClient

# Initialize client
client = ConstructionMCPClient()
await client.initialize()

# AI-powered construction queries
result = await client.ai_query(
    query="What factors should I consider for construction budget planning?",
    query_type="budget_analysis",
    include_data_context=True
)

print(f"AI Response: {result['ai_response']}")
print(f"Confidence: {result['confidence_score']:.2f}")
print(f"Cost: ${result['cost_estimate']:.4f}")

# Get usage statistics
stats = await client.get_ai_usage_stats()
print(f"Today's usage: {stats['daily_summary']}")
```

#### REST API
```bash
# Basic AI query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I manage construction project delays?",
    "type": "ai_query",
    "parameters": {
      "query_type": "schedule_management",
      "include_data_context": true
    }
  }'

# Enhanced query (without AI)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me budget variance analysis",
    "type": "enhanced_query",
    "parameters": {
      "prompt_type": "budget_analysis"
    }
  }'
```

### 3. Query Types and Use Cases

#### Budget Analysis (`budget_analysis`)
```python
# Examples of budget-related queries
queries = [
    "What's causing our cost overruns?",
    "How can we optimize our construction budget?",
    "Analyze our spending patterns this quarter",
    "What are the main budget risk factors?"
]

for query in queries:
    result = await client.ai_query(query, query_type="budget_analysis")
    print(f"Q: {query}")
    print(f"A: {result['ai_response'][:100]}...")
```

#### Safety Compliance (`safety_compliance`)
```python
# Safety-related queries
safety_queries = [
    "What safety protocols should we implement?",
    "How to prevent common construction accidents?",
    "OSHA compliance checklist for our site",
    "Emergency response procedures for construction sites"
]
```

#### Schedule Management (`schedule_management`)
```python
# Schedule-related queries
schedule_queries = [
    "How to compress our project timeline?",
    "What causes typical construction delays?",
    "Resource allocation for faster completion",
    "Critical path optimization strategies"
]
```

#### Quality Control (`quality_control`)
```python
# Quality-related queries
quality_queries = [
    "Quality inspection procedures for concrete work",
    "How to ensure building code compliance?",
    "Defect prevention in construction",
    "Material testing requirements"
]
```

### 4. Monitoring and Analytics

#### Health Check
```bash
curl http://localhost:8000/health
```

Response includes AI service status:
```json
{
  "status": "healthy",
  "services": {
    "ai_service": true
  },
  "ai_service_info": {
    "enabled": true,
    "model": "gpt-4-turbo",
    "usage_stats": {
      "daily_summary": {
        "total_tokens": 1250,
        "total_cost": 0.0425,
        "request_count": 8
      }
    }
  }
}
```

#### Real-Time Logs
```bash
# View logs via HTTP
curl http://localhost:8000/logs

# Or use WebSocket for real-time streaming
# Connect to ws://localhost:8000/ws/logs
```

### 5. Configuration Options

#### AI Service Configuration (`config/credentials.json`)
```json
{
  "ai_service": {
    "openai_api_key": "${OPENAI_API_KEY}",
    "model": "gpt-4-turbo",           // Model to use
    "max_tokens": 2000,               // Max response length
    "temperature": 0.1,               // Response randomness (0-1)
    "max_retries": 3,                 // API retry attempts
    "retry_delay": 1.0                // Delay between retries
  }
}
```

#### Supported Models
- `gpt-4` - Most capable, higher cost
- `gpt-4-turbo` - Fast and capable (recommended)
- `gpt-3.5-turbo` - Faster, lower cost

### 6. Cost Management

#### Token Usage Tracking
```python
# Get detailed usage statistics
stats = ai_service.get_usage_stats()
print(f"Total cost today: ${stats['daily_summary']['total_cost']:.4f}")
print(f"Average tokens per request: {stats['daily_summary']['average_tokens_per_request']:.1f}")

# Export usage history
ai_service.export_usage_history('usage_report.json')
```

#### Cost Optimization Tips
1. **Use appropriate models**: GPT-3.5 Turbo for simple queries, GPT-4 for complex analysis
2. **Optimize prompts**: Clear, specific queries get better results with fewer tokens
3. **Monitor usage**: Check daily summaries and set up alerts for high usage
4. **Batch queries**: Process multiple related questions in a single request when possible

### 7. Error Handling and Fallbacks

The AI service includes comprehensive error handling:

```python
# AI service automatically handles:
# - API rate limits (exponential backoff)
# - Network errors (retry logic)
# - Invalid API keys (graceful fallback)
# - Service outages (fallback to enhanced queries)

result = await client.ai_query("What's the project status?")

if "error" in result:
    print(f"AI service unavailable: {result['error']}")
    if "fallback_data" in result:
        print(f"Using fallback: {result['fallback_data']}")
else:
    print(f"AI response: {result['ai_response']}")
```

### 8. WebSocket Real-Time Communication

```javascript
// Connect to WebSocket for real-time AI queries
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = function() {
    // Send AI query
    ws.send(JSON.stringify({
        type: 'ai_query',
        query: 'What are the current project risks?',
        parameters: {
            query_type: 'general',
            include_data_context: true
        }
    }));
};

ws.onmessage = function(event) {
    const response = JSON.parse(event.data);
    console.log('AI Response:', response.data.ai_response);
    console.log('Confidence:', response.data.confidence_score);
};
```

### 9. Integration with Existing Data

The AI service automatically includes relevant data context:

```python
# When processing queries about projects or budgets,
# the system automatically gathers relevant data
result = await client.ai_query(
    "Analyze our current project performance",
    query_type="general",
    include_data_context=True  # Includes project data automatically
)

# The AI response will reference actual project data
print(result['has_context'])  # True if data was included
```

### 10. Production Deployment

#### Environment Variables
```bash
# Required
export OPENAI_API_KEY='your-api-key'

# Optional
export AI_MODEL='gpt-4-turbo'
export AI_MAX_TOKENS='2000'
export AI_TEMPERATURE='0.1'
```

#### Docker Deployment
```dockerfile
# Add to your Dockerfile
ENV OPENAI_API_KEY=${OPENAI_API_KEY}
ENV AI_MODEL=gpt-4-turbo
ENV AI_MAX_TOKENS=2000
```

#### Monitoring Alerts
Set up monitoring for:
- High API usage (cost control)
- API errors (service reliability)
- Response times (performance)
- Token consumption patterns (optimization)

---

## 🎯 Best Practices

### 1. Query Optimization
- Be specific and clear in your questions
- Use appropriate query types for better results
- Include relevant context when available

### 2. Cost Management
- Monitor daily usage through health endpoints
- Use GPT-3.5 Turbo for simple queries
- Set up cost alerts for budget control

### 3. Error Handling
- Always check for errors in responses
- Use fallback data when AI service is unavailable
- Implement retry logic for critical operations

### 4. Security
- Never expose API keys in client-side code
- Use environment variables for configuration
- Monitor API usage for unusual patterns

---

## 🔧 Troubleshooting

### Common Issues

#### "AI service not available"
- Check OPENAI_API_KEY environment variable
- Verify API key is valid and has credit
- Check network connectivity

#### High response times
- Consider using gpt-3.5-turbo for faster responses
- Reduce max_tokens for shorter responses
- Check current OpenAI API status

#### "Import module not found"
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python path configuration

### Support
- Check logs at `/logs` endpoint
- Run `python demo_ai_integration.py` for diagnostics
- Review `test_ai_integration.py` for validation

---

**🏗️ You're now ready to leverage AI-powered construction management with BuildBridge-MCP!**