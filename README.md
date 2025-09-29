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

## 📋 **Project Structure**

```
BuildBridge-MCP/
├── VALUE_PROPOSITION.md          # Complete business case and market analysis
├── src/                          # Core MCP implementation
│   ├── main.py                   # Main MCP server
│   ├── connectors/               # Data connectors
│   ├── query_processor.py        # Natural language query processing
│   └── ai_service.py             # AI integration service
├── tests/                        # Test files
├── examples/                     # Demo and example scripts
├── docs/                         # Technical documentation
├── scripts/                      # Utility scripts
├── config/                       # Configuration files
├── data/                         # Sample data and datasets
├── static/                       # Web interface files
├── deploy/                       # Deployment configurations
├── ssl/                          # SSL certificates
└── logs/                         # Log files
```

## 🔒 Security Notice

**⚠️ NEVER commit credential files to version control!**

The following files contain sensitive information and are already in `.gitignore`:
- `.env` - Environment variables with API keys
- `config/client_secret.json` - Google OAuth credentials
- `config/credentials.json` - Service account keys and project configs
- `config/token.pickle` - OAuth access tokens

### Setup Instructions:
1. Copy `.env.template` to `.env` and fill in your credentials
2. For development, you can still use local config files as fallback
3. For production, use environment variables only

### Security Documentation:
See [`docs/SECURITY_CONFIG_GUIDE.md`](docs/SECURITY_CONFIG_GUIDE.md) for comprehensive security configuration and best practices.

### If you accidentally commit credentials:
1. Remove files from git: `git rm --cached <file>`
2. Use BFG Repo Cleaner to remove from history: `bfg --delete-files <filename>`
3. Regenerate compromised credentials

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


## 🚦 Quick Start on New Hardware

See [docs/copilot-continue.md](docs/copilot-continue.md) for step-by-step setup and Copilot Chat resume instructions.

Or use the Ubuntu one-liner:
```bash
curl -fsSL https://raw.githubusercontent.com/egk10/BuildBridge-MCP/main/scripts/bootstrap_ubuntu.sh | bash
```

---

## 🚀 Production Deployment

BuildBridge-MCP supports secure production deployment using Docker and environment variables.

### Prerequisites
- Docker and Docker Compose installed
- Production Google OAuth credentials
- Production OpenAI API key
- SSL certificates (optional but recommended)

### Quick Production Deploy

1. **Configure Environment**
   ```bash
   # Copy production template
   cp .env.production.template .env
   
   # Edit with your production credentials
   nano .env
   ```

2. **Deploy with One Command**
   ```bash
   cd deploy
   ./deploy-production.sh
   ```

### Production Services
- **BuildBridge-MCP API**: `http://localhost:8002`
- **Nginx Reverse Proxy**: `http://localhost:8081`
- **Grafana Dashboard**: `http://localhost:3003` (admin/admin)
- **Prometheus Metrics**: `http://localhost:9092`

### Environment Variables Required
See `.env.production.template` for all required variables including:
- Google OAuth credentials
- Google Sheets project IDs
- OpenAI API configuration
- Database and Redis settings
- SSL certificate paths

### Security Features
- ✅ Environment variable priority over local files
- ✅ No sensitive data in Docker images
- ✅ Automatic SSL/TLS support
- ✅ Health checks and monitoring
- ✅ Production logging and metrics

### Management Commands
```bash
cd deploy
docker-compose logs -f           # View logs
docker-compose restart          # Restart services
docker-compose down             # Stop deployment
docker-compose pull && docker-compose up -d  # Update
```

## � Ubuntu one-liner bootstrap

On a fresh Ubuntu Desktop machine, run this to clone, create a venv, install deps, enable local mode, run tests, and optionally start the server:

```bash
curl -fsSL https://raw.githubusercontent.com/egk10/BuildBridge-MCP/main/scripts/bootstrap_ubuntu.sh | bash
```

Environment variables (optional):
- REPO_URL: repo to clone (default: https://github.com/egk10/BuildBridge-MCP.git)
- BRANCH: branch to use (default: main)
- DIR: target dir (default: BuildBridge-MCP)
- START_SERVER: set to true to start server after setup (default: false)

Example starting server automatically:
```bash
START_SERVER=true curl -fsSL https://raw.githubusercontent.com/egk10/BuildBridge-MCP/main/scripts/bootstrap_ubuntu.sh | bash
```

## 🧰 Helper scripts

- `start_buildbridge.sh` — **Recommended**: Auto-detects and activates venv, then starts MCP server
   ```bash
   ./start_buildbridge.sh          # Start server
   ./start_buildbridge.sh --test   # Run initialization test
   ```
- `scripts/start_server.sh` — activate venv and run server (legacy)
   ```bash
   bash scripts/start_server.sh
   ```

## �📊 Features

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

## Continue Copilot Chat on new hardware

See `docs/copilot-continue.md` for a quick, copy-paste checklist to rehydrate your environment and resume this chat on another machine.