"""Tests for UI components."""

from unittest.mock import MagicMock

from src.models.book import Book
from src.ui.book_widget import BookWidget
from src.ui.shelf_grid import ShelfGrid


def test_book_widget_initialization() -> None:
    """Test that BookWidget initializes with correct book."""
    book = Book(path="/path/to/book.pdf", title="Test Book", author="Author")
    callback = MagicMock()
    widget = BookWidget(book, callback)
    assert widget.book == book


def test_shelf_grid_update_books() -> None:
    """Test that ShelfGrid correctly adds book widgets."""
    callback = MagicMock()
    grid = ShelfGrid(callback)
    books = [
        Book(path="1", title="T1", author="A1"),
        Book(path="2", title="T2", author="A2"),
    ]
    grid.update_books(books)
    # FlowBox doesn't have a simple 'get_children' but we can check first child
    assert grid.get_first_child() is not None
