# BuildBridge-MCP 🏗️

**Bridge your construction data with AI-powered natural language queries**

A Model Context Protocol (MCP) server that connects Excel files, SharePoint data, and construction documents into one intelligent interface. Ask questions in plain English and get instant insights from your construction projects.

## Overview

BuildBridge-MCP enables natural language querying of construction management data stored across:
- Excel files in OneDrive
- SharePoint Lists
- Local document repositories

Based on the architecture from [KDnuggets MCP Data Science Article](https://www.kdnuggets.com/built-an-mcp-to-automate-my-data-science-job).

## Architecture

The system consists of three main components:

1. **Excel Data Connector** - Processes Excel files with project data, budgets, schedules
2. **SharePoint Connector** - Accesses SharePoint lists and document libraries
3. **Query Processing Engine** - Understands natural language and routes to appropriate data sources

## Project Structure

```
BuildBridge-MCP/
├── src/
│   ├── main.py                 # Main MCP server
│   ├── connectors/
│   │   ├── excel_connector.py  # Excel/OneDrive integration
│   │   ├── sharepoint_connector.py # SharePoint integration
│   │   └── document_indexer.py # Document search and indexing
│   └── query_processor.py      # Natural language query processing
├── config/
│   ├── mcp_config.json         # MCP server configuration
│   └── credentials.json        # API credentials (not in git)
├── data/
│   └── sample/                 # Sample construction data
└── docs/
    └── setup.md               # Setup instructions
```

## Features

- Natural language queries like "What's the status of Project ABC?"
- Budget analysis and cost tracking
- Schedule monitoring and milestone tracking
- Resource allocation insights
- Compliance and safety report generation

## Getting Started

See `docs/setup.md` for detailed setup instructions.

## Example Queries

- "Show me all projects that are over budget this month"
- "What's the completion percentage for the downtown office building?"
- "List all safety incidents from the last quarter"
- "Which subcontractors are working on active projects?"
- "Generate a status report for projects ending this month"

## 🚀 Quick Start

1. Clone and install
   ```bash
   git clone https://github.com/egk10/BuildBridge-MCP.git
   cd BuildBridge-MCP
   pip install -r requirements.txt
   ```

2. Local Mode (no Azure required)
   ```bash
   # Copy template and enable local mode
   copy config\credentials.json.template config\credentials.json  # Windows
   # or: cp config/credentials.json.template config/credentials.json  # macOS/Linux
   # Then open config/credentials.json and set:
   #   "local_mode": true
   #   "onedrive_folder": "data/sample"
   ```

3. Test
   ```bash
   python test_mcp.py
   ```

4. Start the MCP server
   ```bash
   python src/main.py
   ```

5. Connect your MCP client (VS Code or Cursor)
   - See `docs/vscode_setup.md` for configuration

Want real SharePoint/OneDrive data? Disable local mode and add your Azure credentials; see `docs/setup.md`.

## 📊 Features

- **Natural Language Queries**: Ask questions in plain English
- **Multi-Source Integration**: Excel, SharePoint, and document libraries
- **Real-Time Data**: Live access to your construction management data
- **Intelligent Search**: AI-powered document and data discovery
- **Comprehensive Reports**: Budget analysis, project status, safety reports

## 🏗️ Architecture

Built on the Model Context Protocol (MCP) framework, BuildBridge-MCP consists of:

1. **Excel Connector** - Processes Excel files with project data, budgets, schedules
2. **SharePoint Connector** - Accesses SharePoint lists and document libraries  
3. **Document Indexer** - Intelligent search across construction documents
4. **Query Processor** - Natural language understanding and routing

## 📁 Sample Data

The repository includes realistic sample construction data:
- 7 construction projects with budgets and timelines
- Task schedules and resource allocations
- Budget tracking with variance analysis
- Ready-to-test project scenarios

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines and submit pull requests for any improvements.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Based on the MCP architecture from [KDnuggets Data Science MCP Article](https://www.kdnuggets.com/built-an-mcp-to-automate-my-data-science-job)
- Built with [FastMCP](https://github.com/jxnl/fastmcp) framework
- Inspired by the need for better construction data accessibility