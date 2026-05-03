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


def test_select_category_invalid():
    """Test selecting a category that doesn't exist."""
    on_selected = MagicMock()
    on_created = MagicMock()
    on_deleted = MagicMock()
    sidebar = Sidebar(on_selected, on_created, on_deleted)

    # Select a category that doesn't exist
    sidebar.select_category(999, False)
    # Should not crash
    assert True


def test_on_delete_clicked():
    """Test clicking the delete button on a category."""
    on_selected = MagicMock()
    on_created = MagicMock()
    on_deleted = MagicMock()
    sidebar = Sidebar(on_selected, on_created, on_deleted)

    sidebar.on_delete_clicked(MagicMock(), 1)
    on_deleted.assert_called_once_with(1)


def test_on_book_drop() -> None:
    """Test book drop on a category row."""
    on_selected = MagicMock()
    on_created = MagicMock()
    on_deleted = MagicMock()
    on_dropped = MagicMock()
    sidebar = Sidebar(on_selected, on_created, on_deleted, on_book_dropped=on_dropped)

    # Case 1: Drop on custom category
    assert sidebar.on_book_drop(MagicMock(), "/tmp/book.pdf", 0, 0, "1") is True
    on_dropped.assert_called_once_with("/tmp/book.pdf", 1)

    # Case 2: Drop on "all"
    on_dropped.reset_mock()
    assert sidebar.on_book_drop(MagicMock(), "/tmp/book.pdf", 0, 0, "all") is False
    on_dropped.assert_not_called()

    # Case 3: Drop on "uncategorized"
    on_dropped.reset_mock()
    assert (
        sidebar.on_book_drop(MagicMock(), "/tmp/book.pdf", 0, 0, "uncategorized")
        is True
    )
    on_dropped.assert_called_once_with("/tmp/book.pdf", None)


def test_on_row_selected() -> None:
    """Test row selection handling."""
    on_selected = MagicMock()
    on_created = MagicMock()
    on_deleted = MagicMock()
    sidebar = Sidebar(on_selected, on_created, on_deleted)

    # Select "all"
    sidebar.on_row_selected(MagicMock(), CategoryRow("all"))
    on_selected.assert_called_once_with(None, True)

    # Select "uncategorized"
    on_selected.reset_mock()
    sidebar.on_row_selected(MagicMock(), CategoryRow("uncategorized"))
    on_selected.assert_called_once_with(None, False)

    # Select custom category
    on_selected.reset_mock()
    sidebar.on_row_selected(MagicMock(), CategoryRow("123"))
    on_selected.assert_called_once_with(123, False)
