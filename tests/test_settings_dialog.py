"""Tests for the SettingsDialog component."""

import gi
from unittest.mock import MagicMock, patch

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk
from src.ui.dialogs.settings_dialog import SettingsDialog

@patch("src.ui.dialogs.settings_dialog.load_config")
@patch("src.ui.dialogs.settings_dialog.save_config")
def test_settings_dialog_save(mock_save: MagicMock, mock_load: MagicMock) -> None:
    """Test saving settings from the dialog."""
    mock_load.return_value = {
        "books_per_line": 6,
        "zoom_level": 1.0,
        "library_dirs": [],
        "cache_dir": "/tmp",
        "show_titles": True,
        "appearance": "System"
    }
    
    parent = Gtk.Window()
    controller = MagicMock()
    on_save_cb = MagicMock()
    
    dialog = SettingsDialog(parent, controller, MagicMock(), on_save_cb=on_save_cb)
    
    # Simulate changing a spin button value
    dialog.books_per_line_spin.set_value(5)
    
    # Trigger save
    dialog._on_save(MagicMock())
    
    # Verify save_config was called with updated value
    saved_config = mock_save.call_args[0][0]
    assert saved_config["books_per_line"] == 5
    on_save_cb.assert_called_once()
