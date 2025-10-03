# VS Code MCP Configuration Guide

## Setting up VS Code as MCP Client

### Option 1: Using VS Code Settings

1. Open VS Code
2. Go to File → Preferences → Settings (or `Ctrl+,`)
3. Search for "Model Context Protocol" or "MCP"
4. If you have the MCP extension installed, you'll see MCP settings
5. Add the configuration from `config/mcp_config.json`

### Option 2: Using Cursor (Recommended)

If you have Cursor installed:

1. Open Cursor
2. Go to Cursor → Settings → Features → Model Context Protocol
3. Click "Add MCP Server"
4. Copy the configuration from `config/mcp_config.json`

### Option 3: Manual Configuration

1. Create or edit your VS Code `settings.json` file:
   - On Windows: `%APPDATA%\Code\User\settings.json`
   - On macOS: `~/Library/Application Support/Code/User/settings.json`
   - On Linux: `~/.config/Code/User/settings.json`

2. Add the MCP server configuration:

```json
{
  "mcp.servers": {
    "construction-management": {
      "command": "python",
      "args": ["src/main.py"],
      "cwd": "c:/Users/eliek/Data Science MCP/construction-management-mcp",
      "env": {
        "PYTHONPATH": "c:/Users/eliek/Data Science MCP/construction-management-mcp/src"
      }
    }
  }
}
```

## Testing the Configuration

1. Ensure you have completed the credential setup in `config/credentials.json`
2. Install the required Python packages:
   ```bash
   cd "c:/Users/eliek/Data Science MCP/construction-management-mcp"
   pip install -r requirements.txt
   ```

3. Test the MCP server manually:
   ```bash
   cd "c:/Users/eliek/Data Science MCP/construction-management-mcp"
   python src/main.py
   ```

4. If using Cursor, you should see the Construction Management MCP in the available tools
5. Try a test query like: "Show me all active projects"

## Troubleshooting

### Common Issues:

1. **Python not found**: Ensure Python is in your system PATH
2. **Module import errors**: Check that all dependencies are installed
3. **Authentication errors**: Verify your Project A app registration and credentials
4. **File not found errors**: Check that all file paths are correct

### Error Messages:

- `"MCP server not properly initialized"`: Check credentials.json and Project A setup
- `"Failed to download Excel file"`: Verify OneDrive permissions and file paths
- `"Failed to get items from list"`: Check SharePoint site URL and list names

## Available MCP Tools

Once configured, you'll have access to these tools in your AI assistant:

1. **search_projects**: Find projects by natural language criteria
2. **get_project_status**: Get detailed status for specific projects
3. **analyze_budget**: Perform budget analysis and variance reporting
4. **get_schedule_updates**: Check upcoming milestones and delays
5. **search_documents**: Find construction documents by keywords
6. **generate_report**: Create various construction management reports

## Example Queries

Try these natural language queries with your MCP-enabled AI assistant:

- "Show me all projects that are over budget"
- "What's the status of project ABC-123?"
- "List upcoming milestones for the next 30 days"
- "Find all safety incident reports from this month"
- "Generate a budget analysis report"
- "Search for electrical drawings"
- "Which subcontractors are working on active projects?"

## Security Notes

- Keep your `credentials.json` file secure and never commit it to version control
- Regularly rotate your Project A app client secrets
- Ensure your SharePoint site has appropriate access controls
- Monitor MCP server logs for any unusual activity