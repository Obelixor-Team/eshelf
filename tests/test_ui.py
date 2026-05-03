"""Tests for UI components."""

from unittest.mock import MagicMock, patch

import gi
from gi.repository import Gtk  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")

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


def test_book_widget_right_click():
    """Test right-click handling in BookWidget."""
    widget = BookWidget()
    book = Book(title="Test Book", path="/tmp/test.pdf", author="Test Author")
    callback = MagicMock()
    widget.bind(book, on_click_callback=MagicMock(), on_right_click_callback=callback)

    widget.on_right_clicked(MagicMock(), n_press=1, x=0, y=0)
    callback.assert_called_once_with(widget, book)


def test_book_widget_bind_with_cover_error():
    """Test binding with a non-existent cover path."""
    widget = BookWidget()
    book = Book(
        title="Error Book",
        path="/tmp/error.pdf",
        author="Error Author",
        cover_path="/nonexistent/path.jpg",
    )
    mock_callback = MagicMock()

    # Patch the logger
    with patch("src.ui.book_widget.BookWidget.logger") as mock_logger:
        # Mock Gdk.Texture.new_from_filename to raise an exception
        with patch(
            "gi.repository.Gdk.Texture.new_from_filename",
            side_effect=Exception("Simulated error"),
        ):
            widget.bind(book, on_click_callback=mock_callback)
            mock_logger.error.assert_called_once()
            assert widget.image.get_paintable() is None


def test_book_widget_bind_no_cover():
    """Test binding a book with no cover path."""
    widget = BookWidget()
    book = Book(title="No Cover Book", path=None, author="No Cover Author")
    mock_callback = MagicMock()
    widget.bind(book, on_click_callback=mock_callback)
    assert widget.image.get_paintable() is None


def test_book_widget_drag_prepare_no_book():
    """Test drag prepare when no book is bound."""
    widget = BookWidget()
    # Ensure drag prepare returns None when no book is bound
    assert widget._on_drag_prepare(MagicMock(), 0, 0) is None


def test_book_widget_drag_prepare_with_book():
    """Test drag prepare when a book is bound."""
    widget = BookWidget()
    book = Book(
        title="Draggable Book",
        path="/tmp/drag.pdf",
        author="Drag Author",
        cover_path="/tmp/cover.jpg",
    )

    mock_source = MagicMock()
    # Mock Gdk.Texture.new_from_filename and Gtk.Picture.set_paintable/get_paintable
    with patch("gi.repository.Gdk.Texture.new_from_filename") as mock_texture_new:
        mock_texture = MagicMock()
        mock_texture_new.return_value = mock_texture

        with patch.object(widget.image, "set_paintable"):
            with patch.object(widget.image, "get_paintable", return_value=mock_texture):
                widget.bind(book, on_click_callback=MagicMock())

                # Call _on_drag_prepare. This should set the icon.
                widget._on_drag_prepare(mock_source, 10, 20)

                # Check if set_icon was called with the correct arguments
                mock_source.set_icon.assert_called_once_with(mock_texture, 10, 20)


# Add test for image loading error specifically
def test_book_widget_bind_cover_loading_error():
    """Test error handling when loading a cover image fails."""
    widget = BookWidget()
    book = Book(
        title="Error Book",
        path="/tmp/error.pdf",
        author="Error Author",
        cover_path="/nonexistent/path.jpg",
    )
    mock_callback = MagicMock()

    # Patch the logger to check if error is called
    with patch("src.ui.book_widget.BookWidget.logger") as mock_logger:
        # Mock Gdk.Texture.new_from_filename to raise an exception
        with patch(
            "gi.repository.Gdk.Texture.new_from_filename",
            side_effect=Exception("Simulated error"),
        ):
            widget.bind(book, on_click_callback=mock_callback)
            # Ensure the error log was called
            mock_logger.error.assert_called_once()
    # Ensure image is set to None on error
    assert widget.image.get_paintable() is None
