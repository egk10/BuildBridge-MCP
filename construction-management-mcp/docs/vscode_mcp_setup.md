# VS Code MCP Setup Guide

## 1. Install VS Code MCP Extension

First, install the MCP extension in VS Code:
- Open VS Code
- Go to Extensions (Ctrl+Shift+X)
- Search for "MCP" or "Model Context Protocol"
- Install the official MCP extension

## 2. Configure MCP Settings

Create or update your VS Code settings to connect to your construction MCP server:

1. Open VS Code Settings (Ctrl+,)
2. Search for "MCP"
3. Add your server configuration

### Example MCP Configuration:

```json
{
  "mcp.servers": {
    "construction-mcp": {
      "command": "python",
      "args": ["src/main.py"],
      "cwd": "/home/egk/buildbridge-MCP/BuildBridge-MCP/construction-management-mcp",
      "env": {
        "VIRTUAL_ENV": "/home/egk/buildbridge-MCP/BuildBridge-MCP/construction-management-mcp/construction_env"
      }
    }
  }
}
```

## 3. Start Using Your Construction MCP

Once configured, you can:
- Open the MCP panel in VS Code
- Connect to your "construction-mcp" server
- Start asking construction-related questions!

### Example Queries to Try:
- "What projects are currently over budget?"
- "Show me the schedule for active projects"
- "Analyze budget variance for this quarter"
- "Search for safety incident documents"
- "Generate a project status report"

## 4. Troubleshooting

If connection fails:
1. Make sure your virtual environment is activated
2. Check that all dependencies are installed
3. Verify the file paths in your configuration
4. Look at VS Code's output panel for MCP logs