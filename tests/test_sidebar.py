"""Tests for Sidebar UI component."""

from unittest.mock import MagicMock

import gi

from src.models.category import Category
from src.ui.sidebar import CategoryRow, Sidebar

gi.require_version("Gtk", "4.0")


def test_sidebar_initialization() -> None:
    """Test sidebar initialization."""
    on_selected = MagicMock()
    on_created = MagicMock()
    on_deleted = MagicMock()
    sidebar = Sidebar(on_selected, on_created, on_deleted)

    assert sidebar is not None


def test_update_categories() -> None:
    """Test updating the categories list."""
    on_selected = MagicMock()
    on_created = MagicMock()
    on_deleted = MagicMock()
    sidebar = Sidebar(on_selected, on_created, on_deleted)

    categories = [Category(id=1, name="Sci-Fi")]
    sidebar.update_categories(categories)

    # Should have "All Books", "Uncategorized", and "Sci-Fi"
    row = sidebar.list_box.get_first_child()
    assert isinstance(row, CategoryRow)
    assert row.identifier == "all"

    row = row.get_next_sibling()
    assert isinstance(row, CategoryRow)
    assert row.identifier == "uncategorized"

    row = row.get_next_sibling()
    assert isinstance(row, CategoryRow)
    assert row.identifier == "1"


def test_on_add_clicked() -> None:
    """Test clicking the add button."""
    on_selected = MagicMock()
    on_created = MagicMock()
    on_deleted = MagicMock()
    sidebar = Sidebar(on_selected, on_created, on_deleted)

    sidebar.category_entry.set_text("Horror")
    sidebar.on_add_clicked(MagicMock())

    on_created.assert_called_once_with("Horror")
    assert sidebar.category_entry.get_text() == ""
