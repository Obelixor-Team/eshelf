"""Configuration management for eShelf."""

import json
import os
from typing import Any

CONFIG_FILE = os.path.expanduser("~/.config/eshelf/config.json")

DEFAULT_CONFIG = {
    "books_per_line": 6,
    "zoom_level": 1.0,
    "cache_dir": os.path.join(os.path.expanduser("~"), ".cache", "eshelf", "covers"),
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
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
