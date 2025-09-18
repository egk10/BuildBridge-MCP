# Setup Instructions for Construction Management MCP

## Prerequisites

1. **Python 3.8+** installed
2. **Microsoft 365 account** with access to OneDrive and SharePoint
3. **VS Code or Cursor** as MCP client
4. **Git** for version control

## Step 1: Environment Setup

1. Clone or navigate to the project directory
2. Create a virtual environment:
   ```bash
   python -m venv construction-mcp-env
   construction-mcp-env\Scripts\activate  # Windows
   ```

3. Install required packages:
   ```bash
   pip install fastmcp pandas openpyxl msal office365-rest-python-client python-dotenv
   ```

## Step 2a: Local Mode (no Azure required)

For local development and demos, you can run entirely offline using the sample data.

1. Copy credentials template and enable local mode:
   ```bash
   copy config\credentials.json.template config\credentials.json  # Windows
   # or: cp config/credentials.json.template config/credentials.json  # macOS/Linux
   ```
2. Edit `config/credentials.json` and set:
   ```json
   {
     "local_mode": true,
     "onedrive_folder": "data/sample"
   }
   ```
3. Run tests and start the server:
   ```bash
   python test_mcp.py
   python src/main.py
   ```

In local mode, SharePoint list calls return empty arrays and the Excel connector reads from `data/sample/*`. No network calls or Azure auth are attempted.

## Step 2b: Microsoft 365 API Setup

### For Excel/OneDrive Access:
1. Go to [Azure Portal](https://portal.azure.com/)
2. Register a new application:
   - Name: "Construction MCP Server"
   - Supported account types: "Accounts in this organizational directory only"
3. Note the **Application (client) ID**
4. Under "API permissions", add:
   - Microsoft Graph → Files.Read.All
   - Microsoft Graph → Sites.Read.All
5. Generate a client secret under "Certificates & secrets"

### For SharePoint Access:
1. In the same app registration, add SharePoint permissions:
   - SharePoint → Sites.Read.All
   - SharePoint → Lists.Read.All

## Step 3: Configuration

1. Copy `config/credentials.json.template` to `config/credentials.json`
2. Fill in your Microsoft 365 credentials:
   ```json
   {
     "client_id": "your-client-id",
     "client_secret": "your-client-secret",
     "tenant_id": "your-tenant-id",
     "sharepoint_site": "https://yourcompany.sharepoint.com/sites/construction"
   }
   ```

## Step 4: Sample Data Setup

1. Create sample Excel files in `data/sample/`
2. Upload construction management data to your OneDrive
3. Configure SharePoint lists for projects, tasks, and resources

## Step 5: MCP Client Configuration

### For VS Code:
1. Install the MCP extension (if available)
2. Update VS Code settings with MCP server configuration

### For Cursor:
1. Open Cursor settings → Features → Model Context Protocol
2. Add the construction MCP server configuration

## Step 6: Testing

1. Start the MCP server:
   ```bash
   python src/main.py
   ```

2. Test with sample queries in your MCP client

## Troubleshooting

- **Authentication issues**: Verify Azure app registration permissions
- **File access problems**: Check OneDrive sharing settings
- **SharePoint errors**: Ensure site URL is correct and accessible

## Security Notes

- Never commit `credentials.json` to version control
- Use environment variables for production deployments
- Regularly rotate client secrets
- Follow your organization's data access policies