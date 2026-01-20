#!/usr/bin/env python3
"""
Script to load raw JSON data from data lake to PostgreSQL.

This script loads scraped Telegram data from the data lake into the
PostgreSQL raw schema for further transformation with dbt.

Usage:
    python scripts/load_raw_data.py --path data/raw/telegram_messages/2026-01-18
    python scripts/load_raw_data.py --path data/raw/telegram_messages --date 2026-01-18
    python scripts/load_raw_data.py --all
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.db_connector import DatabaseConnector
from src.database.data_loader import DataLoader
from src.utils.logger import get_logger


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration."""
    level = getattr(logging, log_level.upper())
    return get_logger(__name__, level=level)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Load raw Telegram data from data lake to PostgreSQL"
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--path", type=str, help="Path to JSON file or directory to load"
    )
    group.add_argument(
        "--date", type=str, help="Date folder to load (format: YYYY-MM-DD)"
    )
    group.add_argument(
        "--all", action="store_true", help="Load all data from data lake"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=1000,
        help="Number of records to insert per batch (default: 1000)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--create-table",
        action="store_true",
        help="Create raw table if it doesn't exist",
    )

    parser.add_argument(
        "--show-stats", action="store_true", help="Show table statistics after loading"
    )

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()
    logger = setup_logging(args.log_level)

    logger.info("=" * 60)
    logger.info("Raw Data Loader - Medical Telegram Warehouse")
    logger.info("=" * 60)

    try:
        # Initialize database connector
        logger.info("Connecting to PostgreSQL database...")
        db_connector = DatabaseConnector()
        db_connector.connect()

        # Create schemas if needed
        db_connector.create_schemas(["raw", "staging", "marts"])

        # Initialize data loader
        loader = DataLoader(db_connector)

        # Create table if requested
        if args.create_table:
            logger.info("Creating raw.telegram_messages table...")
            loader.create_raw_table()

        # Determine path to load
        if args.path:
            load_path = args.path
        elif args.date:
            load_path = f"data/raw/telegram_messages/{args.date}"
        else:  # --all
            load_path = "data/raw/telegram_messages"

        logger.info(f"Loading data from: {load_path}")

        # Check if path exists
        if not Path(load_path).exists():
            logger.error(f"Path not found: {load_path}")
            sys.exit(1)

        # Load data
        start_time = datetime.now()
        total_loaded = loader.load_json_to_postgres(
            load_path, batch_size=args.batch_size
        )
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info("=" * 60)
        logger.info(f"✅ Data loading completed successfully!")
        logger.info(f"Total messages loaded: {total_loaded}")
        logger.info(f"Duration: {duration:.2f} seconds")

        # Show table statistics if requested
        if args.show_stats:
            logger.info("=" * 60)
            logger.info("Table Statistics:")
            stats = loader.get_table_stats()
            for key, value in stats.items():
                logger.info(f"  {key}: {value}")

        logger.info("=" * 60)

        # Close database connection
        db_connector.close()

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error during data loading: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
