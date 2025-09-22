#!/usr/bin/env bash
set -euo pipefail

# Bootstrap BuildBridge-MCP on Ubuntu Desktop
# - Creates a venv (.venv)
# - Installs deps
# - Copies credentials template and enables local_mode
# - Runs tests
# - Optionally starts the MCP server

REPO_URL=${REPO_URL:-"https://github.com/egk10/BuildBridge-MCP.git"}
BRANCH=${BRANCH:-"main"}
DIR=${DIR:-"BuildBridge-MCP"}
START_SERVER=${START_SERVER:-"false"}

if [[ ! -d "$DIR" ]]; then
  echo "Cloning repository..."
  git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$DIR"
fi

cd "$DIR"

# Ensure Python is present
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 is required. Install with: sudo apt update && sudo apt install -y python3 python3-venv python3-pip"
  exit 1
fi

# Create venv if missing
if [[ ! -d .venv ]]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Upgrade pip and install deps
python -m pip install --upgrade pip
pip install -r requirements.txt

# Prepare local credentials
if [[ ! -f config/credentials.json ]]; then
  cp config/credentials.json.template config/credentials.json
  # Enable local mode and set onedrive_folder to sample
  python - <<'PY'
import json
p = 'config/credentials.json'
with open(p) as f:
    data = json.load(f)
changed = False
if not data.get('local_mode'):
    data['local_mode'] = True; changed = True
if data.get('onedrive_folder') != 'data/sample':
    data['onedrive_folder'] = 'data/sample'; changed = True
if changed:
    with open(p,'w') as f:
        json.dump(data,f,indent=2)
print('credentials.json prepared (local_mode=true)')
PY
fi

# Run tests
python tests/test_mcp.py || true

# Optionally start the server
if [[ "$START_SERVER" == "true" ]]; then
  echo "Starting MCP server..."
  python src/main.py
fi

echo "Bootstrap complete. To start the server later:"
echo "  cd $DIR && source .venv/bin/activate && python src/main.py"
