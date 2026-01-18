#!/usr/bin/env python3
"""
Create the raw.telegram_messages table.

This script creates the raw table structure in PostgreSQL to store
scraped Telegram messages before transformation.
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db_connector import DatabaseConnector
from src.utils.logger import get_logger

logger = get_logger(__name__)


def create_raw_table():
    """Create the raw.telegram_messages table."""

    # Create database connector
    db = DatabaseConnector()

    try:
        # Connect to database
        db.connect()
        logger.info("Connected to database")

        # SQL to create table
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS raw.telegram_messages (
            message_id BIGINT PRIMARY KEY,
            channel_name VARCHAR(255) NOT NULL,
            message_date TIMESTAMP NOT NULL,
            message_text TEXT,
            has_media BOOLEAN DEFAULT FALSE,
            image_path TEXT,
            views INTEGER DEFAULT 0,
            forwards INTEGER DEFAULT 0,
            replies INTEGER DEFAULT 0,
            media_type VARCHAR(50),
            scraped_at TIMESTAMP DEFAULT NOW()
        );
        
        CREATE INDEX IF NOT EXISTS idx_channel_name ON raw.telegram_messages(channel_name);
        CREATE INDEX IF NOT EXISTS idx_message_date ON raw.telegram_messages(message_date);
        """

        # Execute table creation
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(create_table_sql)
                conn.commit()

        logger.info("Successfully created raw.telegram_messages table")

        # Verify table exists
        if db.table_exists("telegram_messages", schema="raw"):
            logger.info("✅ Table verification successful")
        else:
            logger.error("❌ Table verification failed")

    except Exception as e:
        logger.error(f"Error creating table: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    create_raw_table()
