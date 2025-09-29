#!/usr/bin/env python3
"""
Centralized Secure Configuration Manager for BuildBridge-MCP

This module provides a single, secure source of truth for all configuration,
prioritizing environment variables over local files for security.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class GoogleConfig:
    """Google API Configuration"""
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    project_id: Optional[str] = None
    sheets_credentials_file: Optional[str] = None
    token_file: Optional[str] = None

@dataclass
class GoogleSheetsConfig:
    """Google Sheets Project Configuration"""
    projects: Dict[str, str]  # project_name -> sheet_id

@dataclass
class OpenAIConfig:
    """OpenAI API Configuration"""
    api_key: Optional[str] = None
    model: str = "gpt-4-turbo"
    max_tokens: int = 2000
    temperature: float = 0.1
    max_retries: int = 3

@dataclass
class AppConfig:
    """Application Configuration"""
    local_mode: bool = True
    log_level: str = "INFO"
    debug: bool = False

class SecureConfig:
    """Centralized configuration manager with security-first approach"""

    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self._config = None

    def load_config(self) -> Dict[str, Any]:
        """Load configuration with environment variable priority"""
        if self._config is not None:
            return self._config

        config = {
            'google': self._load_google_config(),
            'google_sheets': self._load_google_sheets_config(),
            'openai': self._load_openai_config(),
            'app': self._load_app_config(),
        }

        self._config = config
        return config

    def _load_google_config(self) -> GoogleConfig:
        """Load Google API configuration from environment or files"""
        # Priority: Environment > Local files
        config = GoogleConfig()

        # Try environment variables first (most secure)
        config.client_id = os.getenv('GOOGLE_CLIENT_ID')
        config.client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        config.project_id = os.getenv('GOOGLE_PROJECT_ID')
        config.sheets_credentials_file = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE')
        config.token_file = os.getenv('GOOGLE_TOKEN_FILE')

        # Fallback to local files if environment not set
        if not config.client_id and (self.config_dir / "client_secret.json").exists():
            try:
                with open(self.config_dir / "client_secret.json", 'r') as f:
                    client_data = json.load(f)
                    if 'installed' in client_data:
                        config.client_id = client_data['installed'].get('client_id')
                        config.client_secret = client_data['installed'].get('client_secret')
                        config.project_id = client_data['installed'].get('project_id')
                        logger.warning("Using local client_secret.json - consider using environment variables")
            except Exception as e:
                logger.error(f"Failed to load client_secret.json: {e}")

        # Set defaults for file paths
        if not config.sheets_credentials_file:
            config.sheets_credentials_file = str(self.config_dir / "credentials.json")
        if not config.token_file:
            config.token_file = str(self.config_dir / "token.pickle")

        return config

    def _load_google_sheets_config(self) -> GoogleSheetsConfig:
        """Load Google Sheets project configuration"""
        projects = {}

        # Try environment variables first
        env_projects = {
            '72_perth': os.getenv('GOOGLE_SHEETS_PROJECT_72_PERTH'),
            '17175_yonge_st': os.getenv('GOOGLE_SHEETS_PROJECT_17175_YONGE_ST'),
            'azure_road': os.getenv('GOOGLE_SHEETS_PROJECT_AZURE_ROAD'),
        }

        # Filter out None values
        projects.update({k: v for k, v in env_projects.items() if v})

        # Fallback to local config file
        if not projects and (self.config_dir / "credentials.json").exists():
            try:
                with open(self.config_dir / "credentials.json", 'r') as f:
                    local_config = json.load(f)
                    if 'google_sheets' in local_config and 'projects' in local_config['google_sheets']:
                        projects.update(local_config['google_sheets']['projects'])
                        logger.warning("Using local credentials.json for sheets - consider using environment variables")
            except Exception as e:
                logger.error(f"Failed to load sheets config: {e}")

        return GoogleSheetsConfig(projects=projects)

    def _load_openai_config(self) -> OpenAIConfig:
        """Load OpenAI configuration from environment"""
        config = OpenAIConfig()

        # Environment variables only (no fallback files for API keys)
        config.api_key = os.getenv('OPENAI_API_KEY')
        config.model = os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
        config.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))
        config.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.1'))
        config.max_retries = int(os.getenv('OPENAI_MAX_RETRIES', '3'))

        if not config.api_key:
            logger.warning("OPENAI_API_KEY not set in environment variables")

        return config

    def _load_app_config(self) -> AppConfig:
        """Load application configuration"""
        config = AppConfig()

        config.local_mode = os.getenv('LOCAL_MODE', 'true').lower() == 'true'
        config.log_level = os.getenv('LOG_LEVEL', 'INFO')
        config.debug = os.getenv('DEBUG', 'false').lower() == 'true'

        return config

    def validate_config(self) -> list[str]:
        """Validate configuration and return list of issues"""
        issues = []
        config = self.load_config()

        # Check Google config
        google = config['google']
        if not google.client_id:
            issues.append("GOOGLE_CLIENT_ID not configured")
        if not google.client_secret:
            issues.append("GOOGLE_CLIENT_SECRET not configured")

        # Check Google Sheets
        sheets = config['google_sheets']
        if not sheets.projects:
            issues.append("No Google Sheets projects configured")

        # Check OpenAI
        openai = config['openai']
        if not openai.api_key:
            issues.append("OPENAI_API_KEY not configured")

        return issues

    def get_config_summary(self) -> str:
        """Get a summary of current configuration (without sensitive data)"""
        config = self.load_config()
        summary = []

        summary.append("🔐 Configuration Summary:")
        summary.append(f"Google OAuth: {'✅' if config['google'].client_id else '❌'} Configured")
        summary.append(f"Google Sheets: {len(config['google_sheets'].projects)} projects")
        summary.append(f"OpenAI API: {'✅' if config['openai'].api_key else '❌'} Configured")
        summary.append(f"Local Mode: {config['app'].local_mode}")

        issues = self.validate_config()
        if issues:
            summary.append("\n⚠️  Configuration Issues:")
            for issue in issues:
                summary.append(f"  - {issue}")

        return "\n".join(summary)

# Global instance for easy access
_config_manager = None

def get_config_manager() -> SecureConfig:
    """Get the global configuration manager instance"""
    global _config_manager
    if _config_manager is None:
        _config_manager = SecureConfig()
    return _config_manager

def load_secure_config() -> Dict[str, Any]:
    """Convenience function to load secure configuration"""
    return get_config_manager().load_config()

# Backwards compatibility
def load_config():
    """Legacy function for backwards compatibility"""
    logger.warning("Using deprecated load_config(), consider using load_secure_config()")
    return load_secure_config()