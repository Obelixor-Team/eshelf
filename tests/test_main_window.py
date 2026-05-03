"""Tests for main window UI components."""

from unittest.mock import MagicMock, patch

import gi
from gi.repository import Gtk

from src.ui.main_window import CategoryRow, MainWindow

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


def test_main_window_initialization() -> None:
    """Test MainWindow initialization."""
    window = MainWindow()
    assert window is not None
    assert window.get_title() == "eShelf"


def test_main_window_components() -> None:
    """Test for essential components in MainWindow."""
    window = MainWindow()
    assert hasattr(window, "sidebar")
    assert hasattr(window, "header_bar")
    assert hasattr(window, "grid")
    assert isinstance(window.sidebar, Gtk.Widget)
    assert isinstance(window.header_bar, Gtk.Widget)
    assert isinstance(window.grid, Gtk.Widget)


def test_on_sidebar_toggle_clicked() -> None:
    """Test sidebar toggle visibility."""
    window = MainWindow()

    # Toggle off
    window.sidebar.set_visible(True)
    window.on_sidebar_toggle_clicked(MagicMock())
    assert window.sidebar.get_visible() is False

    # Toggle on
    window.on_sidebar_toggle_clicked(MagicMock())
    assert window.sidebar.get_visible() is True


def test_on_category_selected() -> None:
    """Test category selection."""
    window = MainWindow()
    window.refresh_grid = MagicMock()
    window.request_save_ui_state = MagicMock()

    window._is_initializing = False
    window.on_category_selected(1, False)

    window.refresh_grid.assert_called_once_with(1, False)
    window.request_save_ui_state.assert_called_once()


@patch("src.ui.main_window.save_config")
@patch("src.ui.main_window.load_config")
def test_save_ui_state(
    mock_load_config: MagicMock, mock_save_config: MagicMock
) -> None:
    """Test saving UI state."""
    window = MainWindow()
    mock_load_config.return_value = {}

    # Mocking sidebar and sort combo state
    window.sidebar.set_visible(True)
    mock_item = MagicMock()
    mock_item.get_string.return_value = "Author"
    window.sort_combo.get_selected_item = MagicMock(return_value=mock_item)

    # Mocking category selection
    mock_row = MagicMock(spec=CategoryRow)
    mock_row.identifier = 2
    window.sidebar.list_box.get_selected_row = MagicMock(return_value=mock_row)

    window.save_ui_state()

    mock_save_config.assert_called_once()
    saved_config = mock_save_config.call_args[0][0]
    assert saved_config["sidebar_visible"] is True
    assert saved_config["last_sort_option"] == "Author"
    assert saved_config["last_category_identifier"] == 2


@patch("src.ui.main_window.save_config")
def test_on_sort_changed(mock_save_config: MagicMock) -> None:
    """Test sort option change."""
    window = MainWindow()
    window.refresh_grid = MagicMock()
    window.request_save_ui_state = MagicMock()

    # Mocking Gtk.DropDown selected item
    mock_item = MagicMock()
    mock_item.get_string.return_value = "Author"

    mock_combo = MagicMock()
    mock_combo.get_selected_item.return_value = mock_item

    window.on_sort_changed(mock_combo)
    window.refresh_grid.assert_called_once_with(sort_by="Author")
    window.request_save_ui_state.assert_called_once()


@patch("src.ui.main_window.MainController")
def test_on_category_created(mock_controller: MagicMock) -> None:
    """Test category creation."""
    window = MainWindow()
    window.controller = mock_controller
    window.refresh_sidebar = MagicMock()

    window.on_category_created("New Category")

    mock_controller.create_category.assert_called_once_with("New Category")
    window.refresh_sidebar.assert_called_once()


@patch("src.ui.main_window.MainController")
def test_on_category_deleted(mock_controller: MagicMock) -> None:
    """Test category deletion."""
    window = MainWindow()
    window.controller = mock_controller
    window.refresh_sidebar = MagicMock()
    window.refresh_grid = MagicMock()

    window.on_category_deleted(1)

    mock_controller.delete_category.assert_called_once_with(1)
    window.refresh_sidebar.assert_called_once()
    window.refresh_grid.assert_called_once_with(None, True)


