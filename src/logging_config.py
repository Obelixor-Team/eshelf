"""Logging configuration for eShelf."""

import logging
import os
from typing import Any


def setup_logging(config: dict[str, Any]) -> None:
    """Configure logging for the application.

    Args:
        config (dict[str, Any]): Application configuration dictionary.
    """
    log_level_str = config.get("log_level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Format for logs
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    # File handler
    log_dir = os.path.expanduser("~/.local/share/eshelf")
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.FileHandler(os.path.join(log_dir, "eshelf.log"))
    file_handler.setFormatter(log_format)

    # Root logger configuration
    logging.basicConfig(level=log_level, handlers=[console_handler, file_handler])

    # Set level for specific libraries to avoid noise
    logging.getLogger("ebooklib").setLevel(logging.WARNING)
    logging.getLogger("pdf2image").setLevel(logging.WARNING)
