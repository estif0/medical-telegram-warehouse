"""
Centralized logging configuration for the Medical Telegram Warehouse project.

This module provides a consistent logging setup across all modules.

Example:
    >>> from src.utils.logger import get_logger
    >>> logger = get_logger(__name__)
    >>> logger.info("Starting scraper...")
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional


def get_logger(
    name: str,
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = "logs",
) -> logging.Logger:
    """
    Get or create a logger with consistent formatting.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (default: logging.INFO)
        log_to_file: Whether to log to file (default: True)
        log_dir: Directory for log files (default: "logs")

    Returns:
        Configured logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started")
    """
    logger = logging.getLogger(name)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = Path(log_dir) / f"{today}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
