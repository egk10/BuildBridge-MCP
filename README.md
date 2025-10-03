# BuildBridge-MCP 🏗️

[![Version](https://img.shields.io/badge/version-2.1.0-blue.svg)](https://github.com/egk10/BuildBridge-MCP/releases/tag/v2.1.0)
[![Status](https://img.shields.io/badge/status-production%20ready-green.svg)]()
[![Configuration](https://img.shields.io/badge/config-.env%20only-brightgreen.svg)]()

**Bridge your construction data with AI-powered natural language queries**

A Model Context Protocol (MCP) server that connects Google Sheets, Google Drive, and construction documents into one intelligent interface. Ask questions in plain English and get instant insights from your construction projects.

## Overview

BuildBridge-MCP enables natural language querying of construction management data stored in:
- ✅ **Google Sheets** - Project budgets, schedules, cost tracking, GCA stats
- ✅ **Google Drive** - Construction documents and specifications
- 🔄 **Excel files in OneDrive** _(Roadmap)_
- 🔄 **SharePoint Lists** _(Roadmap)_
- 🔄 **Local document repositories** _(Roadmap)_

### What's New in v2.1.0 🎉

- **📝 .env-only Configuration** - 95% simpler! Just 2 lines per project (was 42 lines)
- **🎯 Convention-Based Defaults** - Smart defaults work for 95% of projects
- **⚡ 10x Faster Onboarding** - Add new project in 30 seconds (was 5+ minutes)
- **🔒 Enhanced Security** - Single source of truth for all credentials
- **📚 Comprehensive Docs** - Production deployment guide + 1,500 lines of documentation

See [docs/VERSION_2.0_RELEASE_NOTES.md](docs/VERSION_2.0_RELEASE_NOTES.md) for complete changelog.

## Architecture

The system consists of three main components:

1. **Google Sheets Connector** - Processes Google Sheets with project data, budgets, schedules, GCA statistics
2. **Configuration System** - Convention-based .env-only configuration with smart defaults
3. **Query Processing Engine** - AI-powered natural language understanding and intelligent routing
4. **Web Chat Interface** - Interactive chat UI with project selection and query suggestions

### Planned Components (Roadmap)
- SharePoint Connector - Access SharePoint lists and document libraries
- Excel Connector - Process Excel files with project data
- Document Indexer - Intelligent search across construction documents

## 📋 Project Structure

```
BuildBridge-MCP/
├── src/                          # Core MCP implementation
│   ├── main.py                   # Main MCP server entrypoint
│   ├── connectors/               # Data connectors
│   ├── query_processor.py        # Natural language query orchestration
│   └── ai_service.py             # AI integration service
├── docs/                         # Technical documentation portal
│   ├── guides/                   # Step-by-step setup and tooling guides
│   │   └── GOOGLE_DRIVE_SETUP_GUIDE.md
│   ├── reports/                  # Executive and analytical reports
│   │   └── VALUE_PROPOSITION.md
│   ├── runbook/                  # Operational runbooks
│   └── archives/                 # Historical plans & conversation logs
├── scripts/                      # Utility and bootstrap scripts
├── tests/                        # Automated tests
├── examples/                     # Demo and example scripts
├── config/                       # Configuration templates and manifests
├── data/                         # Sample data and datasets
├── deploy/                       # Deployment configurations
├── static/                       # Web interface assets
├── ssl/                          # SSL certificates
└── logs/                         # Log files
```

## 🔒 Security Notice

**⚠️ NEVER commit credential files to version control!**

The following files contain sensitive information and are already in `.gitignore`:
- `.env` - Environment variables with API keys and project configuration
- `config/client_secret.json` - Google OAuth credentials
- `config/token.pickle` - OAuth access tokens

### Quick Setup (v2.1.0 - Simplified!):
1. **Copy template:**
   ```bash
   cp .env.template .env
   ```

2. **Add your credentials and projects:**
   ```bash
   # Google OAuth (from Google Cloud Console)
   GOOGLE_CLIENT_ID=your-client-id
   GOOGLE_CLIENT_SECRET=your-secret
   OPENAI_API_KEY=your-openai-key
   
   # Projects (just 2 lines each!)
   GOOGLE_SHEETS_PROJECT_1_NAME=ProjectA
   GOOGLE_SHEETS_PROJECT_1_ID=your-spreadsheet-id
   ```

3. **That's it!** Smart defaults handle the rest.

### What Happened to JSON Files?
**v2.1.0 eliminated complex JSON configuration!** The new .env-only system:
- ✅ 95% simpler (2 lines vs 42 lines per project)
- ✅ Convention-based defaults work for 95% of projects
- ✅ Optional per-project overrides for edge cases
- ✅ Backward compatible (old JSON files still work as fallback)

See [`docs/ENV_ONLY_CONFIG_COMPLETE.md`](docs/ENV_ONLY_CONFIG_COMPLETE.md) for migration guide.

### Security Documentation:
- Configuration Guide: [`docs/ENV_ONLY_CONFIG_COMPLETE.md`](docs/ENV_ONLY_CONFIG_COMPLETE.md)
- Production Deployment: [`docs/PRODUCTION_DEPLOYMENT.md`](docs/PRODUCTION_DEPLOYMENT.md)

### If you accidentally commit credentials:
1. Remove files from git: `git rm --cached <file>`
2. Use BFG Repo Cleaner to remove from history: `bfg --delete-files <filename>`
3. Regenerate compromised credentials

## Features

### Current (v2.1.0)
- ✅ Natural language queries like "What's the status of Project P?"
- ✅ Budget analysis and cost tracking from Google Sheets
- ✅ GCA (Gross Construction Area) statistics and unit cost calculations
- ✅ Project summary data with area, units, and parking info
- ✅ Multi-project support with dynamic discovery
- ✅ Web Chat V2 interface with project selection
- ✅ AI-powered query suggestions per project
- ✅ Convention-based configuration (add projects in 30 seconds!)

### Roadmap
- 🔄 Schedule monitoring and milestone tracking
- 🔄 Resource allocation insights
- 🔄 Compliance and safety report generation
- 🔄 SharePoint Lists integration
- 🔄 Excel files in OneDrive support
- 🔄 Document search and indexing

## Getting Started

### Prerequisites
- Python 3.8 or higher
- Google Cloud Project with Sheets API enabled
- OpenAI API key
- Google OAuth 2.0 credentials

### Quick Start

1. **Clone and setup:**
   ```bash
   git clone https://github.com/egk10/BuildBridge-MCP.git
   cd BuildBridge-MCP
   python -m venv buildbridge_venv
   source buildbridge_venv/bin/activate  # On Windows: buildbridge_venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure (v2.1.0 - Super Easy!):**
   ```bash
   cp .env.template .env
   # Edit .env with your credentials and project IDs
   ```

3. **Start the server:**
   ```bash
   ./start_buildbridge.sh
   ```

4. **Access Web Chat:**
   Open `http://localhost:8000` in your browser

### Detailed Setup Guides
- **Google Sheets Setup:** [`docs/guides/GOOGLE_DRIVE_SETUP_GUIDE.md`](docs/guides/GOOGLE_DRIVE_SETUP_GUIDE.md)
- **Configuration Guide:** [`docs/ENV_ONLY_CONFIG_COMPLETE.md`](docs/ENV_ONLY_CONFIG_COMPLETE.md)
- **Production Deployment:** [`docs/PRODUCTION_DEPLOYMENT.md`](docs/PRODUCTION_DEPLOYMENT.md)

## Example Queries

### Current Capabilities (Google Sheets)
- "Show me the budget for Project P"
- "What's the total direct cost for Project Y?"
- "Calculate cost per square foot for Project A"
- "Show building area and residential units for Project P"
- "What are the parking details for Project Y?"
- "Compare GCA statistics across all projects"

### Roadmap (Coming Soon)
- "Show me all projects that are over budget this month"
- "What's the completion percentage for the downtown office building?"
- "List all safety incidents from the last quarter"
- "Which subcontractors are working on active projects?"
- "Generate a status report for projects ending this month"


## 🚦 Quick Start on New Hardware

See the docs folder for step-by-step setup and environment rehydration instructions.

Or use the Ubuntu one-liner:
```bash
curl -fsSL https://raw.githubusercontent.com/egk10/BuildBridge-MCP/main/scripts/bootstrap_ubuntu.sh | bash
```

---

## 🚀 Production Deployment

BuildBridge-MCP v2.1.0 features a **simplified .env-only configuration** for production deployment.

### Quick Production Deploy

1. **Configure Environment**
   ```bash
   # Copy template
   cp .env.template .env
   
   # Edit with production credentials
   nano .env
   ```

2. **Set production values:**
   ```bash
   # Production Google OAuth
   GOOGLE_CLIENT_ID=production-client-id
   GOOGLE_CLIENT_SECRET=production-secret
   
   # Production Projects (just 2 lines each!)
   GOOGLE_SHEETS_PROJECT_1_NAME=ProductionProject
   GOOGLE_SHEETS_PROJECT_1_ID=production-sheet-id
   
   # Production OpenAI
   OPENAI_API_KEY=production-key
   OPENAI_MODEL=gpt-4o
   
   # Production settings
   LOCAL_MODE=false
   LOG_LEVEL=WARNING
   DEBUG=false
   ```

3. **Deploy**
   ```bash
   # Install production dependencies
   pip install -r requirements-production.txt
   
   # Start server
   export PYTHONPATH="$(pwd)/src:${PYTHONPATH:-}"
   nohup python src/production_mcp_integration.py \
       --mode server --host 0.0.0.0 --port 8000 \
       > logs/server.log 2>&1 &
   ```

### Production Features (v2.1.0)
- ✅ Single .env file configuration (no JSON editing!)
- ✅ Smart defaults for 95% of use cases
- ✅ Optional per-project overrides
- ✅ Backward compatible with v1.x JSON configs
- ✅ Environment variable priority
- ✅ Comprehensive deployment guide
- ✅ Security best practices included

### Management & Monitoring

**Using systemd (recommended):**
```bash
# See docs/PRODUCTION_DEPLOYMENT.md for systemd setup
sudo systemctl start buildbridge-mcp
sudo systemctl status buildbridge-mcp
sudo journalctl -u buildbridge-mcp -f
```

**Health checks:**
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/projects | jq
```

### Complete Production Guide
See [`docs/PRODUCTION_DEPLOYMENT.md`](docs/PRODUCTION_DEPLOYMENT.md) for:
- Systemd service configuration
- Nginx reverse proxy setup
- SSL/TLS configuration
- Monitoring and alerting
- Backup strategies
- Troubleshooting procedures

### Docker Deployment (Legacy)
Docker deployment is still supported but **v2.1.0's .env-only system** makes native deployment much simpler. Docker instructions available in `deploy/` directory.

## 🐧 Ubuntu one-liner bootstrap

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

## 📊 Feature Highlights

### Current Features (v2.1.0)
- **🤖 AI-Powered Queries** – Ask questions in plain English about your construction projects
- **📊 Google Sheets Integration** – Real-time access to project budgets, schedules, and GCA stats
- **💬 Web Chat Interface V2** – Interactive chat with project selection and smart query suggestions
- **⚡ 10x Faster Configuration** – Add new projects in 30 seconds (was 5+ minutes)
- **🎯 Convention-Based Config** – Smart defaults work for 95% of projects, zero JSON editing
- **🔒 Enhanced Security** – Single .env file for all credentials, properly gitignored
- **📈 Portfolio Analysis** – AI-driven calculations across multiple projects
- **🔄 Real-Time Updates** – Cache refresh from live Google Sheets on demand

### Roadmap Features
- **Multi-source federation** – Blend Excel, SharePoint, and document libraries seamlessly
- **Semantic document search** – Surface the right specs, RFIs, and reports instantly
- **Automated reporting** – Generate compliance, status, and variance summaries on demand
- **Schedule tracking** – Monitor milestones and critical path analysis
- **Resource management** – Track labor, materials, and equipment allocation

## 🏗️ Architecture

Built on the Model Context Protocol (MCP) framework, BuildBridge-MCP v2.1.0 consists of:

### Current Implementation
1. **Google Sheets Connector** - Real-time access to project data, budgets, schedules, and GCA statistics
2. **Configuration System** - Convention-based .env-only configuration with smart defaults
3. **Query Processor** - AI-powered natural language understanding and intelligent routing
4. **Web Chat Interface V2** - Interactive UI with project selection and query suggestions
5. **AI Service** - OpenAI GPT-4 integration for natural language processing
6. **Cache System** - File-based caching with refresh-on-demand capability

### Planned Components (Roadmap)
- **SharePoint Connector** - Access SharePoint lists and document libraries
- **Excel Connector** - Process Excel files from OneDrive
- **Document Indexer** - Intelligent search across construction documents
- **Database Backend** - PostgreSQL for multi-instance support
- **Redis Cache** - Distributed caching for horizontal scaling

## 📁 Sample Data

The repository includes realistic sample construction project data for testing:
- 3 anonymized construction projects (P, Y, A) with complete data
- Project budgets and GCA statistics
- Cost breakdowns (project summary, below grade, above grade)
- Real-world data structure from actual construction projects
- Ready-to-test scenarios with Web Chat V2 interface

**Note:** All sample data uses anonymized project names to maintain confidentiality.

## 🤝 Contributing

We welcome contributions! Please read our contributing guidelines and submit pull requests for any improvements.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need for better construction data accessibility
- Built with [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) framework
- Powered by OpenAI GPT-4 for natural language understanding
- Special thanks to the construction management community for feedback

## 📚 Documentation

### Getting Started
- [Google Drive Setup Guide](docs/guides/GOOGLE_DRIVE_SETUP_GUIDE.md)
- [Configuration Guide (v2.1.0)](docs/ENV_ONLY_CONFIG_COMPLETE.md)
- [Production Deployment](docs/PRODUCTION_DEPLOYMENT.md)

### Version History
- [Version 2.1.0 Release Notes](docs/VERSION_2.0_RELEASE_NOTES.md)
- [Configuration Consolidation Proposal](docs/CONFIG_CONSOLIDATION_PROPOSAL.md)

### Technical Details
- [Project Structure](docs/) - Comprehensive documentation portal
- [Value Proposition](docs/reports/VALUE_PROPOSITION.md)
   - Continue development on new hardware - see docs/ for setup and rehydration guides

## 🔄 Version History

- **v2.1.0** (Oct 3, 2025) - Configuration Consolidation
  - .env-only configuration system (95% simpler)
  - Convention-based defaults
  - Production deployment guide
  - 1,500+ lines of new documentation
  
- **v2.0.0** (Oct 2, 2025) - Chat Interface V2 + AI Portfolio
  - Dynamic project sidebar
  - AI-driven portfolio calculations
  - 50% test pass rate improvement
  - 2,171 lines of documentation
  
- **v1.x** - Initial Google Sheets integration

