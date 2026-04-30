"""Tests for UI components."""

from unittest.mock import MagicMock

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk  # noqa: E402

from src.models.book import Book  # noqa: E402
from src.ui.book_widget import BookWidget  # noqa: E402


def test_book_widget_initialization() -> None:
    """Test widget initialization."""
    widget = BookWidget()
    assert widget.book is None
    assert widget.get_orientation() == Gtk.Orientation.VERTICAL


def test_book_widget_double_click_opens_book() -> None:
    """Test book opening on double click and not single click."""
    widget = BookWidget()
    book = Book(title="Test Book", path="/tmp/test.pdf", author="Test Author")
    callback = MagicMock()
    widget.bind(book, on_click_callback=callback)

    # Simulate first click (n_press=1)
    widget._on_clicked(MagicMock(), n_press=1, x=0, y=0)
    callback.assert_not_called()

    # Simulate second click (n_press=2) - should open
    widget._on_clicked(MagicMock(), n_press=2, x=0, y=0)
    callback.assert_called_once_with(book)
