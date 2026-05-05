"""Tests for UI configuration reactivity."""

from unittest.mock import MagicMock, patch

from src.database.repository import BookRepository
from src.ui.shelf_grid import ShelfGrid


def test_shelf_grid_reactivity() -> None:
    """Verify that ShelfGrid updates its column layout when config changes."""
    # Mock callbacks
    on_book_selected = MagicMock()

    # Initialize ShelfGrid
    with patch("src.ui.shelf_grid.load_config") as mock_load:
        mock_repo = MagicMock(spec=BookRepository)
        mock_load.return_value = {"books_per_line": 6, "zoom_level": 1.0}
        grid = ShelfGrid(
            repository=mock_repo, on_book_selected_callback=on_book_selected
        )
    # Verify initial config (default is 6)
    assert grid.grid_view.get_max_columns() == 6
    # Update config
    new_config = {"books_per_line": 4, "zoom_level": 2.0}
    grid.update_config(new_config)

    # Verify reactivity
    assert grid.grid_view.get_max_columns() == 4
    assert grid._config.get("zoom_level") == 2.0
