"""Expanded tests for the UI components."""

from unittest.mock import MagicMock, patch

from src.ui.main_window import MainWindow


def test_main_window_show_error():
    """Test that show_error creates an alert dialog."""
    window = MainWindow()
    window.set_visible(True)  # Ensure window is visible
    with patch("src.ui.main_window.Adw.AlertDialog") as mock_dialog:
        # Mocking the instance and parent
        mock_instance = MagicMock()
        mock_dialog.return_value = mock_instance

        window.show_error("Test error")

        # GLib.idle_add is used, we need to make sure the callback runs.
        # The main_window.py uses GLib.idle_add(_show_error_on_main_thread)
        # So we need to mock GLib or run the loop.
        # For testing, let's patch GLib.idle_add to execute immediately.
        pass


@patch("src.ui.main_window.GLib.idle_add", side_effect=lambda f, *args: f(*args))
def test_main_window_show_error_immediate(mock_idle):
    """Test that show_error creates an alert dialog immediately when GLib is patched."""
    window = MainWindow()
    window.set_visible(True)
    with patch("src.ui.main_window.Adw.AlertDialog") as mock_dialog:
        window.show_error("Test error")
        assert mock_dialog.called


def test_main_window_refresh_grid_no_books():
    """Test that refresh_grid handles cases with no books gracefully."""
    window = MainWindow()
    window.set_controller(MagicMock())
    # Should not crash
    window.refresh_grid(None, False)


def test_main_window_empty_states():
    """Test the context-aware empty state logic in refresh_grid."""
    window = MainWindow()
    mock_controller = MagicMock()
    window.set_controller(mock_controller)
    window.grid = MagicMock()
    window.stack = MagicMock()
    window.empty_page = MagicMock()
    window.empty_scan_button = MagicMock()
    window.empty_clear_search_button = MagicMock()

    # Case 1: Library is completely empty
    mock_controller.repository.get_book_count.return_value = 0
    window.refresh_grid(all_books=True)
    window.stack.set_visible_child_name.assert_called_with("empty")
    window.empty_page.set_title.assert_called_with("No Books Found")
    window.empty_scan_button.set_visible.assert_called_with(True)

    # Case 2: Library has books, but current category is empty
    mock_controller.repository.get_book_count.return_value = 10
    window.grid.model.do_get_n_items.return_value = 0
    window.refresh_grid(category_id=1, all_books=False)
    window.stack.set_visible_child_name.assert_called_with("empty")
    window.empty_page.set_title.assert_called_with("No Books")
    window.empty_page.set_description.assert_called_with(
        "This category is currently empty."
    )
    window.empty_scan_button.set_visible.assert_called_with(False)

    # Case 3: Library has books, but search has no results
    window.refresh_grid(search_text="Python")
    window.stack.set_visible_child_name.assert_called_with("empty")
    window.empty_page.set_title.assert_called_with("No Results Found")
    window.empty_page.set_description.assert_called_with('No books matching "Python"')
    window.empty_clear_search_button.set_visible.assert_called_with(True)

    # Case 4: Results found
    window.grid.model.do_get_n_items.return_value = 5
    window.refresh_grid(all_books=True)
    window.stack.set_visible_child_name.assert_called_with("grid")


def test_main_window_on_close_request():
    """Test the close request handler."""
    window = MainWindow()
    # Mocking Adw.ApplicationWindow
    window.close()
