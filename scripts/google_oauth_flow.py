#!/usr/bin/env python3
"""Interactive helper to generate Google OAuth tokens for BuildBridge-MCP."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on the import path when executed from repo root
REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from secure_config import SecureConfig  # type: ignore  # noqa: E402
from connectors.google_sheets_connector import GoogleSheetsConnector  # type: ignore  # noqa: E402


def main() -> None:
    cfg_manager = SecureConfig()
    config = cfg_manager.build_legacy_config()

    token_path = Path(config.get("google_token_file", "config/token.pickle"))
    config["local_mode"] = True  # prevent automatic Sheets API calls during flow

    connector = GoogleSheetsConnector(config)
    print("Starting interactive Google OAuth flow…")
    connector._perform_oauth_flow()

    print("\n✅ OAuth credentials saved to:", token_path.resolve())
    print("You can now rerun your tests or scripts with LOCAL_MODE=false.")


if __name__ == "__main__":
    main()
