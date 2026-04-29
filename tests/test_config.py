"""Tests for configuration management."""

import os

from src.config import CONFIG_FILE, load_config, save_config


def test_load_config_defaults() -> None:
    """Test that load_config returns defaults if no file exists."""
    # Ensure config file doesn't exist
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

    config = load_config()
    assert config["books_per_line"] == 10
    assert config["zoom_level"] == 1.0
    assert "cache_dir" in config


def test_save_and_load_config() -> None:
    """Test that config can be saved and loaded correctly."""
    test_config = {
        "books_per_line": 5,
        "zoom_level": 1.5,
        "cache_dir": "/tmp/eshelf_cache",
    }

    save_config(test_config)
    loaded_config = load_config()

    assert loaded_config["books_per_line"] == 5
    assert loaded_config["zoom_level"] == 1.5
    assert loaded_config["cache_dir"] == "/tmp/eshelf_cache"


def test_load_config_partial() -> None:
    """Test that loading partial config merges with defaults."""
    import json

    # Create a partial config file
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump({"books_per_line": 20}, f)

    config = load_config()
    assert config["books_per_line"] == 20
    assert config["zoom_level"] == 1.0  # Default
