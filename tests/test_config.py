"""Tests for configuration management."""

import json
import os
import shutil
import tempfile
from typing import Generator

import pytest

import src.config
from src.config import load_config, save_config


@pytest.fixture  # type: ignore
def mock_config_file() -> Generator[str, None, None]:
    """Fixture to provide a temporary config file path and monkeypatch CONFIG_FILE."""
    test_dir = tempfile.mkdtemp()
    test_config_path = os.path.join(test_dir, "config.json")

    original_config_file = src.config.CONFIG_FILE
    src.config.CONFIG_FILE = test_config_path

    yield test_config_path

    src.config.CONFIG_FILE = original_config_file
    shutil.rmtree(test_dir)


def test_load_config_defaults(mock_config_file: str) -> None:
    """Test that load_config returns defaults if no file exists."""
    # Ensure config file doesn't exist (it shouldn't by default in temp dir)
    config = load_config()
    assert config["books_per_line"] == src.config.DEFAULT_CONFIG["books_per_line"]
    assert config["zoom_level"] == src.config.DEFAULT_CONFIG["zoom_level"]
    assert "cache_dir" in config


def test_save_and_load_config(mock_config_file: str) -> None:
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


def test_load_config_partial(mock_config_file: str) -> None:
    """Test that loading partial config merges with defaults."""
    # Create a partial config file
    with open(mock_config_file, "w") as f:
        json.dump({"books_per_line": 20}, f)

    config = load_config()
    assert config["books_per_line"] == 20
    assert config["zoom_level"] == src.config.DEFAULT_CONFIG["zoom_level"]
