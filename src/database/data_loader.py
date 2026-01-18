"""
Data loader module for loading JSON data from data lake to PostgreSQL.

This module handles loading scraped Telegram data from the data lake
into the PostgreSQL raw schema.

Example:
    >>> from src.database.data_loader import DataLoader
    >>> loader = DataLoader()
    >>> loader.create_raw_table()
    >>> loader.load_json_to_postgres("data/raw/telegram_messages/2026-01-18")
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from psycopg2 import sql, Error
from src.database.db_connector import DatabaseConnector


class DataLoader:
    """
    Data loader for loading JSON data from data lake to PostgreSQL.

    This class handles creating raw tables and loading JSON data from
    the data lake into PostgreSQL with duplicate checking.

    Attributes:
        db_connector: DatabaseConnector instance
        logger: Logger instance

    Example:
        >>> loader = DataLoader()
        >>> loader.create_raw_table()
        >>> count = loader.load_json_to_postgres("data/raw/telegram_messages/2026-01-18")
        >>> print(f"Loaded {count} messages")
    """

    def __init__(self, db_connector: Optional[DatabaseConnector] = None):
        """
        Initialize DataLoader with database connector.

        Args:
            db_connector: DatabaseConnector instance (creates new one if None)
        """
        self.db_connector = db_connector or DatabaseConnector()
        self.logger = logging.getLogger(__name__)

        # Ensure database connection is established
        if not self.db_connector.connection_pool:
            self.db_connector.connect()

    def create_raw_table(self) -> None:
        """
        Create raw.telegram_messages table if it doesn't exist.

        The table stores all scraped Telegram messages with metadata.

        Raises:
            psycopg2.Error: If table creation fails
        """
        create_table_query = """
            CREATE TABLE IF NOT EXISTS raw.telegram_messages (
                message_id BIGINT PRIMARY KEY,
                channel_name VARCHAR(255) NOT NULL,
                channel_id BIGINT,
                message_date TIMESTAMP NOT NULL,
                message_text TEXT,
                has_media BOOLEAN DEFAULT FALSE,
                media_type VARCHAR(50),
                image_path TEXT,
                views INTEGER DEFAULT 0,
                forwards INTEGER DEFAULT 0,
                replies INTEGER DEFAULT 0,
                edit_date TIMESTAMP,
                post_author VARCHAR(255),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_channel_name ON raw.telegram_messages(channel_name);
            CREATE INDEX IF NOT EXISTS idx_message_date ON raw.telegram_messages(message_date);
            CREATE INDEX IF NOT EXISTS idx_scraped_at ON raw.telegram_messages(scraped_at);
        """

        try:
            self.db_connector.execute_query(create_table_query, fetch=False)
            self.logger.info("Table raw.telegram_messages created or already exists")
        except Error as e:
            self.logger.error(f"Failed to create raw table: {e}")
            raise

    def check_duplicates(self, message_ids: List[int]) -> List[int]:
        """
        Check which message IDs already exist in the database.

        Args:
            message_ids: List of message IDs to check

        Returns:
            List of message IDs that already exist in database
        """
        if not message_ids:
            return []

        query = """
            SELECT message_id 
            FROM raw.telegram_messages 
            WHERE message_id = ANY(%s)
        """

        try:
            results = self.db_connector.execute_query(query, params=(message_ids,))
            existing_ids = [row["message_id"] for row in results] if results else []
            return existing_ids
        except Error as e:
            self.logger.error(f"Error checking duplicates: {e}")
            return []

    def _validate_message_data(self, message: Dict[str, Any]) -> bool:
        """
        Validate message data before insertion.

        Args:
            message: Message dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["message_id", "channel_name", "message_date"]

        for field in required_fields:
            if field not in message or message[field] is None:
                self.logger.warning(f"Message missing required field: {field}")
                return False

        # Validate message_id is a number
        try:
            int(message["message_id"])
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid message_id: {message.get('message_id')}")
            return False

        return True

    def bulk_insert(self, messages: List[Dict[str, Any]]) -> int:
        """
        Bulk insert messages into raw.telegram_messages table.

        Args:
            messages: List of message dictionaries

        Returns:
            Number of messages inserted

        Raises:
            psycopg2.Error: If insertion fails
        """
        if not messages:
            self.logger.warning("No messages to insert")
            return 0

        # Filter valid messages
        valid_messages = [msg for msg in messages if self._validate_message_data(msg)]

        if not valid_messages:
            self.logger.warning("No valid messages to insert after validation")
            return 0

        # Check for duplicates
        message_ids = [msg["message_id"] for msg in valid_messages]
        existing_ids = self.check_duplicates(message_ids)

        # Filter out duplicates
        new_messages = [
            msg for msg in valid_messages if msg["message_id"] not in existing_ids
        ]

        if not new_messages:
            self.logger.info("All messages already exist in database")
            return 0

        # Prepare insert query
        insert_query = """
            INSERT INTO raw.telegram_messages (
                message_id, channel_name, channel_id, message_date, message_text,
                has_media, media_type, image_path, views, forwards, replies,
                edit_date, post_author, scraped_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (message_id) DO NOTHING
        """

        # Prepare data tuples
        data = []
        for msg in new_messages:
            data.append(
                (
                    msg.get("message_id"),
                    msg.get("channel_name"),
                    msg.get("channel_id"),
                    msg.get("message_date"),
                    msg.get("message_text"),
                    msg.get("has_media", False),
                    msg.get("media_type"),
                    msg.get("image_path"),
                    msg.get("views", 0),
                    msg.get("forwards", 0),
                    msg.get("replies", 0),
                    msg.get("edit_date"),
                    msg.get("post_author"),
                    msg.get("scraped_at", datetime.now()),
                )
            )

        try:
            self.db_connector.execute_many(insert_query, data)
            self.logger.info(f"Successfully inserted {len(new_messages)} messages")

            if existing_ids:
                self.logger.info(f"Skipped {len(existing_ids)} duplicate messages")

            return len(new_messages)

        except Error as e:
            self.logger.error(f"Failed to bulk insert messages: {e}")
            raise

    def load_json_to_postgres(self, json_path: str, batch_size: int = 1000) -> int:
        """
        Load JSON files from data lake to PostgreSQL.

        Args:
            json_path: Path to JSON file or directory containing JSON files
            batch_size: Number of records to insert per batch

        Returns:
            Total number of messages loaded

        Raises:
            FileNotFoundError: If json_path doesn't exist
            json.JSONDecodeError: If JSON parsing fails

        Example:
            >>> loader.load_json_to_postgres("data/raw/telegram_messages/2026-01-18")
            >>> loader.load_json_to_postgres("data/raw/telegram_messages/2026-01-18/CheMed123.json")
        """
        path = Path(json_path)

        if not path.exists():
            raise FileNotFoundError(f"Path not found: {json_path}")

        # Collect all JSON files
        json_files = []
        if path.is_file() and path.suffix == ".json":
            json_files = [path]
        elif path.is_dir():
            json_files = list(path.rglob("*.json"))
        else:
            raise ValueError(f"Invalid path: {json_path}")

        if not json_files:
            self.logger.warning(f"No JSON files found in {json_path}")
            return 0

        total_loaded = 0

        for json_file in json_files:
            self.logger.info(f"Loading data from {json_file}")

            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Handle both single message and list of messages
                if isinstance(data, dict):
                    messages = [data]
                elif isinstance(data, list):
                    messages = data
                else:
                    self.logger.warning(f"Unexpected data format in {json_file}")
                    continue

                # Load in batches
                for i in range(0, len(messages), batch_size):
                    batch = messages[i : i + batch_size]
                    loaded = self.bulk_insert(batch)
                    total_loaded += loaded

            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON from {json_file}: {e}")
                continue
            except Exception as e:
                self.logger.error(f"Error loading {json_file}: {e}")
                continue

        self.logger.info(f"Total messages loaded: {total_loaded}")
        return total_loaded

    def get_table_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the raw.telegram_messages table.

        Returns:
            Dictionary with table statistics

        Example:
            >>> stats = loader.get_table_stats()
            >>> print(f"Total messages: {stats['total_messages']}")
        """
        query = """
            SELECT 
                COUNT(*) as total_messages,
                COUNT(DISTINCT channel_name) as unique_channels,
                MIN(message_date) as earliest_message,
                MAX(message_date) as latest_message,
                COUNT(*) FILTER (WHERE has_media = TRUE) as messages_with_media
            FROM raw.telegram_messages
        """

        try:
            result = self.db_connector.execute_query(query)
            return result[0] if result else {}
        except Error as e:
            self.logger.error(f"Error getting table stats: {e}")
            return {}
