"""
Dagster resources for the Medical Telegram Warehouse pipeline.

Resources provide shared configuration and connections for assets.
"""

import os
from pathlib import Path
from typing import Optional

from dagster import ConfigurableResource
from sqlalchemy import create_engine, Engine
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()


class DatabaseResource(ConfigurableResource):
    """
    Database connection resource for pipeline operations.

    Provides SQLAlchemy engine for database operations in assets.
    """

    host: str = "localhost"
    port: int = 5432
    database: str = "medical_warehouse"
    user: str = "warehouse_user"
    password: str = "changeme"

    def get_engine(self) -> Engine:
        """
        Create and return SQLAlchemy engine.

        Returns:
            SQLAlchemy engine instance
        """
        connection_string = (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )
        return create_engine(
            connection_string, pool_size=5, max_overflow=10, pool_pre_ping=True
        )

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            engine = self.get_engine()
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            return False


class FilePathResource(ConfigurableResource):
    """
    File path resource for managing project directories.

    Provides centralized path management for data files and outputs.
    """

    project_root: str

    @property
    def data_raw_dir(self) -> Path:
        """Raw data directory path."""
        return Path(self.project_root) / "data" / "raw"

    @property
    def data_processed_dir(self) -> Path:
        """Processed data directory path."""
        return Path(self.project_root) / "data" / "processed"

    @property
    def scripts_dir(self) -> Path:
        """Scripts directory path."""
        return Path(self.project_root) / "scripts"

    @property
    def dbt_dir(self) -> Path:
        """dbt project directory path."""
        return Path(self.project_root) / "medical_warehouse"

    @property
    def logs_dir(self) -> Path:
        """Logs directory path."""
        return Path(self.project_root) / "logs"

    def ensure_directories(self):
        """Create directories if they don't exist."""
        for dir_path in [self.data_raw_dir, self.data_processed_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


class TelegramConfigResource(ConfigurableResource):
    """
    Telegram API configuration resource.

    Manages Telegram API credentials and settings.
    """

    api_id: Optional[str] = None
    api_hash: Optional[str] = None
    phone: Optional[str] = None

    def get_credentials(self) -> dict:
        """
        Get Telegram API credentials.

        Returns:
            Dict with API credentials
        """
        return {
            "api_id": self.api_id or os.getenv("TELEGRAM_API_ID"),
            "api_hash": self.api_hash or os.getenv("TELEGRAM_API_HASH"),
            "phone": self.phone or os.getenv("TELEGRAM_PHONE"),
        }

    def validate_credentials(self) -> bool:
        """
        Validate that all required credentials are present.

        Returns:
            True if valid, False otherwise
        """
        creds = self.get_credentials()
        return all([creds["api_id"], creds["api_hash"], creds["phone"]])


# Default resource configurations
def get_default_resources():
    """
    Get default resource configurations.

    Returns:
        Dict of configured resources
    """
    project_root = Path(__file__).resolve().parent.parent.parent

    return {
        "database": DatabaseResource(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432)),
            database=os.getenv("POSTGRES_DB", "medical_warehouse"),
            user=os.getenv("POSTGRES_USER", "warehouse_user"),
            password=os.getenv("POSTGRES_PASSWORD", "changeme"),
        ),
        "file_paths": FilePathResource(project_root=str(project_root)),
        "telegram_config": TelegramConfigResource(
            api_id=os.getenv("TELEGRAM_API_ID"),
            api_hash=os.getenv("TELEGRAM_API_HASH"),
            phone=os.getenv("TELEGRAM_PHONE"),
        ),
    }
