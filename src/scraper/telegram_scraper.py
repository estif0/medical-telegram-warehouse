"""
Telegram Scraper for extracting messages and media from channels.

This module provides an OOP interface for scraping Telegram channels
using the Telethon library.

Example:
    >>> from src.scraper.telegram_scraper import TelegramScraper
    >>> scraper = TelegramScraper(api_id, api_hash, phone)
    >>> await scraper.connect()
    >>> messages = await scraper.get_channel_messages("CheMed123", limit=100)
    >>> await scraper.disconnect()
"""

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import MessageMediaPhoto

from src.utils.logger import get_logger


class TelegramScraper:
    """
    Scrapes messages and media from Telegram channels.

    Attributes:
        api_id: Telegram API ID
        api_hash: Telegram API hash
        phone: Phone number for authentication
        client: Telethon client instance
        logger: Logger instance

    Example:
        >>> scraper = TelegramScraper(12345, "abc123", "+1234567890")
        >>> await scraper.connect()
        >>> messages = await scraper.get_channel_messages("channel_name")
        >>> await scraper.disconnect()
    """

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        session_name: str = "scraper_session",
    ):
        """
        Initialize Telegram scraper.

        Args:
            api_id: Telegram API ID from https://my.telegram.org
            api_hash: Telegram API hash
            phone: Phone number with country code (e.g., "+1234567890")
            session_name: Session file name (default: "scraper_session")

        Raises:
            ValueError: If credentials are invalid
        """
        if not api_id or not api_hash or not phone:
            raise ValueError("API ID, API hash, and phone number are required")

        self.api_id = api_id
        self.api_hash = api_hash
        self.phone = phone
        self.session_name = session_name
        self.client: Optional[TelegramClient] = None
        self.logger = get_logger(__name__)

        self.logger.info(f"Initialized TelegramScraper with session: {session_name}")

    async def connect(self) -> None:
        """
        Establish connection to Telegram.

        Creates and starts a Telegram client session.

        Raises:
            ConnectionError: If connection fails

        Example:
            >>> await scraper.connect()
        """
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start(phone=self.phone)
            self.logger.info("✅ Connected to Telegram successfully")

        except Exception as e:
            self.logger.error(f"Failed to connect to Telegram: {e}")
            raise ConnectionError(f"Telegram connection failed: {e}")

    async def disconnect(self) -> None:
        """
        Close Telegram connection gracefully.

        Example:
            >>> await scraper.disconnect()
        """
        if self.client:
            await self.client.disconnect()
            self.logger.info("Disconnected from Telegram")

    async def get_channel_messages(
        self,
        channel: str,
        limit: int = 100,
        message_delay: float = 0.5,
        max_retries: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Fetch messages from a Telegram channel.

        Args:
            channel: Channel username (with or without @)
            limit: Maximum number of messages to fetch (default: 100)
            message_delay: Delay between message fetches in seconds (default: 0.5)
            max_retries: Maximum retry attempts on rate limit (default: 3)

        Returns:
            List of message dictionaries with fields:
                - message_id: Unique message identifier
                - channel_name: Channel username (without @)
                - channel_title: Channel display title
                - message_date: ISO format timestamp
                - message_text: Message content
                - has_media: Boolean indicating media presence
                - views: View count
                - forwards: Forward count

        Raises:
            ValueError: If channel doesn't exist or is inaccessible
            FloodWaitError: If rate limited by Telegram

        Example:
            >>> messages = await scraper.get_channel_messages("CheMed123", limit=50)
            >>> print(f"Fetched {len(messages)} messages")
        """
        if not self.client:
            raise ConnectionError("Client not connected. Call connect() first.")

        channel_name = channel.strip("@")
        messages = []
        retries = 0

        while retries <= max_retries:
            try:
                # Get channel entity
                entity = await self.client.get_entity(channel)
                channel_title = getattr(entity, "title", channel_name)

                self.logger.info(
                    f"Fetching messages from {channel_name} (limit={limit})"
                )

                # Iterate through messages
                async for message in self.client.iter_messages(entity, limit=limit):
                    message_dict = {
                        "message_id": message.id,
                        "channel_name": channel_name,
                        "channel_title": channel_title,
                        "message_date": (
                            message.date.isoformat() if message.date else None
                        ),
                        "message_text": message.message or "",
                        "has_media": message.media is not None,
                        "views": message.views or 0,
                        "forwards": message.forwards or 0,
                    }

                    messages.append(message_dict)

                    # Rate limiting
                    if message_delay > 0:
                        await asyncio.sleep(message_delay)

                self.logger.info(
                    f"✅ Fetched {len(messages)} messages from {channel_name}"
                )
                return messages

            except FloodWaitError as e:
                wait_seconds = getattr(e, "seconds", 60)
                retries += 1

                if retries > max_retries:
                    self.logger.error(
                        f"Max retries exceeded for {channel_name} due to rate limiting"
                    )
                    raise

                self.logger.warning(
                    f"Rate limited. Waiting {wait_seconds}s (retry {retries}/{max_retries})"
                )
                await asyncio.sleep(wait_seconds)

            except Exception as e:
                self.logger.error(f"Error fetching messages from {channel_name}: {e}")
                raise ValueError(f"Failed to fetch from {channel}: {e}")

        return messages

    async def download_media(
        self, message_id: int, channel: str, output_path: Path, max_retries: int = 3
    ) -> Optional[Path]:
        """
        Download media (image) from a message.

        Args:
            message_id: Message identifier
            channel: Channel username
            output_path: Path where image should be saved
            max_retries: Maximum retry attempts (default: 3)

        Returns:
            Path to downloaded file, or None if no media or download failed

        Example:
            >>> path = await scraper.download_media(
            ...     12345, "CheMed123", Path("data/raw/images/CheMed123/12345.jpg")
            ... )
        """
        if not self.client:
            raise ConnectionError("Client not connected. Call connect() first.")

        retries = 0
        channel_name = channel.strip("@")

        while retries <= max_retries:
            try:
                entity = await self.client.get_entity(channel)
                message = await self.client.get_messages(entity, ids=message_id)

                if not message or not message.media:
                    self.logger.debug(
                        f"No media in message {message_id} from {channel_name}"
                    )
                    return None

                if not isinstance(message.media, MessageMediaPhoto):
                    self.logger.debug(f"Message {message_id} media is not a photo")
                    return None

                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Download media
                await self.client.download_media(message.media, str(output_path))
                self.logger.debug(f"Downloaded media: {output_path}")
                return output_path

            except FloodWaitError as e:
                wait_seconds = getattr(e, "seconds", 60)
                retries += 1

                if retries > max_retries:
                    self.logger.error(
                        f"Max retries exceeded downloading media {message_id}"
                    )
                    return None

                self.logger.warning(f"Rate limited. Waiting {wait_seconds}s")
                await asyncio.sleep(wait_seconds)

            except Exception as e:
                self.logger.error(f"Error downloading media {message_id}: {e}")
                return None

        return None

    async def download_channel_media(
        self, messages: List[Dict[str, Any]], output_dir: Path, delay: float = 1.0
    ) -> Dict[int, Optional[Path]]:
        """
        Download all media from a list of messages.

        Args:
            messages: List of message dictionaries (from get_channel_messages)
            output_dir: Base directory for saving images
            delay: Delay between downloads in seconds (default: 1.0)

        Returns:
            Dictionary mapping message_id to download path (or None if failed)

        Example:
            >>> messages = await scraper.get_channel_messages("CheMed123")
            >>> results = await scraper.download_channel_media(
            ...     messages, Path("data/raw/images/CheMed123")
            ... )
        """
        if not messages:
            return {}

        results = {}
        channel_name = messages[0].get("channel_name", "unknown")
        media_messages = [msg for msg in messages if msg.get("has_media")]

        self.logger.info(
            f"Downloading {len(media_messages)} images from {channel_name}"
        )

        for msg in media_messages:
            message_id = msg["message_id"]
            output_path = output_dir / f"{message_id}.jpg"

            path = await self.download_media(message_id, channel_name, output_path)
            results[message_id] = path

            if delay > 0:
                await asyncio.sleep(delay)

        success_count = sum(1 for p in results.values() if p is not None)
        self.logger.info(
            f"Downloaded {success_count}/{len(media_messages)} images from {channel_name}"
        )

        return results

    def __enter__(self):
        """Context manager support (synchronous - use async with instead)."""
        raise TypeError("Use 'async with' instead of 'with'")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
