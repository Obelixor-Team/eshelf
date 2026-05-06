"""Integration test to verify the grid layout behavior."""

from unittest.mock import MagicMock

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from src.database.repository import BookRepository  # noqa: E402
from src.models.book import Book, BookObject  # noqa: E402
from src.models.book_model import BookListModel  # noqa: E402
from src.ui.book_widget import BookWidget  # noqa: E402
from src.ui.shelf_grid import ShelfGrid  # noqa: E402


def test_shelf_grid_layout_columns() -> None:
    """Verify that multiple books are placed in different columns."""
    mock_repo = MagicMock(spec=BookRepository)
    grid = ShelfGrid(
        repository=mock_repo,
        on_book_selected_callback=lambda b: None,
        on_book_right_clicked_callback=None,
    )

    # Verify the model is correct
    assert grid.grid_view.get_model() == grid.selection_model
    assert grid.selection_model.get_model() == grid.model


def test_shelf_grid_update_config() -> None:
    """Test updating the grid configuration."""
    mock_repo = MagicMock(spec=BookRepository)
    grid = ShelfGrid(repository=mock_repo, on_book_selected_callback=lambda b: None)

    # Update config
    new_config = {"zoom_level": 2.0, "show_titles": False}
    grid.update_config(new_config)

    assert grid._config == new_config


def test_shelf_grid_factory_setup() -> None:
    """Test the grid item factory setup."""
    mock_repo = MagicMock(spec=BookRepository)
    grid = ShelfGrid(repository=mock_repo, on_book_selected_callback=lambda b: None)
    mock_factory = MagicMock()
    mock_item = MagicMock()

    grid._on_factory_setup(mock_factory, mock_item)

    assert mock_item.get_child() is not None
    assert hasattr(mock_item.get_child(), "get_first_child")


def test_shelf_grid_factory_bind() -> None:
    """Test the grid item factory bind."""
    mock_repo = MagicMock(spec=BookRepository)
    grid = ShelfGrid(repository=mock_repo, on_book_selected_callback=lambda b: None)
    mock_factory = MagicMock()
    mock_item = MagicMock()

    book = Book(path="/tmp/book1.pdf", title="Title", author="Author")
    book_obj = BookObject(book)

    mock_item.get_item.return_value = book_obj

    # Create a mock box and widget
    mock_box = MagicMock()
    mock_widget = MagicMock(spec=BookWidget)
    mock_item.get_child.return_value = mock_box
    mock_box.get_first_child.return_value = mock_widget

    grid._on_factory_bind(mock_factory, mock_item)

    mock_widget.bind.assert_called_once()


def test_shelf_grid_get_selected_books() -> None:
    """Test retrieving selected books from the grid."""
    mock_repo = MagicMock(spec=BookRepository)
    grid = ShelfGrid(repository=mock_repo, on_book_selected_callback=lambda b: None)

    # Use a real instance of BookListModel to satisfy Gio.ListModel expectations
    grid.model = BookListModel(mock_repo)
    grid.selection_model.set_model(grid.model)

    # Mock selection
    grid.selection_model.get_selection = MagicMock()
    mock_selection = MagicMock()
    grid.selection_model.get_selection.return_value = mock_selection

    # Mock repository data
    mock_repo.get_book_count.return_value = 5
    grid.model._n_items = 5

    # Select books 0 and 2
    mock_selection.contains.side_effect = lambda i: i in [0, 2]
    mock_repo.get_books_by_category_paginated.side_effect = (
        lambda cat, limit, offset, all_books=False, search_query=None: [
            Book(
                path=f"/tmp/book{offset + i}.pdf",
                title=f"Book {offset + i}",
                author="Author",
            )
            for i in range(min(limit, 5 - offset))
        ]
    )
    selected = grid.get_selected_books()
    assert len(selected) == 2
    assert selected[0].path == "/tmp/book0.pdf"
    assert selected[1].path == "/tmp/book2.pdf"
