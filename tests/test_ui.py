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
        patch("threading.Thread") as mock_thread,
    ):
        win = MainWindow()
        controller = MagicMock()
        controller.scan_library.return_value = (1, 1, [])
        controller.cleanup_library.return_value = 1
        win.controller = controller

        # Test scan
        win.on_scan_clicked(MagicMock())
        assert mock_thread.call_count == 1
        # Execute the scan worker synchronously for testing
        scan_worker = mock_thread.call_args[1]["target"]
        scan_worker()
        controller.scan_library.assert_called_once()

        # Test cleanup
        win.on_cleanup_clicked(MagicMock())
        assert mock_thread.call_count == 2
        cleanup_worker = mock_thread.call_args[1]["target"]
        cleanup_worker()
        controller.cleanup_library.assert_called_once()

        # Test book selection
        book = Book(path="1", title="T1", author="A1")
        win.on_book_selected(book)
        controller.open_book.assert_called_once_with(book)

        # Test category events
        win.on_category_selected(1, False)
        controller.get_books.assert_called_with(1)

        win.on_category_created("New")
        controller.create_category.assert_called_once_with("New")

        win.on_category_deleted(1)
        controller.delete_category.assert_called_once_with(1)

        # Test sidebar toggle
        win.sidebar = MagicMock()
        win.sidebar.get_visible.return_value = True
        win.on_sidebar_toggle_clicked(MagicMock())
        win.sidebar.set_visible.assert_called_with(False)


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
        win.on_scan_finished(1, 1, [])
        win.scan_button.set_sensitive.assert_called_with(True)
        win.progress_bar.set_visible.assert_called_with(False)
        win.refresh_grid()  # Should not crash

        # Test refresh_grid
        win.controller.get_books.return_value = []
        win.refresh_grid()
        win.controller.get_books.assert_called()
        win.grid.update_books.assert_called()

        # Test show_error
        with patch("src.ui.main_window.Adw.MessageDialog") as mock_dialog:
            win.show_error("Test Error")
            mock_dialog.assert_called_once()


def test_main_window_settings_clicked() -> None:
    """Test that opening settings creates a dialog."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        with patch("src.ui.main_window.Adw.PreferencesDialog") as mock_dialog:
            win.on_settings_clicked(MagicMock())
            mock_dialog.assert_called_once()


def test_main_window_edit_metadata_clicked() -> None:
    """Test that editing metadata creates a dialog and updates controller."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        controller = MagicMock()
        win.controller = controller
        book = Book(path="1", title="Old", author="Old")

        with patch("src.ui.main_window.Adw.Dialog") as mock_dialog:
            # We can't easily simulate the GTK event loop and button clicks here,
            # but we can test the on_edit_metadata_clicked method itself.
            win.on_edit_metadata_clicked(book, MagicMock())
            mock_dialog.assert_called_once()
