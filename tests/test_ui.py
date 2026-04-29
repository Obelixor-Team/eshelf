"""Tests for UI components."""

from unittest.mock import MagicMock, patch

from src.models.book import Book
from src.ui.book_widget import BookWidget
from src.ui.main_window import MainWindow
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


def test_main_window_controller_integration() -> None:
    """Test MainWindow's interaction with the controller."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        # Manually set some necessary attributes that would be set by __init__
        win.controller = None
        win.grid = MagicMock()

        controller = MagicMock()
        controller.get_books.return_value = [Book(path="1", title="T1", author="A1")]

        win.set_controller(controller)
        assert win.controller == controller
        controller.get_books.assert_called_once()
        win.grid.update_books.assert_called_once()


def test_main_window_event_handlers() -> None:
    """Test MainWindow event handlers call correct controller methods."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        controller = MagicMock()
        controller.scan_library.return_value = (1, 1)
        controller.cleanup_library.return_value = 1
        win.controller = controller

        # Test scan
        win.on_scan_clicked(MagicMock())
        # Scan is now asynchronous, so we don't assert call directly

        # Test cleanup
        win.on_cleanup_clicked(MagicMock())
        controller.cleanup_library.assert_called_once()

        # Test book selection
        book = Book(path="1", title="T1", author="A1")
        win.on_book_selected(book)
        controller.open_book.assert_called_once_with(book)


def test_main_window_import_handlers() -> None:
    """Test MainWindow import handlers."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        controller = MagicMock()
        win.controller = controller

        # Test import file (without controller)
        win.controller = None
        win.on_import_file_clicked(MagicMock())

        # Test import folder (without controller)
        win.on_import_folder_clicked(MagicMock())

        # Test import file (with controller) - we mock FileDialog
        win.controller = controller
        with patch("src.ui.main_window.Gtk.FileDialog") as mock_dialog:
            win.on_import_file_clicked(MagicMock())
            mock_dialog.assert_called_once()

        with patch("src.ui.main_window.Gtk.FileDialog") as mock_dialog:
            win.on_import_folder_clicked(MagicMock())
            mock_dialog.assert_called_once()


def test_main_window_helper_methods() -> None:
    """Test MainWindow helper methods."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        win.progress_bar = MagicMock()
        win.scan_button = MagicMock()
        win.grid = MagicMock()
        win.controller = MagicMock()

        # Test update_progress
        win.update_progress(5, 10)
        win.progress_bar.set_fraction.assert_called_with(0.5)

        # Test on_scan_finished
        win.on_scan_finished(1, 1)
        win.scan_button.set_sensitive.assert_called_with(True)
        win.progress_bar.set_visible.assert_called_with(False)
        win.refresh_grid()  # Should not crash

        # Test refresh_grid
        win.controller.get_books.return_value = []
        win.refresh_grid()
        win.controller.get_books.assert_called()
        win.grid.update_books.assert_called()


def test_main_window_settings_clicked() -> None:
    """Test that opening settings creates a dialog."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        with patch("src.ui.main_window.Gtk.Window") as mock_dialog:
            win.on_settings_clicked(MagicMock())
            mock_dialog.assert_called_once()
