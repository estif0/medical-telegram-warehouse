#!/usr/bin/env python3
"""
Run Telegram scraper to collect messages and images from channels.

Usage:
    python scripts/run_scraper.py --channels CheMed123 lobelia4cosmetics --limit 100
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.scraper.telegram_scraper import TelegramScraper
from src.scraper.data_lake_manager import DataLakeManager
from src.utils.logger import get_logger


logger = get_logger(__name__)


async def main():
    """Main scraper execution."""
    parser = argparse.ArgumentParser(description="Scrape Telegram channels")
    parser.add_argument(
        "--channels",
        nargs="+",
        required=True,
        help="Channel usernames to scrape (space-separated)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum messages per channel (default: 100)",
    )
    parser.add_argument(
        "--download-media", action="store_true", help="Download images from messages"
    )
    parser.add_argument(
        "--data-path", default="data", help="Base path for data lake (default: data)"
    )

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    phone = os.getenv("TELEGRAM_PHONE")

    if not all([api_id, api_hash, phone]):
        logger.error("Missing Telegram credentials in .env file")
        logger.error("Required: TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE")
        sys.exit(1)

    # Initialize components
    scraper = TelegramScraper(int(api_id), api_hash, phone)
    data_lake = DataLakeManager(base_path=args.data_path)

    try:
        # Connect to Telegram
        await scraper.connect()

        channel_stats = {}

        # Scrape each channel
        for channel in args.channels:
            logger.info(f"📡 Scraping channel: {channel}")

            try:
                # Fetch messages
                messages = await scraper.get_channel_messages(channel, limit=args.limit)

                if not messages:
                    logger.warning(f"No messages fetched from {channel}")
                    continue

                # Save messages to data lake
                data_lake.save_message_json(messages, channel.strip("@"))

                channel_stats[channel.strip("@")] = len(messages)

                # Download media if requested
                if args.download_media:
                    images_dir = data_lake.get_images_dir(channel.strip("@"))
                    await scraper.download_channel_media(messages, images_dir)

            except Exception as e:
                logger.error(f"Failed to scrape {channel}: {e}")
                continue

        # Write manifest
        if channel_stats:
            from datetime import datetime

            date_str = datetime.now().strftime("%Y-%m-%d")
            data_lake.write_manifest(date_str, channel_stats)

            total = sum(channel_stats.values())
            logger.info(f"✅ Scraping complete! Total messages: {total}")
            logger.info(f"📊 Channel stats: {channel_stats}")

    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        sys.exit(1)
    finally:
        await scraper.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