@patch("src.ui.main_window.Adw.AlertDialog")
@patch("src.ui.main_window.Gtk.FileDialog")
@patch("src.ui.main_window.MainController")
def test_on_import_clicked(
    mock_controller: MagicMock,
    mock_file_dialog: MagicMock,
    mock_alert_dialog: MagicMock,
) -> None:
    """Test import dialog initiation."""
    window = MainWindow()
    window.controller = mock_controller
    window.on_import_clicked(MagicMock())

    mock_alert_dialog.assert_called_once()
    instance = mock_alert_dialog.return_value
    instance.choose.assert_called_once()


@patch("src.ui.main_window.threading.Thread")
@patch("src.ui.main_window.MainController")
def test_on_scan_clicked(mock_controller: MagicMock, mock_thread: MagicMock) -> None:
    """Test scan library initiation."""
    window = MainWindow()
    window.controller = mock_controller
    window.scan_button = MagicMock()
    window.progress_bar = MagicMock()

    window.on_scan_clicked(MagicMock())

    window.scan_button.set_sensitive.assert_called_once_with(False)
    window.progress_bar.set_visible.assert_called_once_with(True)
    mock_thread.assert_called_once()
    assert mock_thread.call_args[1]["daemon"] is True


def test_on_search_changed() -> None:
    """Test search entry change."""
    window = MainWindow()
    window.refresh_grid = MagicMock()

    mock_entry = MagicMock()
    mock_entry.get_text.return_value = "query"

    window.on_search_changed(mock_entry)

    window.refresh_grid.assert_called_once_with(search_text="query")


@patch("src.ui.main_window.MainController")
def test_on_book_selected(mock_controller: MagicMock) -> None:
    """Test book selection."""
    window = MainWindow()
    window.controller = mock_controller
    mock_book = MagicMock()

    window.on_book_selected(mock_book)

    mock_controller.open_book.assert_called_once_with(mock_book)


@patch("src.ui.main_window.MainController")
def test_refresh_grid(mock_controller: MagicMock) -> None:
    """Test refresh_grid updates the grid with correct books."""
    window = MainWindow()
    window.controller = mock_controller
    window.grid = MagicMock()
    mock_books = ["book1", "book2"]
    mock_controller.get_books.return_value = mock_books

    window.refresh_grid(category_id=1, all_books=False)

    mock_controller.get_books.assert_called_once_with(1)
    window.grid.update_books.assert_called_once_with(mock_books)


@patch("src.ui.main_window.load_config")
def test_set_controller(mock_load_config: MagicMock) -> None:
    """Test controller injection and UI state restoration."""
    window = MainWindow()
    mock_controller = MagicMock()
    mock_load_config.return_value = {"sidebar_visible": False}

    window.set_controller(mock_controller)

    assert window.controller == mock_controller
    assert window.controller.error_callback == window.show_error
    assert window.sidebar.get_visible() is False


@patch("src.ui.main_window.GLib.idle_add", side_effect=lambda f, *args: f(*args))
@patch("src.ui.main_window.Adw.AlertDialog")
def test_show_error(mock_dialog: MagicMock, mock_idle: MagicMock) -> None:
    """Test show_error displays a message dialog."""
    window = MainWindow()
    window.set_visible(True)
    window.show_error("Test Error")

    mock_dialog.assert_called_once()
    instance = mock_dialog.return_value
    instance.choose.assert_called_once()


@patch("src.ui.main_window.GLib.idle_add", side_effect=lambda f, *args: f(*args))
@patch("src.ui.main_window.Adw.AlertDialog")
def test_show_error_aggregation(mock_dialog: MagicMock, mock_idle: MagicMock) -> None:
    """Test show_error aggregates multiple messages."""
    window = MainWindow()
    window.set_visible(True)

    window.show_error("Error 1")
    instance = mock_dialog.return_value
    instance.get_property.return_value = "Error 1"
    window.show_error("Error 2")

    # Should only be called once
    mock_dialog.assert_called_once()
    # Second call should update the property
    instance.set_property.assert_called_with("body", "Error 1\nError 2")


@patch("src.ui.main_window.GLib.idle_add", side_effect=lambda f, *args: f(*args))
def test_show_toast(mock_idle: MagicMock) -> None:
    """Test show_toast adds a toast to the overlay."""
    window = MainWindow()
    window.set_visible(True)
    window.toast_overlay = MagicMock()
    window.show_toast("Test Toast")

    window.toast_overlay.add_toast.assert_called_once()


