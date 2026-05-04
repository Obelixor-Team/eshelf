"""Configuration management for eShelf."""

__all__ = [
    "DEFAULT_CONFIG",
    "load_config",
    "save_config",
    "user_data_dir",
    "user_cache_dir",
    "user_config_dir",
]

import json
import os
from typing import Any, Literal

try:
    from platformdirs import user_cache_dir, user_config_dir, user_data_dir
except ImportError:

    def user_config_dir(
        appname: str | None = None,
        appauthor: str | Literal[False] | None = None,
        version: str | None = None,
        roaming: bool = False,
        ensure_exists: bool = False,
        use_site_for_root: bool = False,
    ) -> str:
        """Fallback for user_config_dir when platformdirs is not available."""
        if not appname:
            return os.path.expanduser("~/.config")
        return os.path.expanduser(f"~/.config/{appname}")

    def user_cache_dir(
        appname: str | None = None,
        appauthor: str | Literal[False] | None = None,
        version: str | None = None,
        opinion: bool = True,
        ensure_exists: bool = False,
        use_site_for_root: bool = False,
    ) -> str:
        """Fallback for user_cache_dir when platformdirs is not available."""
        if not appname:
            return os.path.expanduser("~/.cache")
        return os.path.expanduser(f"~/.cache/{appname}")

    def user_data_dir(
        appname: str | None = None,
        appauthor: str | Literal[False] | None = None,
        version: str | None = None,
        roaming: bool = False,
        ensure_exists: bool = False,
        use_site_for_root: bool = False,
    ) -> str:
        """Fallback for user_data_dir when platformdirs is not available."""
        if not appname:
            return os.path.expanduser("~/.local/share")
        return os.path.expanduser(f"~/.local/share/{appname}")


CONFIG_FILE = os.path.join(user_config_dir("eshelf"), "config.json")

DEFAULT_CONFIG = {
    "books_per_line": 6,
    "zoom_level": 1.0,
    "cache_dir": os.path.join(user_cache_dir("eshelf"), "covers"),
    "library_dirs": [os.path.join(user_data_dir("eshelf"), "Books")],
    "last_category_identifier": "all",
    "sidebar_visible": True,
    "last_sort_option": "Title",
    "show_titles": True,
    "log_level": "INFO",
    "appearance": "System",
}


def load_config() -> dict[str, Any]:
    """Load configuration from file or return defaults."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            loaded = json.load(f)

            # Migration: library_dir -> library_dirs
            if "library_dir" in loaded and "library_dirs" not in loaded:
                old_dir = loaded.pop("library_dir")
                if isinstance(old_dir, str):
                    loaded["library_dirs"] = [old_dir]

            # Merge with defaults
            config = {**DEFAULT_CONFIG, **loaded}

            # Basic validation/coercion
            if (
                not isinstance(config["books_per_line"], int)
                or config["books_per_line"] < 1
            ):
                config["books_per_line"] = DEFAULT_CONFIG["books_per_line"]

            if (
                not isinstance(config["zoom_level"], (int, float))
                or config["zoom_level"] < 0.1
            ):
                config["zoom_level"] = DEFAULT_CONFIG["zoom_level"]

            # Ensure string fields are strings
            for key in [
                "cache_dir",
                "last_category_identifier",
                "last_sort_option",
                "appearance",
            ]:
                if not isinstance(config.get(key), str):
                    config[key] = DEFAULT_CONFIG.get(key)

            # Ensure library_dirs is a list of strings
            if not isinstance(config["library_dirs"], list) or not all(
                isinstance(p, str) for p in config["library_dirs"]
            ):
                config["library_dirs"] = DEFAULT_CONFIG["library_dirs"]

            # Ensure boolean fields are booleans
            for key in ["sidebar_visible", "show_titles"]:
                if not isinstance(config.get(key), bool):
                    config[key] = DEFAULT_CONFIG[key]

            return config
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

    library_dirs = full_config.get("library_dirs")
    if not isinstance(library_dirs, list) or not all(
        isinstance(p, str) for p in library_dirs
    ):
        raise ValueError("library_dirs must be a list of strings")

    last_category_identifier = full_config.get("last_category_identifier")
    if not isinstance(last_category_identifier, str):
        raise ValueError("last_category_identifier must be a string")

    sidebar_visible = full_config.get("sidebar_visible")
    if not isinstance(sidebar_visible, bool):
        raise ValueError("sidebar_visible must be a boolean")

    show_titles = full_config.get("show_titles")
    if not isinstance(show_titles, bool):
        raise ValueError("show_titles must be a boolean")

    last_sort_option = full_config.get("last_sort_option")
    if not isinstance(last_sort_option, str):
        raise ValueError("last_sort_option must be a string")

    appearance = full_config.get("appearance")
    if not isinstance(appearance, str):
        raise ValueError("appearance must be a string")

    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(full_config, f, indent=4)
