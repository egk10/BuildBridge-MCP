# 🏗️ BuildBridge-MCP - Quick Start for Proof Testing

## ⚡ Quick Start (3 Steps)

### 1. Start Web Server
```bash
./start_web_server.sh
```
Wait until you see: `INFO:     Uvicorn running on http://localhost:8000`

### 2. Run Tests (in new terminal)
```bash
./scripts/run_proof_tests.sh
```

That's it! ✅

---

## 🚨 Important: Server Modes

BuildBridge has **TWO server modes**:

### 🔌 MCP Server (`./start_buildbridge.sh`)
- **For**: VS Code, Claude Desktop, MCP clients
- **Protocol**: stdio/MCP  
- **Appears "stuck"**: ✅ This is normal!

### 🌐 Web Server (`./start_web_server.sh`)
- **For**: CURL testing, HTTP API, proof tests
- **Protocol**: HTTP/REST
- **Shows logs**: ✅ HTTP requests visible

**For proof testing, use `./start_web_server.sh`** ⚠️

---

## 📚 Full Documentation

- **[PROOF_TEST_PLAN.md](docs/PROOF_TEST_PLAN.md)** - Complete testing strategy
- **[SERVER_MODES_EXPLAINED.md](docs/SERVER_MODES_EXPLAINED.md)** - Server modes explained
- **[PROOF_TEST_QUICK_REFERENCE.md](docs/PROOF_TEST_QUICK_REFERENCE.md)** - Quick reference
- **[README_PROOF_TESTS.md](tests/README_PROOF_TESTS.md)** - Test suite guide

---

## ✅ Checklist

Before running tests:
- [ ] Web server started (`./start_web_server.sh`)
- [ ] Server responds: `curl http://localhost:8000/health`
- [ ] Google Sheets cache exists: `ls cache/normalized/*.json`

Then run: `./scripts/run_proof_tests.sh`

---

**Not working?** See [SERVER_MODES_EXPLAINED.md](docs/SERVER_MODES_EXPLAINED.md)
