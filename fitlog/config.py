"""
Configuration management for fitlog.

Handles environment variables, configuration files, and settings
for both local and cloud modes.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for fitlog CLI and cloud integration."""

    def __init__(self):
        # Cloud API configuration
        self.api_url = os.getenv(
            "FITLOG_API_URL",
            "https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev",
        )
        self.api_key = os.getenv("FITLOG_API_KEY")

        # Mode selection (local vs cloud)
        self.use_cloud = os.getenv("FITLOG_USE_CLOUD", "false").lower() == "true"

        # Local database configuration
        self.local_db_path = os.getenv("FITLOG_DB_PATH", "data/fitlog.db")

        # Debug settings
        self.debug = os.getenv("FITLOG_DEBUG", "false").lower() == "true"

        # API request timeout
        self.request_timeout = int(os.getenv("FITLOG_REQUEST_TIMEOUT", "30"))

    @property
    def is_cloud_configured(self) -> bool:
        """Check if cloud API is properly configured."""
        return bool(self.api_key and self.api_url)

    def require_cloud_config(self) -> None:
        """Raise error if cloud configuration is missing."""
        if not self.api_key:
            raise ValueError(
                "FITLOG_API_KEY environment variable is required for cloud mode.\n"
                "Set it to your API key: fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw\n"
                "Example: export FITLOG_API_KEY='fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw'"
            )

        if not self.api_url:
            raise ValueError(
                "FITLOG_API_URL environment variable is required for cloud mode."
            )

    def get_env_example(self) -> str:
        """Return example .env file content."""
        return """# Fitlog Configuration

# Cloud API Settings
FITLOG_API_KEY=fitlog_z-e8yE_lWLIZAkRcKy6AVW5ZaJJ3qmaGS5eFVZjtnHw
FITLOG_API_URL=https://2054k0hh9j.execute-api.us-east-1.amazonaws.com/dev

# Mode Selection
FITLOG_USE_CLOUD=true

# Local Database (if not using cloud)
FITLOG_DB_PATH=data/fitlog.db

# Debug Mode
FITLOG_DEBUG=false

# API Timeout (seconds)
FITLOG_REQUEST_TIMEOUT=30
"""

    def create_env_file(self, path: str | None = None) -> Path:
        """Create example .env file."""
        if path is None:
            path = ".env.example"

        env_path = Path(path)
        env_path.write_text(self.get_env_example())
        return env_path


# Global configuration instance
config = Config()


def get_database_client():
    """
    Factory function to get the appropriate database client.

    Returns either CloudClient or Database based on configuration.
    """
    if config.use_cloud:
        # Use cloud client
        config.require_cloud_config()
        from .cloud import CloudClient

        return CloudClient(debug=config.debug)
    else:
        # Use local database
        from .db import Database

        return Database(db_path=config.local_db_path, debug=config.debug)


def setup_cloud_mode():
    """
    Helper function to set up cloud mode.

    Sets environment variable and validates configuration.
    """
    os.environ["FITLOG_USE_CLOUD"] = "true"

    # Reload config to pick up changes
    global config
    config = Config()

    try:
        config.require_cloud_config()
        print("✅ Cloud mode enabled and configured successfully")
        return True
    except ValueError as e:
        print(f"❌ Cloud configuration error: {e}")
        return False


def setup_local_mode():
    """Helper function to set up local mode."""
    os.environ["FITLOG_USE_CLOUD"] = "false"

    # Reload config to pick up changes
    global config
    config = Config()

    print("✅ Local mode enabled")
    return True


def show_config():
    """Display current configuration."""
    print("🔧 Current Fitlog Configuration:")
    print(f"  Mode: {'Cloud' if config.use_cloud else 'Local'}")

    if config.use_cloud:
        print(f"  API URL: {config.api_url}")
        print(f"  API Key: {'✅ Set' if config.api_key else '❌ Missing'}")
        print(f"  Configured: {'✅ Yes' if config.is_cloud_configured else '❌ No'}")
    else:
        print(f"  Database: {config.local_db_path}")

    print(f"  Debug: {config.debug}")
    print(f"  Request Timeout: {config.request_timeout}s")