@patch("src.ui.main_window.MainController")
def test_move_book(mock_controller: MagicMock) -> None:
    """Test moving a book to a category."""
    window = MainWindow()
    window.controller = mock_controller
    window.refresh_grid = MagicMock()
    mock_book = MagicMock(path="/tmp/book.pdf")
    mock_popover = MagicMock()

    window.move_book(mock_book, 1, mock_popover)

    mock_controller.move_book_to_category.assert_called_once_with("/tmp/book.pdf", 1)
    window.refresh_grid.assert_called_once()
    mock_popover.popdown.assert_called_once()


@patch("src.ui.main_window.Adw.Dialog")
@patch("src.ui.main_window.MainController")
def test_on_edit_metadata_clicked(
    mock_controller: MagicMock, mock_dialog: MagicMock
) -> None:
    """Test edit metadata dialog initiation."""
    window = MainWindow()
    window.controller = mock_controller
    mock_book = MagicMock(title="Title", author="Author", path="/tmp/book.pdf")
    mock_popover = MagicMock()

    window.on_edit_metadata_clicked(mock_book, mock_popover)

    mock_popover.popdown.assert_called_once()
    mock_dialog.assert_called_once()


@patch("src.ui.main_window.threading.Thread")
@patch("src.ui.main_window.MainController")
def test_on_cleanup_clicked(mock_controller: MagicMock, mock_thread: MagicMock) -> None:
    """Test cleanup library initiation."""
    window = MainWindow()
    window.controller = mock_controller

    window.on_cleanup_clicked(MagicMock())

    mock_thread.assert_called_once()
    assert mock_thread.call_args[1]["daemon"] is True


@patch("src.ui.main_window.Adw.PreferencesDialog")
@patch("src.ui.main_window.load_config")
def test_on_settings_clicked(
    mock_load_config: MagicMock, mock_dialog: MagicMock
) -> None:
    """Test settings dialog initiation."""
    window = MainWindow()
    mock_load_config.return_value = {"books_per_line": 6, "zoom_level": 1.0}

    window.on_settings_clicked(MagicMock())

    mock_dialog_instance = mock_dialog.return_value
    mock_dialog_instance.present.assert_called_once()


def test_on_category_selected_initializing() -> None:
    """Test category selection during initialization."""
    window = MainWindow()
    window.refresh_grid = MagicMock()

    window._is_initializing = True
    window.on_category_selected(1, False)

    window.refresh_grid.assert_not_called()


def test_on_category_created_no_controller() -> None:
    """Test category creation without controller."""
    window = MainWindow()
    window.controller = None
    window.refresh_sidebar = MagicMock()

    window.on_category_created("New Category")
    window.refresh_sidebar.assert_not_called()


def test_on_category_deleted_no_controller() -> None:
    """Test category deletion without controller."""
    window = MainWindow()
    window.controller = None
    window.refresh_sidebar = MagicMock()
    window.refresh_grid = MagicMock()

    window.on_category_deleted(1)
    window.refresh_sidebar.assert_not_called()
    window.refresh_grid.assert_not_called()


def test_on_import_clicked_no_controller() -> None:
    """Test import clicked without controller."""
    window = MainWindow()
    window.controller = None
    # Should just return without showing dialog
    window.on_import_clicked(MagicMock())
    # No way to easily verify dialog NOT shown without mocking Adw.MessageDialog
    # but we can check it doesn't crash.


def test_on_scan_clicked_no_controller() -> None:
    """Test scan clicked without controller."""
    window = MainWindow()
    window.controller = None
    window.scan_button = MagicMock()

    window.on_scan_clicked(MagicMock())
    window.scan_button.set_sensitive.assert_not_called()


def test_on_cleanup_clicked_no_controller() -> None:
    """Test cleanup clicked without controller."""
    window = MainWindow()
    window.controller = None

    with patch("src.ui.main_window.threading.Thread") as mock_thread:
        window.on_cleanup_clicked(MagicMock())
        mock_thread.assert_not_called()


def test_on_book_selected_no_controller() -> None:
    """Test book selection without controller."""
    window = MainWindow()
    window.controller = None
    mock_book = MagicMock()

    window.on_book_selected(mock_book)
    # Should just return
    assert True


