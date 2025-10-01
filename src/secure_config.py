
#!/usr/bin/env python3
"""Secure configuration loader for BuildBridge-MCP.

This module provides the `SecureConfig` manager which favours environment variables
over local files and exposes helpers compatible with legacy configuration
consumers. All fallbacks to the deprecated ``credentials.json`` file have been
removed; operators must configure the application via environment variables or
explicitly referenced JSON manifests.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses representing structured configuration
# ---------------------------------------------------------------------------


@dataclass
class GoogleConfig:
    """Google OAuth / Sheets configuration envelope."""

    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    project_id: Optional[str] = None
    sheets_credentials_file: Optional[str] = None
    token_file: Optional[str] = None
    auth_method: str = "oauth"
    oauth_client_config: Optional[Dict[str, Any]] = None


@dataclass
class GoogleSheetsConfig:
    """Projects and tab metadata for Google Sheets."""

    projects: Dict[str, str] = field(default_factory=dict)
    sheets: Dict[str, Dict[str, str]] = field(default_factory=dict)
    default_summary_range: str = "Project Summary!A1:Z1000"


@dataclass
class OpenAIConfig:
    """OpenAI service configuration."""

    api_key: Optional[str] = None
    model: str = "gpt-4-turbo"
    max_tokens: int = 2000
    temperature: float = 0.1
    max_retries: int = 3


@dataclass
class AppConfig:
    """Application-level toggles."""

    local_mode: bool = False
    log_level: str = "INFO"
    debug: bool = False


@dataclass
class SharePointConfig:
    """Microsoft SharePoint / OneDrive configuration."""

    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    tenant_id: Optional[str] = None
    site: Optional[str] = None
    lists: Dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Secure configuration loader
# ---------------------------------------------------------------------------


class SecureConfig:
    """Centralised configuration manager with environment-first semantics."""

    def __init__(self, config_dir: Optional[Path] = None) -> None:
        project_root = Path(__file__).resolve().parent.parent
        self.config_dir = config_dir or (project_root / "config")
        self._project_root = project_root
        self._config: Optional[Dict[str, Any]] = None

        env_file = project_root / ".env"
        if env_file.exists():
            load_dotenv(env_file)
            logger.debug("Loaded environment variables from %s", env_file)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load_config(self) -> Dict[str, Any]:
        """Load configuration once and cache the structured dataclasses."""

        if self._config is None:
            self._config = {
                "google": self._load_google_config(),
                "google_sheets": self._load_google_sheets_config(),
                "sharepoint": self._load_sharepoint_config(),
                "openai": self._load_openai_config(),
                "app": self._load_app_config(),
            }
        return self._config

    def build_legacy_config(self) -> Dict[str, Any]:
        """Return a dictionary compatible with legacy connector expectations."""

        structured = self.load_config()
        legacy: Dict[str, Any] = {}

        google: GoogleConfig = structured["google"]
        if any([google.client_id, google.client_secret, google.oauth_client_config]):
            google_fields = {
                "google_client_id": google.client_id,
                "google_client_secret": google.client_secret,
                "google_project_id": google.project_id,
                "google_credentials_file": google.sheets_credentials_file,
                "google_token_file": google.token_file,
                "google_auth_method": google.auth_method,
            }
            legacy.update({k: v for k, v in google_fields.items() if v})
            if google.oauth_client_config:
                legacy["google_oauth_client_config"] = google.oauth_client_config

        sheets: GoogleSheetsConfig = structured["google_sheets"]
        if sheets.projects or sheets.sheets:
            payload = {"projects": sheets.projects}
            payload.update(sheets.sheets)
            legacy["google_sheets"] = payload
            if sheets.default_summary_range:
                legacy["google_sheets_defaults"] = {
                    "project_summary_range": sheets.default_summary_range
                }

        openai: OpenAIConfig = structured["openai"]
        if openai.api_key:
            legacy["ai_service"] = {
                "openai_api_key": openai.api_key,
                "model": openai.model,
                "max_tokens": openai.max_tokens,
                "temperature": openai.temperature,
                "max_retries": openai.max_retries,
            }

        app: AppConfig = structured["app"]
        legacy["local_mode"] = app.local_mode
        legacy["log_level"] = app.log_level

        sharepoint: SharePointConfig = structured["sharepoint"]
        if any([
            sharepoint.client_id,
            sharepoint.client_secret,
            sharepoint.tenant_id,
            sharepoint.site,
            sharepoint.lists,
        ]):
            sharepoint_fields = {
                "client_id": sharepoint.client_id,
                "client_secret": sharepoint.client_secret,
                "tenant_id": sharepoint.tenant_id,
                "sharepoint_site": sharepoint.site,
            }
            legacy.update({k: v for k, v in sharepoint_fields.items() if v})
            if sharepoint.lists:
                legacy["sharepoint_lists"] = sharepoint.lists

        return legacy

    def validate_config(self) -> list[str]:
        """Return human-readable configuration issues."""

        cfg = self.load_config()
        issues: list[str] = []

        google: GoogleConfig = cfg["google"]
        if not (google.client_id and google.client_secret) and not google.oauth_client_config:
            issues.append("Google OAuth credentials not fully configured")

        sheets: GoogleSheetsConfig = cfg["google_sheets"]
        if not sheets.projects:
            issues.append("No Google Sheets projects configured")

        openai: OpenAIConfig = cfg["openai"]
        if not openai.api_key:
            issues.append("OPENAI_API_KEY not configured")

        sharepoint: SharePointConfig = cfg["sharepoint"]
        required_sp = [
            sharepoint.client_id,
            sharepoint.client_secret,
            sharepoint.tenant_id,
            sharepoint.site,
        ]
        populated = [value for value in required_sp if value]
        if populated and len(populated) != len(required_sp):
            issues.append("SharePoint credentials partially configured")

        return issues

    def get_config_summary(self) -> str:
        """Produce a short, safe-to-share summary of the current config state."""

        cfg = self.load_config()
        lines: list[str] = ["🔐 Configuration Summary:"]

        google: GoogleConfig = cfg["google"]
        lines.append(
            f"Google OAuth: {'✅' if google.client_id or google.oauth_client_config else '❌'} Configured"
        )

        sheets: GoogleSheetsConfig = cfg["google_sheets"]
        lines.append(
            f"Google Sheets: {len(sheets.projects)} projects, {len(sheets.sheets)} tab configs"
        )

        sharepoint: SharePointConfig = cfg["sharepoint"]
        sharepoint_configured = all(
            [
                sharepoint.client_id,
                sharepoint.client_secret,
                sharepoint.tenant_id,
                sharepoint.site,
            ]
        )
        lines.append("SharePoint: " + ("✅ Configured" if sharepoint_configured else "ℹ️ Disabled"))

        openai: OpenAIConfig = cfg["openai"]
        lines.append(f"OpenAI API: {'✅' if openai.api_key else '❌'} Configured")

        app: AppConfig = cfg["app"]
        lines.append(f"Local Mode: {app.local_mode}")

        issues = self.validate_config()
        if issues:
            lines.append("\n⚠️  Configuration Issues:")
            lines.extend(f"  - {issue}" for issue in issues)

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _load_google_config(self) -> GoogleConfig:
        cfg = GoogleConfig()

        cfg.client_id = os.getenv("GOOGLE_CLIENT_ID")
        cfg.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        cfg.project_id = os.getenv("GOOGLE_PROJECT_ID")
        cfg.sheets_credentials_file = (
            os.getenv("GOOGLE_SHEETS_CREDENTIALS_FILE")
            or os.getenv("GOOGLE_CLIENT_SECRET_FILE")
        )
        cfg.token_file = os.getenv("GOOGLE_TOKEN_FILE")
        cfg.auth_method = os.getenv("GOOGLE_AUTH_METHOD", "oauth").lower()

        client_secret_path = self.config_dir / "client_secret.json"
        if not cfg.client_id and client_secret_path.exists():
            try:
                with client_secret_path.open("r", encoding="utf-8") as fp:
                    client_data = json.load(fp)
                installed = client_data.get("installed")
                if isinstance(installed, dict):
                    cfg.client_id = installed.get("client_id")
                    cfg.client_secret = installed.get("client_secret")
                    cfg.project_id = installed.get("project_id")
                    logger.warning(
                        "Using local client_secret.json – prefer environment variables for production"
                    )
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.error("Failed to load client_secret.json: %s", exc)

        if not cfg.sheets_credentials_file and client_secret_path.exists():
            cfg.sheets_credentials_file = str(client_secret_path)

        if not cfg.token_file:
            cfg.token_file = str(self.config_dir / "token.pickle")

        cfg.oauth_client_config = self._build_oauth_client_config(cfg)
        return cfg

    def _build_oauth_client_config(self, google_config: GoogleConfig) -> Optional[Dict[str, Any]]:
        if not google_config.client_id or not google_config.client_secret:
            return None

        auth_uri = os.getenv("GOOGLE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth")
        token_uri = os.getenv("GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")
        cert_url = os.getenv(
            "GOOGLE_AUTH_PROVIDER_CERT_URL", "https://www.googleapis.com/oauth2/v1/certs"
        )
        redirect_uris_env = os.getenv(
            "GOOGLE_OAUTH_REDIRECT_URIS", "http://localhost,http://localhost:8080/"
        )
        redirect_uris = [uri.strip() for uri in redirect_uris_env.split(",") if uri.strip()]
        if not redirect_uris:
            redirect_uris = ["http://localhost"]

        return {
            "installed": {
                "client_id": google_config.client_id,
                "project_id": google_config.project_id or "",
                "auth_uri": auth_uri,
                "token_uri": token_uri,
                "auth_provider_x509_cert_url": cert_url,
                "client_secret": google_config.client_secret,
                "redirect_uris": redirect_uris,
            }
        }

    def _load_google_sheets_config(self) -> GoogleSheetsConfig:
        projects: Dict[str, str] = {}
        sheets: Dict[str, Dict[str, str]] = {}
        default_summary_range = os.getenv(
            "GOOGLE_SHEETS_DEFAULT_SUMMARY_RANGE", "Project Summary!A1:Z1000"
        )

        legacy_keys = {
            "72_perth": "GOOGLE_SHEETS_PROJECT_72_PERTH",
            "17175_yonge_st": "GOOGLE_SHEETS_PROJECT_17175_YONGE_ST",
            "azure_road": "GOOGLE_SHEETS_PROJECT_AZURE_ROAD",
        }
        for project_key, env_key in legacy_keys.items():
            sheet_id = os.getenv(env_key)
            if sheet_id:
                projects[project_key] = sheet_id

        slot_prefix = "GOOGLE_SHEETS_PROJECT_"
        for env_key, value in os.environ.items():
            if not env_key.startswith(slot_prefix) or not env_key.endswith("_ID"):
                continue
            if not value:
                continue
            slot = env_key[len(slot_prefix) : -len("_ID")]
            name_key = f"{slot_prefix}{slot}_NAME"
            project_key = os.getenv(name_key)
            if not project_key:
                project_key = re.sub(r"[^0-9a-z]+", "", slot.lower()) or f"project_{slot.lower()}"
            projects[project_key] = value

        def merge_sheet_configs(source: Dict[str, Any]) -> None:
            for key, value in source.items():
                if key == "projects" or key.startswith("//"):
                    continue
                if isinstance(value, dict) and {"sheet_id", "range"} <= value.keys():
                    sheets[key] = value

        config_file_env = os.getenv("GOOGLE_SHEETS_CONFIG_FILE")
        if config_file_env:
            candidate = Path(config_file_env)
            if not candidate.is_absolute():
                candidate = (self._project_root / config_file_env).resolve()
            if candidate.exists():
                try:
                    with candidate.open("r", encoding="utf-8") as fp:
                        payload = json.load(fp)
                    merge_sheet_configs(payload.get("google_sheets", payload))
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.error("Failed to load Google Sheets config file %s: %s", candidate, exc)
            else:
                logger.warning("GOOGLE_SHEETS_CONFIG_FILE not found: %s", candidate)

        inline_json = os.getenv("GOOGLE_SHEETS_CONFIG_JSON")
        if inline_json:
            try:
                inline_payload = json.loads(inline_json)
                merge_sheet_configs(inline_payload.get("google_sheets", inline_payload))
            except json.JSONDecodeError as exc:
                logger.error("Invalid JSON in GOOGLE_SHEETS_CONFIG_JSON: %s", exc)

        override_prefix = "GOOGLE_SHEETS_CONFIG_"
        for env_key, value in os.environ.items():
            if not env_key.startswith(override_prefix) or not env_key.endswith("_SHEET_ID"):
                continue
            base = env_key[len(override_prefix) : -len("_SHEET_ID")]
            range_env = os.getenv(f"{override_prefix}{base}_RANGE")
            if not range_env:
                continue
            sheet_key = base.lower().replace("__", ".").replace("-", "_")
            sheets[sheet_key] = {"sheet_id": value, "range": range_env}

        for project_key, sheet_id in projects.items():
            clean_key = re.sub(r"[^0-9a-z]+", "", project_key.lower())
            summary_key = f"{clean_key}_project_summary"
            if summary_key in sheets:
                continue
            env_prefix = f"GOOGLE_SHEETS_{project_key.upper().replace('-', '_')}"
            summary_sheet_id = os.getenv(
                f"{env_prefix}_PROJECT_SUMMARY_SHEET_ID", f"projects.{project_key}"
            )
            summary_range = os.getenv(
                f"{env_prefix}_PROJECT_SUMMARY_RANGE", default_summary_range
            )
            sheets[summary_key] = {"sheet_id": summary_sheet_id, "range": summary_range}

        return GoogleSheetsConfig(
            projects=projects,
            sheets=sheets,
            default_summary_range=default_summary_range,
        )

    def _load_sharepoint_config(self) -> SharePointConfig:
        cfg = SharePointConfig()

        cfg.client_id = os.getenv("SHAREPOINT_CLIENT_ID") or os.getenv("AZURE_APP_CLIENT_ID")
        cfg.client_secret = os.getenv("SHAREPOINT_CLIENT_SECRET") or os.getenv(
            "AZURE_APP_CLIENT_SECRET"
        )
        cfg.tenant_id = os.getenv("SHAREPOINT_TENANT_ID") or os.getenv("AZURE_APP_TENANT_ID")
        cfg.site = os.getenv("SHAREPOINT_SITE") or os.getenv("SHAREPOINT_URL")

        lists_json = os.getenv("SHAREPOINT_LISTS_JSON")
        if lists_json:
            try:
                parsed = json.loads(lists_json)
                if isinstance(parsed, dict):
                    cfg.lists = {k: str(v) for k, v in parsed.items()}
                else:
                    logger.error("SHAREPOINT_LISTS_JSON must decode to an object")
            except json.JSONDecodeError as exc:
                logger.error("Invalid JSON in SHAREPOINT_LISTS_JSON: %s", exc)

        return cfg

    def _load_openai_config(self) -> OpenAIConfig:
        cfg = OpenAIConfig()
        cfg.api_key = os.getenv("OPENAI_API_KEY")
        cfg.model = os.getenv("OPENAI_MODEL", cfg.model)
        cfg.max_tokens = int(os.getenv("OPENAI_MAX_TOKENS", cfg.max_tokens))
        cfg.temperature = float(os.getenv("OPENAI_TEMPERATURE", cfg.temperature))
        cfg.max_retries = int(os.getenv("OPENAI_MAX_RETRIES", cfg.max_retries))
        if not cfg.api_key:
            logger.warning("OPENAI_API_KEY not set in environment variables")
        return cfg

    def _load_app_config(self) -> AppConfig:
        cfg = AppConfig()
        local_mode_raw = os.getenv("LOCAL_MODE")
        if local_mode_raw is not None:
            cfg.local_mode = local_mode_raw.lower() == "true"
        cfg.log_level = os.getenv("LOG_LEVEL", cfg.log_level)
        cfg.debug = os.getenv("DEBUG", "false").lower() == "true"
        return cfg


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

_config_manager: Optional[SecureConfig] = None


def get_config_manager() -> SecureConfig:
    global _config_manager
    if _config_manager is None:
        _config_manager = SecureConfig()
    return _config_manager


def load_secure_config() -> Dict[str, Any]:
    """Return the structured configuration (dataclasses)."""

    return get_config_manager().load_config()


def load_legacy_config() -> Dict[str, Any]:
    """Return the dictionary configuration expected by legacy callers."""

    return get_config_manager().build_legacy_config()


# Backwards-compatible alias used by older scripts
def load_config():  # pragma: no cover - compatibility shim
    logger.warning("load_config() is deprecated; use load_secure_config() or load_legacy_config()")
    return load_secure_config()
