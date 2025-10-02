# 🚨 IMPORTANT: Server Modes Explained

## Two Server Modes

BuildBridge-MCP has **two different server modes** depending on your use case:

### 1. 🔌 **MCP Server Mode** (Default)
**File**: `src/main.py`  
**Start Command**: `./start_buildbridge.sh`

**Purpose**: For MCP protocol clients (VS Code, Claude Desktop, etc.)

**Communication**: stdio (standard input/output) using MCP protocol

**Behavior**: Appears "stuck" in terminal - this is normal! It's waiting for MCP messages.

**Use For**:
- VS Code MCP integration
- Claude Desktop integration  
- Other MCP clients
- Production MCP server deployment

❌ **NOT for CURL testing** - This mode doesn't accept HTTP requests!

---

### 2. 🌐 **Web Server Mode** (For Testing)
**File**: `src/production_mcp_integration.py`  
**Start Command**: `./start_web_server.sh`

**Purpose**: For HTTP/REST API testing and web interface

**Communication**: HTTP/REST API on port 8000

**Behavior**: Shows HTTP request logs, responds to CURL commands

**Use For**:
- ✅ CURL testing (our proof tests!)
- ✅ Web browser access
- ✅ REST API integration
- ✅ Swagger UI (`http://localhost:8000/docs`)

---

## 🎯 For Proof Testing, Use Web Server Mode!

```bash
# CORRECT way to start server for proof tests:
./start_web_server.sh

# Then in another terminal:
python tests/proof_tester.py
# OR
./tests/manual_curl_tests.sh
```

---

## Quick Reference

| What You Want To Do | Use This Command |
|---------------------|------------------|
| **Run proof tests with CURL** | `./start_web_server.sh` |
| **Test with Swagger UI** | `./start_web_server.sh` then visit `http://localhost:8000/docs` |
| **Use in VS Code MCP** | `./start_buildbridge.sh` |
| **Use in Claude Desktop** | `./start_buildbridge.sh` |
| **Web chat interface** | `./start_web_server.sh` |

---

## Understanding "Stuck" Behavior

### MCP Server (stdio mode) - NORMAL
```bash
$ ./start_buildbridge.sh
✅ Google Sheets connector initialized
✅ Query processor initialized
Construction Management MCP Server initialized successfully!
[cursor blinking - waiting for stdin]  ← THIS IS NORMAL!
```

**This is working correctly!** The server is waiting for MCP protocol messages via stdin. Press `Ctrl+C` to stop.

### Web Server (HTTP mode) - SHOWS LOGS
```bash
$ ./start_web_server.sh
🌐 Starting BuildBridge-MCP Web Server
Server: http://localhost:8000
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://localhost:8000
[shows HTTP request logs]
```

**This shows activity!** Each HTTP request will log in the terminal.

---

## Updated Proof Test Instructions

### Step 1: Start Web Server (NOT MCP Server!)
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
./start_web_server.sh
```

Wait for:
```
INFO:     Uvicorn running on http://localhost:8000
```

### Step 2: Generate Ground Truth
In a **new terminal**:
```bash
cd /home/egk/buildbridge-MCP/BuildBridge-MCP
python scripts/create_ground_truth.py
```

### Step 3: Run Proof Tests
```bash
python tests/proof_tester.py
```

### Step 4: Optional Manual Tests
```bash
./tests/manual_curl_tests.sh
```

---

## Troubleshooting

### ❌ "Cannot connect to server"
**Problem**: You started the MCP server instead of web server

**Solution**: 
```bash
# Stop MCP server (Ctrl+C)
# Start web server instead:
./start_web_server.sh
```

### ✅ "Server appears stuck"
**If using MCP mode**: This is normal! It's waiting for MCP messages.

**If you need HTTP**: Use web server mode instead (`./start_web_server.sh`)

### 🔍 Check Which Server is Running
```bash
# Check for web server (port 8000)
curl -s http://localhost:8000/health

# If this works, web server is running ✅
# If it fails, web server is NOT running ❌
```

---

## Updated run_proof_tests.sh

The automated workflow script has been updated to use the correct server mode. But if you're running manually, remember:

**For proof testing**: Use `./start_web_server.sh` not `./start_buildbridge.sh`

---

**Last Updated**: October 1, 2025  
**Issue**: Server mode confusion clarified