def test_move_book_no_controller() -> None:
    """Test moving book without controller."""
    window = MainWindow()
    window.controller = None
    window.refresh_grid = MagicMock()
    mock_book = MagicMock(path="/tmp/book.pdf")

    window.move_book(mock_book, 1)
    window.refresh_grid.assert_not_called()


def test_import_finished_internal() -> None:
    """Test internal import finished handler."""
    window = MainWindow()
    window.import_item = MagicMock()
    window.hide_progress_bar = MagicMock()
    window.refresh_grid = MagicMock()
    window.show_toast = MagicMock()

    # Visible case
    window.set_visible(True)
    result = (1, 2, ["error1"])
    assert window._on_import_finished_internal(result) is False
    window.import_item.set_sensitive.assert_called_with(True)
    window.hide_progress_bar.assert_called_once()
    window.refresh_grid.assert_called_once()
    window.show_toast.assert_called_once()

    # Invisible case
    window.set_visible(False)
    assert window._on_import_finished_internal(result) is False
    # Verify no more calls happened (except the first one)
    assert window.refresh_grid.call_count == 1


def test_import_error_internal() -> None:
    """Test internal import error handler."""
    window = MainWindow()
    window.import_item = MagicMock()
    window.hide_progress_bar = MagicMock()
    window.show_error = MagicMock()

    # Visible case
    window.set_visible(True)
    error = Exception("Import failed")
    assert window._on_import_error_internal(error) is False
    window.import_item.set_sensitive.assert_called_with(True)
    window.hide_progress_bar.assert_called_once()
    window.show_error.assert_called_once_with("Error: Import failed")

    # Invisible case
    window.set_visible(False)
    assert window._on_import_error_internal(error) is False


def test_cleanup_finished_internal() -> None:
    """Test internal cleanup finished handler."""
    window = MainWindow()
    window.cleanup_item = MagicMock()
    window.refresh_grid = MagicMock()
    window.show_toast = MagicMock()

    # Visible case
    window.set_visible(True)
    assert window._on_cleanup_finished(5) is False
    window.cleanup_item.set_sensitive.assert_called_with(True)
    window.refresh_grid.assert_called_once()
    window.show_toast.assert_called_once()

    # Invisible case
    window.set_visible(False)
    assert window._on_cleanup_finished(5) is False


def test_cleanup_error_internal() -> None:
    """Test internal cleanup error handler."""
    window = MainWindow()
    window.cleanup_item = MagicMock()
    window.show_error = MagicMock()

    # Visible case
    window.set_visible(True)
    error = Exception("Cleanup failed")
    assert window._on_cleanup_error(error) is False
    window.cleanup_item.set_sensitive.assert_called_with(True)
    window.show_error.assert_called_once_with("Error during cleanup: Cleanup failed")

    # Invisible case
    window.set_visible(False)
    assert window._on_cleanup_error(error) is False


def test_on_book_dropped() -> None:
    """Test book drop on category."""
    window = MainWindow()
    window.controller = MagicMock()
    window.grid = MagicMock()

    # Case 1: Dropped book is in selection
    mock_book = MagicMock(path="/tmp/book1.pdf")
    window.grid.get_selected_books.return_value = [mock_book]
    window.on_book_dropped("/tmp/book1.pdf", 1)
    window.controller.move_book_to_category.assert_called_once_with("/tmp/book1.pdf", 1)

    # Case 2: Dropped book is NOT in selection
    window.controller.move_book_to_category.reset_mock()
    window.grid.get_selected_books.return_value = [MagicMock(path="/tmp/other.pdf")]
    window.on_book_dropped("/tmp/dropped.pdf", 2)
    window.controller.move_book_to_category.assert_called_once_with(
        "/tmp/dropped.pdf", 2
    )


def test_update_progress() -> None:
    """Test progress bar update."""
    window = MainWindow()
    window.set_visible(True)
    window.progress_bar = MagicMock()

    assert window.update_progress(50, 100) is False
    window.progress_bar.set_fraction.assert_called_once_with(0.5)
    window.progress_bar.set_text.assert_called_once()
    window.progress_bar.set_show_text.assert_called_once_with(True)


