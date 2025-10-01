# Continue Copilot Chat on New Hardware

Use this quick checklist to rehydrate your development environment and pick up where you left off.

## 1) Clone and open in VS Code
- Clone the repo and open the `construction-management-mcp` folder in VS Code.

## 2) Python environment
- Create a virtual environment and install dependencies:
  - Windows PowerShell:
    ```powershell
    python -m venv .venv; .venv\Scripts\Activate.ps1; pip install -r requirements.txt
    ```
  - Ubuntu/macOS Bash:
    ```bash
    python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
    ```
- VS Code should auto-detect the venv. If not, press Ctrl+Shift+P → "Python: Select Interpreter" → choose .venv.

## 3) Configure environment variables
- Copy `.env.template` to `.env` and fill in the required values:
  - Google OAuth client ID/secret (or service account file path)
  - Google Sheets project slots (`GOOGLE_SHEETS_PROJECT_*.{NAME,ID}`)
  - Optional SharePoint/OneDrive credentials (`SHAREPOINT_*`)
  - OpenAI API key and model settings
- Never commit `.env`. For production, prefer real environment variables over the file.

## 4) Optional dev-only local mode
- Leave `LOCAL_MODE` unset (or `false`) for production. To exercise the bundled CSV fixtures while offline:
  - Set `LOCAL_MODE=true` in `.env` or your shell.
  - Ensure the manifest points at the sample CSVs under `data/` (already configured by default).
  - Local mode disables SharePoint calls and forces Google Sheets requests to use the cached CSV manifests.

## 5) Run tests and server
- Tests:
  - Windows:
    ```powershell
    python test_mcp.py
    ```
  - Bash:
    ```bash
    python3 test_mcp.py
    ```
- Start MCP server:
  - Windows:
    ```powershell
    python src/main.py
    ```
  - Bash:
    ```bash
    python3 src/main.py
    ```

## 6) Copilot/Cursor MCP client setup
- The MCP config file is at `config/mcp_config.json` and uses relative paths, so it works anywhere.
- It runs `python src/main.py` from the repo root and sets `PYTHONPATH=src`.
- In VS Code, install the MCP-capable client (Cursor, or VS Code MCP extension when available) and point it to this config.

## 7) Fast path on Ubuntu
- One-liner bootstrap that does steps 1-4 for you:
  ```bash
  curl -fsSL https://raw.githubusercontent.com/egk10/BuildBridge-MCP/main/construction-management-mcp/scripts/bootstrap_ubuntu.sh | bash
  ```
  Optionally start the server automatically:
  ```bash
  START_SERVER=true curl -fsSL https://raw.githubusercontent.com/egk10/BuildBridge-MCP/main/construction-management-mcp/scripts/bootstrap_ubuntu.sh | bash
  ```

## Troubleshooting
- If Excel reads fail with zip errors, we automatically fallback to CSV in `data/sample`.
- Ensure `openpyxl` is installed (it is pinned in `requirements.txt`).
- If VS Code uses the wrong interpreter, re-select the `.venv` as described above.
- If the MCP client can’t find the server, verify you’re at the repo root when starting it and that `config/mcp_config.json` has `cwd` set to ".".
