# Setup Instructions for Construction Management MCP

## Prerequisites

1. **Python 3.10+** installed
2. **Microsoft 365 account** (for SharePoint/OneDrive connectivity)
3. **Google Cloud project** with OAuth credentials for Sheets access
4. **VS Code or Cursor** as an MCP client
5. **Git** for version control

## Step 1: Python environment

1. Clone the repository and open the project root in VS Code.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   # macOS/Linux
   source .venv/bin/activate
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

VS Code should detect `.venv` automatically. If it does not, press `Ctrl+Shift+P` → "Python: Select Interpreter" → choose `.venv`.

## Step 2: Configure secrets via `.env`

All connectors now load credentials from environment variables. Copy the template and fill in the placeholders:

```bash
cp .env.template .env
```

Minimum values to provide:
- **Google OAuth:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_PROJECT_ID`
- **Google Sheets projects:** populate the numbered slots (`GOOGLE_SHEETS_PROJECT_1_NAME`, `GOOGLE_SHEETS_PROJECT_1_ID`, etc.)
- **OpenAI access:** `OPENAI_API_KEY` (and optionally model overrides)

Optional values:
- **SharePoint / OneDrive:** `SHAREPOINT_CLIENT_ID`, `SHAREPOINT_CLIENT_SECRET`, `SHAREPOINT_TENANT_ID`, `SHAREPOINT_SITE`
- **Custom SharePoint list names:** `SHAREPOINT_LISTS_JSON={"projects":"Projects","tasks":"Tasks"}`

> ⚠️  Never commit `.env` to Git. In production, set these values via your deployment platform's secret manager or environment configuration.

## Step 3: Register Microsoft Graph application (optional but recommended)

If you plan to fetch data from SharePoint or OneDrive:
1. Visit the [Azure Portal](https://portal.azure.com/).
2. Register a new application and record the **Application (client) ID**.
3. Add Microsoft Graph permissions: `Files.Read.All`, `Sites.Read.All`, `Sites.ReadWrite.All` (if you need write access).
4. Generate a client secret and set `SHAREPOINT_CLIENT_SECRET`.

## Step 4: Optional dev-only local mode

When `LOCAL_MODE` is `true`, the connectors avoid live API calls and instead use the bundled CSV manifest under `data/`. Enable this only when you explicitly want to operate offline:

```bash
export LOCAL_MODE=true  # or set it inside .env
```

In this mode:
- Google Sheets ranges are read from `config/project_manifest.json` and the CSV files referenced there.
- SharePoint connectors become no-ops returning empty lists.
- Excel/OneDrive paths fall back to local sample data.

## Step 5: Sample data and manifest refresh

- The repository ships with representative CSV extracts in `data/` that align with the manifest.
- After adjusting the manifest or adding new projects, refresh the normalized cache:
  ```bash
  scripts/refresh_manifest_local.py --force
  ```
- Use `scripts/simulate_user_input1.py` to preview the response built from cached metrics.

## Step 6: MCP client configuration

The MCP config lives at `config/mcp_config.json` and already points to `python src/main.py` with `PYTHONPATH=src`. Load that file in Cursor or the VS Code MCP extension to connect.

## Step 7: Smoke tests

1. Run the automated test suite:
   ```bash
   pytest -k "not load_test"
   ```
2. Launch the MCP server:
   ```bash
   python src/main.py
   ```
3. Interact via your MCP client or the static web chat under `deploy/static/`.

## Troubleshooting

- **Authentication failures:** Confirm OAuth credentials and SharePoint permissions are present in `.env`.
- **Sheets manifest errors:** Run `validate_sheets_config.py` to catch missing ranges or IDs.
- **Server startup issues:** Ensure the virtual environment is active and dependencies installed.
- **Local mode confusion:** Double-check `LOCAL_MODE`—the connectors now fail fast if credentials are missing while local mode is disabled.

## Security notes

- Keep secrets out of version control (use `.gitignore` and secret managers).
- Rotate API keys and client secrets regularly.
- Restrict OAuth redirect URIs to trusted origins.
- For production deployments, favour managed identity or secret vaults over flat files.