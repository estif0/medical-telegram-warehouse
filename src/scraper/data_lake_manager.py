"""
Data Lake Manager for organizing raw data storage.

This module handles the file system structure for the data lake,
ensuring data is properly partitioned and organized.

Example:
    >>> from src.scraper.data_lake_manager import DataLakeManager
    >>> dlm = DataLakeManager(base_path="data")
    >>> path = dlm.save_message_json(messages, "CheMed123", "2026-01-18")
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger


class DataLakeManager:
    """
    Manages data lake structure and file operations.

    Data lake structure:
        data/
        ├── raw/
        │   ├── telegram_messages/
        │   │   └── YYYY-MM-DD/
        │   │       ├── channel_name.json
        │   │       └── _manifest.json
        │   └── images/
        │       └── channel_name/
        │           └── message_id.jpg
        └── processed/

    Attributes:
        base_path: Root path for data lake
        logger: Logger instance

    Example:
        >>> dlm = DataLakeManager()
        >>> messages = [{"id": 1, "text": "Hello"}]
        >>> dlm.save_message_json(messages, "channel_name", "2026-01-18")
    """

    def __init__(self, base_path: str = "data"):
        """
        Initialize DataLakeManager.

        Args:
            base_path: Root directory for data lake (default: "data")
        """
        self.base_path = Path(base_path)
        self.logger = get_logger(__name__)
        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """Create necessary data lake directories."""
        dirs = [
            self.base_path / "raw" / "telegram_messages",
            self.base_path / "raw" / "images",
            self.base_path / "processed",
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f"Data lake structure ensured at {self.base_path}")

    def get_messages_partition_dir(self, date_str: str) -> Path:
        """
        Get directory path for a specific date partition.

        Args:
            date_str: Date string in YYYY-MM-DD format

        Returns:
            Path to partition directory
        """
        partition_dir = self.base_path / "raw" / "telegram_messages" / date_str
        partition_dir.mkdir(parents=True, exist_ok=True)
        return partition_dir

    def get_images_dir(self, channel_name: str) -> Path:
        """
        Get directory path for channel images.

        Args:
            channel_name: Name of Telegram channel

        Returns:
            Path to images directory
        """
        images_dir = self.base_path / "raw" / "images" / channel_name
        images_dir.mkdir(parents=True, exist_ok=True)
        return images_dir

    def save_message_json(
        self,
        messages: List[Dict[str, Any]],
        channel_name: str,
        date_str: Optional[str] = None,
    ) -> Path:
        """
        Save messages as JSON file in partitioned structure.

        Args:
            messages: List of message dictionaries
            channel_name: Name of Telegram channel
            date_str: Date string (default: today in YYYY-MM-DD)

        Returns:
            Path to saved JSON file

        Raises:
            ValueError: If messages is empty or invalid
            IOError: If file write fails

        Example:
            >>> messages = [{"id": 1, "text": "Hello", "date": "2026-01-18"}]
            >>> path = dlm.save_message_json(messages, "CheMed123")
        """
        if not messages:
            raise ValueError("Messages list cannot be empty")

        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")

        partition_dir = self.get_messages_partition_dir(date_str)
        file_path = partition_dir / f"{channel_name}.json"

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)

            self.logger.info(
                f"Saved {len(messages)} messages to {file_path.relative_to(self.base_path)}"
            )
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to save messages: {e}")
            raise IOError(f"Failed to write to {file_path}: {e}")

    def save_image(
        self,
        image_data: bytes,
        channel_name: str,
        message_id: int,
        extension: str = "jpg",
    ) -> Path:
        """
        Save image file to organized directory structure.

        Args:
            image_data: Raw image bytes
            channel_name: Name of Telegram channel
            message_id: Message ID associated with image
            extension: File extension (default: "jpg")

        Returns:
            Path to saved image file

        Raises:
            IOError: If file write fails

        Example:
            >>> with open("image.jpg", "rb") as f:
            ...     data = f.read()
            >>> path = dlm.save_image(data, "CheMed123", 12345)
        """
        images_dir = self.get_images_dir(channel_name)
        file_path = images_dir / f"{message_id}.{extension}"

        try:
            with open(file_path, "wb") as f:
                f.write(image_data)

            self.logger.debug(f"Saved image: {file_path.relative_to(self.base_path)}")
            return file_path

        except Exception as e:
            self.logger.error(f"Failed to save image {message_id}: {e}")
            raise IOError(f"Failed to write image to {file_path}: {e}")

    def write_manifest(
        self,
        date_str: str,
        channel_stats: Dict[str, int],
        extra: Optional[Dict[str, Any]] = None,
    ) -> Path:
        """
        Write manifest file with scraping metadata.

        Args:
            date_str: Date string in YYYY-MM-DD format
            channel_stats: Dictionary of channel_name -> message_count
            extra: Optional additional metadata

        Returns:
            Path to manifest file

        Example:
            >>> stats = {"CheMed123": 150, "lobelia4cosmetics": 75}
            >>> dlm.write_manifest("2026-01-18", stats)
        """
        partition_dir = self.get_messages_partition_dir(date_str)
        manifest_path = partition_dir / "_manifest.json"

        manifest = {
            "date": date_str,
            "timestamp": datetime.now().isoformat(),
            "channels": channel_stats,
            "total_messages": sum(channel_stats.values()),
        }

        if extra:
            manifest.update(extra)

        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)

        self.logger.info(f"Wrote manifest: {manifest_path.relative_to(self.base_path)}")
        return manifest_path

    def get_scraped_dates(self) -> List[str]:
        """
        Get list of dates that have been scraped.

        Returns:
            List of date strings in YYYY-MM-DD format
        """
        messages_dir = self.base_path / "raw" / "telegram_messages"
        if not messages_dir.exists():
            return []

        dates = [
            d.name
            for d in messages_dir.iterdir()
            if d.is_dir() and not d.name.startswith("_")
        ]
        return sorted(dates)

    def validate_structure(self) -> bool:
        """
        Validate data lake directory structure.

        Returns:
            True if structure is valid

        Raises:
            FileNotFoundError: If required directories are missing
        """
        required_dirs = [
            self.base_path / "raw" / "telegram_messages",
            self.base_path / "raw" / "images",
        ]

        for dir_path in required_dirs:
            if not dir_path.exists():
                raise FileNotFoundError(f"Required directory missing: {dir_path}")

        self.logger.info("Data lake structure validated successfully")
        return True