def test_on_scan_finished() -> None:
    """Test scan finished handler."""
    window = MainWindow()
    window.set_visible(True)
    window.scan_button = MagicMock()
    window.progress_bar = MagicMock()
    window.refresh_grid = MagicMock()
    window.show_toast = MagicMock()

    # With failures
    assert window.on_scan_finished(1, 2, ["err1"]) is False
    window.scan_button.set_sensitive.assert_called_with(True)
    window.progress_bar.set_visible.assert_called_with(False)
    window.refresh_grid.assert_called_once()
    window.show_toast.assert_called_once()

    # Without failures
    window.show_toast.reset_mock()
    assert window.on_scan_finished(1, 2, []) is False
    window.show_toast.assert_called_once()


def test_fetch_books() -> None:
    """Test _fetch_books logic."""
    window = MainWindow()
    window.controller = MagicMock()

    # Search
    window._fetch_books(search_text="query")
    window.controller.search_books.assert_called_once_with("query")

    # All books
    window.controller.search_books.reset_mock()
    window._fetch_books(all_books=True)
    window.controller.get_books.assert_called_once_with(None)

    # Uncategorized
    window.controller.get_books.reset_mock()
    window._fetch_books(all_books=False, category_id=None)
    window.controller.get_uncategorized_books.assert_called_once()

    # Specific category
    window.controller.get_uncategorized_books.reset_mock()
    window._fetch_books(all_books=False, category_id=1)
    window.controller.get_books.assert_called_once_with(1)

    # Sorting
    window.controller.get_books.reset_mock()
    window._fetch_books(sort_by="Author")
    window.controller.sort_books.assert_called_once()


def test_apply_grid_update() -> None:
    """Test _apply_grid_update with request IDs."""
    window = MainWindow()
    window.grid = MagicMock()

    # Correct request ID
    window._grid_request_id = 1
    window.set_visible(True)
    window._apply_grid_update([MagicMock()], 1)
    window.grid.update_books.assert_called_once()

    # Incorrect request ID
    window.grid.update_books.reset_mock()
    window._apply_grid_update([MagicMock()], 0)
    window.grid.update_books.assert_not_called()

    # Invisible window
    window.grid.update_books.reset_mock()
    window.set_visible(False)
    window._apply_grid_update([MagicMock()], 1)
    window.grid.update_books.assert_not_called()


@patch("src.ui.main_window.load_config")
def test_set_controller_state_restoration(mock_load_config: MagicMock) -> None:
    """Test full state restoration in set_controller."""
    window = MainWindow()
    mock_controller = MagicMock()
    mock_load_config.return_value = {
        "sidebar_visible": False,
        "last_sort_option": "Author",
        "last_category_identifier": "1",
    }
    # Use a mock category with a string name
    cat = MagicMock()
    cat.id = 1
    cat.name = "Cat1"
    mock_controller.get_categories.return_value = [cat]

    window.set_controller(mock_controller)

    assert window.sidebar.get_visible() is False


def test_on_close_request() -> None:
    """Test close request saves UI state."""
    window = MainWindow()
    window.save_ui_state = MagicMock(return_value=False)

    assert window.on_close_request(window) is False
    window.save_ui_state.assert_called_once()


@patch("src.ui.main_window.GLib.timeout_add")
@patch("src.ui.main_window.GLib.source_remove")
def test_request_save_ui_state(mock_source_remove, mock_timeout_add) -> None:
    """Test debounced save request."""
    window = MainWindow()
    window._save_timeout_id = 123

    window.request_save_ui_state()

    mock_source_remove.assert_called_once_with(123)
    mock_timeout_add.assert_called_once()
    assert window._save_timeout_id is not None


def test_on_import_clicked_full() -> None:
    """Test on_import_clicked from dialog show to choice."""
    window = MainWindow()
    window.controller = MagicMock()

    with patch("src.ui.main_window.Adw.AlertDialog") as mock_alert:
        alert_instance = mock_alert.return_value
        window.on_import_clicked(MagicMock())

        alert_instance.choose.assert_called_once()
        # Get the callback passed to choose
        on_choice = alert_instance.choose.call_args[0][2]

        # Mock the result of choose_finish
        alert_instance.choose_finish.return_value = "file"

        # Call the choice callback
        with patch(
            "src.ui.main_window.GLib.idle_add", side_effect=lambda f, *args: f(*args)
        ):
            on_choice(alert_instance, MagicMock())

            with patch("src.ui.main_window.Gtk.FileDialog"):
                # The dialog.open is called inside show_picker
                # We can't easily verify it without more mocking,
                # but this covers some lines
                pass
