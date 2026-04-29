"""Entry point for the eShelf application."""

import os
import sys
from typing import Any

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw  # noqa: E402

from src.config import DEFAULT_CONFIG, load_config  # noqa: E402
from src.controller.main_controller import MainController  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    """Initialize and run the eShelf application."""
    config = load_config()
    home = os.path.expanduser("~")
    library_dir = os.path.join(home, "Documents", "Books")
    db_path = os.path.join(home, ".local/share/eshelf/library.db")
    cache_dir = str(config.get("cache_dir") or DEFAULT_CONFIG["cache_dir"])

    # Ensure directories exist
    os.makedirs(os.path.dirname(db_path) if db_path else ".", exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(library_dir, exist_ok=True)

    # Initialize Backend
    controller = MainController(library_dir, db_path, cache_dir)

    # Initialize UI
    app = Adw.Application(application_id="ai.opencode.eshelf")

    def on_activate(app: Any) -> None:
        win = MainWindow(application=app)
        win.set_controller(controller)
        win.present()

    app.connect("activate", on_activate)
    app.run(sys.argv)


if __name__ == "__main__":
    main()
