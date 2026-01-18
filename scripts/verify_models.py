#!/usr/bin/env python3
"""
Verify the dbt models in the database.

This script queries the built models to verify data is correctly transformed.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db_connector import DatabaseConnector
from src.utils.logger import get_logger

logger = get_logger(__name__)


def verify_models():
    """Verify the dbt models."""

    db = DatabaseConnector()

    try:
        db.connect()
        logger.info("Connected to database")

        # Check schemas
        logger.info("\n=== Schemas ===")
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT schema_name 
                    FROM information_schema.schemata 
                    WHERE schema_name IN ('raw', 'staging_staging', 'staging_marts')
                    ORDER BY schema_name
                """
                )
                for row in cur.fetchall():
                    logger.info(f"  ✓ {row[0]}")

        # Check staging view
        logger.info("\n=== Staging View ===")
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM staging_staging.stg_telegram_messages"
                )
                count = cur.fetchone()[0]
                logger.info(f"  stg_telegram_messages: {count} rows")

        # Check dimension tables
        logger.info("\n=== Dimension Tables ===")
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                # dim_channels
                cur.execute("SELECT COUNT(*) FROM staging_marts.dim_channels")
                count = cur.fetchone()[0]
                logger.info(f"  dim_channels: {count} rows")

                cur.execute(
                    """
                    SELECT channel_name, total_posts, avg_views, activity_level 
                    FROM staging_marts.dim_channels 
                    ORDER BY total_posts DESC
                """
                )
                for row in cur.fetchall():
                    logger.info(
                        f"    - {row[0]}: {row[1]} posts, {row[2]:.1f} avg views, {row[3]} activity"
                    )

                # dim_dates
                cur.execute("SELECT COUNT(*) FROM staging_marts.dim_dates")
                count = cur.fetchone()[0]
                logger.info(f"\n  dim_dates: {count} rows")

                cur.execute(
                    """
                    SELECT MIN(full_date), MAX(full_date) 
                    FROM staging_marts.dim_dates
                """
                )
                min_date, max_date = cur.fetchone()
                logger.info(f"    Date range: {min_date} to {max_date}")

        # Check fact table
        logger.info("\n=== Fact Table ===")
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM staging_marts.fct_messages")
                count = cur.fetchone()[0]
                logger.info(f"  fct_messages: {count} rows")

                # Sample high engagement messages
                cur.execute(
                    """
                    SELECT 
                        LEFT(message_text, 50) as text_preview,
                        views,
                        forwards,
                        engagement_level
                    FROM staging_marts.fct_messages
                    ORDER BY views DESC
                    LIMIT 5
                """
                )
                logger.info("\n  Top 5 messages by views:")
                for row in cur.fetchall():
                    logger.info(
                        f"    - '{row[0]}...' - {row[1]} views, {row[2]} forwards ({row[3]})"
                    )

        logger.info("\n✅ All models verified successfully!")

    except Exception as e:
        logger.error(f"Error verifying models: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    verify_models()
