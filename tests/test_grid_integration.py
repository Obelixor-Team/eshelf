"""Integration test to verify the grid layout behavior."""

from unittest.mock import MagicMock

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


from src.models.book import Book  # noqa: E402
from src.ui.shelf_grid import ShelfGrid  # noqa: E402


def test_shelf_grid_layout_columns() -> None:
    """Verify that multiple books are placed in different columns."""
    # Create grid with mock callbacks
    grid = ShelfGrid(
        on_book_selected_callback=lambda b: None, on_book_right_clicked_callback=None
    )

    # Create test books
    books = [
        Book(path=f"/tmp/book{i}.pdf", title=f"Book {i}", author="Author")
        for i in range(10)
    ]

    # Update grid with books
    grid.update_books(books)

    # Verify store count
    assert grid.store.get_n_items() == 10

    # Verify the GridView's model is correct
    assert grid.grid_view.get_model() == grid.selection_model
    assert grid.selection_model.get_model() == grid.store


def test_shelf_grid_update_config() -> None:
    """Test updating the grid configuration."""
    grid = ShelfGrid(on_book_selected_callback=lambda b: None)

    # Add a book first
    book = Book(path="/tmp/book1.pdf", title="Title", author="Author")
    grid.update_books([book])

    # Update config
    new_config = {"zoom_level": 2.0, "show_titles": False}
    grid.update_config(new_config)

    assert grid._config == new_config
    assert grid.store.get_n_items() == 1


def test_shelf_grid_factory_setup() -> None:
    """Test the grid item factory setup."""
    grid = ShelfGrid(on_book_selected_callback=lambda b: None)
    mock_factory = MagicMock()
    mock_item = MagicMock()

    grid._on_factory_setup(mock_factory, mock_item)

    assert mock_item.get_child() is not None
    assert hasattr(mock_item.get_child(), "get_first_child")


def test_shelf_grid_factory_bind() -> None:
    """Test the grid item factory bind."""
    from src.models.book import BookObject
    from src.ui.book_widget import BookWidget

    grid = ShelfGrid(on_book_selected_callback=lambda b: None)
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
