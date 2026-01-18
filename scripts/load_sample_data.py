#!/usr/bin/env python3
"""
Load sample data into raw.telegram_messages for testing.

This script inserts test data to verify the dbt models work correctly.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.database.db_connector import DatabaseConnector
from src.utils.logger import get_logger

logger = get_logger(__name__)


def load_sample_data():
    """Load sample data into raw table."""

    # Sample data
    base_date = datetime(2024, 1, 15, 10, 0, 0)

    sample_messages = [
        # CheMed123 channel
        (
            1001,
            "CheMed123",
            base_date,
            "New stock! Paracetamol 500mg tablets available. Price: 50 Birr/box. Contact us for orders.",
            True,
            "data/raw/images/CheMed123/1001.jpg",
            1250,
            45,
            12,
            "photo",
        ),
        (
            1002,
            "CheMed123",
            base_date + timedelta(hours=2),
            "Ibuprofen 400mg - Anti-inflammatory medication. Best quality guaranteed! 65 Birr",
            True,
            "data/raw/images/CheMed123/1002.jpg",
            980,
            32,
            8,
            "photo",
        ),
        (
            1003,
            "CheMed123",
            base_date + timedelta(hours=5),
            "Vitamin C tablets 1000mg. Boost your immunity! Only 120 Birr per bottle.",
            True,
            "data/raw/images/CheMed123/1003.jpg",
            1450,
            67,
            15,
            "photo",
        ),
        (
            1004,
            "CheMed123",
            base_date + timedelta(days=1),
            "Amoxicillin 500mg capsules - Antibiotic. Doctor prescription required. 180 Birr",
            False,
            None,
            2100,
            89,
            23,
            None,
        ),
        (
            1005,
            "CheMed123",
            base_date + timedelta(days=1, hours=3),
            "Special offer! Buy 2 get 1 free on all vitamin supplements this week only!",
            True,
            "data/raw/images/CheMed123/1005.jpg",
            3200,
            156,
            45,
            "photo",
        ),
        # lobelia4cosmetics channel
        (
            2001,
            "lobelia4cosmetics",
            base_date,
            "New moisturizing cream with vitamin E. Perfect for dry skin. 250 Birr",
            True,
            "data/raw/images/lobelia4cosmetics/2001.jpg",
            890,
            23,
            6,
            "photo",
        ),
        (
            2002,
            "lobelia4cosmetics",
            base_date + timedelta(hours=4),
            "Anti-aging serum with retinol. Reduce wrinkles naturally! 450 Birr",
            True,
            "data/raw/images/lobelia4cosmetics/2002.jpg",
            1120,
            34,
            9,
            "photo",
        ),
        (
            2003,
            "lobelia4cosmetics",
            base_date + timedelta(days=1),
            "Organic face wash for sensitive skin. Gentle and effective. 180 Birr",
            True,
            "data/raw/images/lobelia4cosmetics/2003.jpg",
            760,
            18,
            4,
            "photo",
        ),
        (
            2004,
            "lobelia4cosmetics",
            base_date + timedelta(days=1, hours=6),
            "Limited edition! Luxury skincare gift set. Contains cleanser, toner, and moisturizer. 800 Birr",
            True,
            "data/raw/images/lobelia4cosmetics/2004.jpg",
            2450,
            98,
            34,
            "photo",
        ),
        # tikvahpharma channel
        (
            3001,
            "tikvahpharma",
            base_date,
            "Insulin pens available. Contact for pricing. Medical prescription required.",
            False,
            None,
            450,
            12,
            5,
            None,
        ),
        (
            3002,
            "tikvahpharma",
            base_date + timedelta(hours=3),
            "Blood pressure monitor - Digital and accurate. 890 Birr",
            True,
            "data/raw/images/tikvahpharma/3002.jpg",
            1340,
            45,
            11,
            "photo",
        ),
        (
            3003,
            "tikvahpharma",
            base_date + timedelta(days=1),
            "Diabetes test strips - 50 strips per box. 320 Birr",
            True,
            "data/raw/images/tikvahpharma/3003.jpg",
            980,
            28,
            8,
            "photo",
        ),
        (
            3004,
            "tikvahpharma",
            base_date + timedelta(days=2),
            "Nebulizer for asthma treatment. High quality imported model. 1500 Birr",
            True,
            "data/raw/images/tikvahpharma/3004.jpg",
            670,
            19,
            7,
            "photo",
        ),
        (
            3005,
            "tikvahpharma",
            base_date + timedelta(days=2, hours=5),
            "Omega-3 fish oil capsules. Support heart health. 280 Birr per bottle",
            True,
            "data/raw/images/tikvahpharma/3005.jpg",
            1890,
            67,
            18,
            "photo",
        ),
        # Additional diverse data
        (
            4001,
            "CheMed123",
            base_date + timedelta(days=3),
            "",
            False,
            None,
            45,
            2,
            0,
            None,
        ),  # Empty message
        (
            4002,
            "lobelia4cosmetics",
            base_date + timedelta(days=3),
            "Flash sale today!",
            False,
            None,
            5600,
            234,
            89,
            None,
        ),  # High engagement
        (
            4003,
            "tikvahpharma",
            base_date + timedelta(days=4),
            "Medical equipment consultation available. DM for details.",
            False,
            None,
            320,
            8,
            3,
            None,
        ),
    ]

    # Connect to database
    db = DatabaseConnector()

    try:
        db.connect()
        logger.info("Connected to database")

        # Insert sample data
        insert_sql = """
        INSERT INTO raw.telegram_messages 
        (message_id, channel_name, message_date, message_text, has_media, 
         image_path, views, forwards, replies, media_type)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (message_id) DO NOTHING;
        """

        with db.get_connection() as conn:
            with conn.cursor() as cur:
                inserted = 0
                for msg in sample_messages:
                    cur.execute(insert_sql, msg)
                    if cur.rowcount > 0:
                        inserted += 1
                conn.commit()

        logger.info(f"✅ Successfully inserted {inserted} sample messages")

        # Verify data
        with db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM raw.telegram_messages")
                count = cur.fetchone()[0]
                logger.info(f"Total messages in database: {count}")

    except Exception as e:
        logger.error(f"Error loading sample data: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_sample_data()
