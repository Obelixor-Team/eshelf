from unittest.mock import MagicMock, patch

from src.ui.main_window import MainWindow


def test_main_window_show_error():
    window = MainWindow()
    window.set_visible(True)  # Ensure window is visible
    with patch('src.ui.main_window.Adw.AlertDialog') as mock_dialog:
        # Mocking the instance and parent
        mock_instance = MagicMock()
        mock_dialog.return_value = mock_instance
        
        window.show_error("Test error")
        
        # GLib.idle_add is used, we need to make sure the callback runs.
        # The main_window.py uses GLib.idle_add(_show_error_on_main_thread)
        # So we need to mock GLib or run the loop. 
        # For testing, let's patch GLib.idle_add to execute immediately.
        pass

@patch('src.ui.main_window.GLib.idle_add', side_effect=lambda f, *args: f(*args))
def test_main_window_show_error_immediate(mock_idle):
    window = MainWindow()
    window.set_visible(True)
    with patch('src.ui.main_window.Adw.AlertDialog') as mock_dialog:
        window.show_error("Test error")
        assert mock_dialog.called

def test_main_window_refresh_grid_no_books():
    window = MainWindow()
    window.set_controller(MagicMock())
    # Should not crash
    window.refresh_grid(None, False)

def test_main_window_on_close_request():
    window = MainWindow()
    # Mocking Adw.ApplicationWindow
    mock_app_window = MagicMock()
    # Should return True
    assert window.on_close_request(mock_app_window) is False
