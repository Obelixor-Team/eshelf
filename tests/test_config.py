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
        "library_dir": "/tmp/eshelf_library",
    }

    save_config(test_config)
    loaded_config = load_config()

    assert loaded_config["books_per_line"] == 5
    assert loaded_config["zoom_level"] == 1.5
    assert loaded_config["cache_dir"] == "/tmp/eshelf_cache"
    assert loaded_config["library_dir"] == "/tmp/eshelf_library"


def test_load_config_partial(mock_config_file: str) -> None:
    """Test that loading partial config merges with defaults."""
    # Create a partial config file
    with open(mock_config_file, "w") as f:
        json.dump({"books_per_line": 20}, f)

    config = load_config()
    assert config["books_per_line"] == 20
    assert config["zoom_level"] == src.config.DEFAULT_CONFIG["zoom_level"]


def test_save_config_validation(mock_config_file: str) -> None:
    """Test that save_config validates input."""
    valid_config = {
        "books_per_line": 6,
        "zoom_level": 1.0,
        "cache_dir": "/tmp/cache",
        "library_dir": "/tmp/library",
    }

    # Test invalid books_per_line
    invalid_books = valid_config.copy()
    invalid_books["books_per_line"] = 0
    with pytest.raises(ValueError, match="books_per_line must be a positive integer"):
        save_config(invalid_books)

    invalid_books["books_per_line"] = "6"
    with pytest.raises(ValueError, match="books_per_line must be a positive integer"):
        save_config(invalid_books)

    # Test invalid zoom_level
    invalid_zoom = valid_config.copy()
    invalid_zoom["zoom_level"] = 0.05
    with pytest.raises(ValueError, match="zoom_level must be a positive number >= 0.1"):
        save_config(invalid_zoom)

    invalid_zoom["zoom_level"] = "1.0"
    with pytest.raises(ValueError, match="zoom_level must be a positive number >= 0.1"):
        save_config(invalid_zoom)

    # Test invalid cache_dir
    invalid_cache = valid_config.copy()
    invalid_cache["cache_dir"] = 123
    with pytest.raises(ValueError, match="cache_dir must be a string"):
        save_config(invalid_cache)

    # Test invalid library_dir
    invalid_lib = valid_config.copy()
    invalid_lib["library_dir"] = 123
    with pytest.raises(ValueError, match="library_dir must be a string"):
        save_config(invalid_lib)


def test_load_config_malformed_json(mock_config_file: str) -> None:
    """Test handling of malformed JSON."""
    with open(mock_config_file, "w") as f:
        f.write("{invalid:json}")

    config = load_config()
    assert config == src.config.DEFAULT_CONFIG


def test_load_config_invalid_values(mock_config_file: str) -> None:
    """Test handling of invalid types in the config file."""
    with open(mock_config_file, "w") as f:
        json.dump(
            {
                "books_per_line": "not-an-int",
                "zoom_level": -1,
                "sidebar_visible": "not-a-bool",
                "last_category_identifier": 123,
            },
            f,
        )

    config = load_config()
    assert config["books_per_line"] == src.config.DEFAULT_CONFIG["books_per_line"]
    assert config["zoom_level"] == src.config.DEFAULT_CONFIG["zoom_level"]
    assert config["sidebar_visible"] == src.config.DEFAULT_CONFIG["sidebar_visible"]


def test_platformdirs_fallback() -> None:
    """Test the platformdirs fallback functions."""
    import sys
    from unittest.mock import patch

    # Ensure platformdirs is not importable for the test
    with patch.dict(sys.modules, {"platformdirs": None}):
        # Reloading config module to trigger the except ImportError block
        import importlib

        import src.config

        importlib.reload(src.config)

        # Test the fallback functions directly if they exist on the module
        # This is tricky because the module is reloaded.
        # Let's check if the functions are defined as expected.
        assert hasattr(src.config, "user_config_dir")

        # Test the fallback behavior
        config_dir = src.config.user_config_dir("testapp")
        assert config_dir == os.path.expanduser("~/.config/testapp")

        cache_dir = src.config.user_cache_dir("testapp")
        assert cache_dir == os.path.expanduser("~/.cache/testapp")

        data_dir = src.config.user_data_dir("testapp")
        assert data_dir == os.path.expanduser("~/.local/share/testapp")
