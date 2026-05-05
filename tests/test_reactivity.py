"""Tests for UI configuration reactivity."""

import pytest
from unittest.mock import MagicMock
from src.ui.shelf_grid import ShelfGrid
from src.models.book import Book


def test_shelf_grid_reactivity() -> None:
    """Verify that ShelfGrid updates its column layout when config changes."""
    # Mock callbacks
    on_book_selected = MagicMock()

    # Initialize ShelfGrid
    grid = ShelfGrid(on_book_selected_callback=on_book_selected)

    # Verify initial config (default is 6)
    assert grid.grid_view.get_max_columns() == 6

    # Update config
    new_config = {"books_per_line": 4, "zoom_level": 2.0}
    grid.update_config(new_config)

    # Verify reactivity
    assert grid.grid_view.get_max_columns() == 4
    assert grid._config.get("zoom_level") == 2.0
