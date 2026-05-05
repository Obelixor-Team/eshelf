"""Tests for UI components."""

from unittest.mock import MagicMock, patch

import gi

from src.models.book import Book
from src.ui.book_widget import BookWidget

gi.require_version("Gtk", "4.0")


def test_book_widget_bind_no_cover():
    """Test binding with no cover path."""
    widget = BookWidget()
    book = Book(title="No Cover", path="/tmp/test.pdf", author="Author")
    widget.bind(book, on_click_callback=MagicMock())
    assert widget.image.get_paintable() is None


def test_book_widget_bind_missing_cover_file():
    """Test binding with a non-existent cover path (should not log error)."""
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
        widget.bind(book, on_click_callback=mock_callback)
        # Verify no error is logged when file is missing
        mock_logger.error.assert_not_called()
    assert widget.image.get_paintable() is None


def test_book_widget_bind_cover_loading_error():
    """Test error handling when loading a cover image fails."""
    widget = BookWidget()
    book = Book(
        title="Error Book",
        path="/tmp/error.pdf",
        author="Error Author",
        cover_path="/tmp/existing.jpg",
    )
    mock_callback = MagicMock()

    # Patch the logger to check if error is called
    with patch("src.ui.book_widget.BookWidget.logger") as mock_logger:
        with patch("src.ui.book_widget.Path") as mock_path:
            mock_path.return_value.exists.return_value = True
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
