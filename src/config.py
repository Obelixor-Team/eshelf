"""Configuration management for eShelf."""

import json
import os
from typing import Any

CONFIG_FILE = os.path.expanduser("~/.config/eshelf/config.json")

DEFAULT_CONFIG = {
    "books_per_line": 6,
    "zoom_level": 1.0,
    "cache_dir": os.path.join(os.path.expanduser("~"), ".cache", "eshelf", "covers"),
    "library_dir": os.path.join(os.path.expanduser("~"), "Books"),
    "last_category_identifier": "all",
    "sidebar_visible": True,
    "last_sort_option": "Title",
    "log_level": "INFO",
}


def load_config() -> dict[str, Any]:
    """Load configuration from file or return defaults."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    # Merge with defaults to ensure all required keys are present
    full_config = {**DEFAULT_CONFIG, **config}

    # Validate configuration values
    books_per_line = full_config.get("books_per_line")
    if not isinstance(books_per_line, int) or books_per_line < 1:
        raise ValueError("books_per_line must be a positive integer")

    zoom_level = full_config.get("zoom_level")
    if not isinstance(zoom_level, (int, float)) or zoom_level < 0.1:
        raise ValueError("zoom_level must be a positive number >= 0.1")

    cache_dir = full_config.get("cache_dir")
    if not isinstance(cache_dir, str):
        raise ValueError("cache_dir must be a string")

    library_dir = full_config.get("library_dir")
    if not isinstance(library_dir, str):
        raise ValueError("library_dir must be a string")

    last_category_identifier = full_config.get("last_category_identifier")
    if not isinstance(last_category_identifier, str):
        raise ValueError("last_category_identifier must be a string")

    sidebar_visible = full_config.get("sidebar_visible")
    if not isinstance(sidebar_visible, bool):
        raise ValueError("sidebar_visible must be a boolean")

    last_sort_option = full_config.get("last_sort_option")
    if not isinstance(last_sort_option, str):
        raise ValueError("last_sort_option must be a string")

    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(full_config, f, indent=4)
