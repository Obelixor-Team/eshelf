"""Integration test to verify the grid layout behavior."""

import sys
from unittest.mock import MagicMock

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib  # noqa: E402

from src.models.book import Book  # noqa: E402
from src.ui.shelf_grid import ShelfGrid  # noqa: E402


# Mock ebooklib and other potentially missing dependencies
def setup_mocks() -> None:
    """Mock ebooklib and other potentially missing dependencies."""
    sys.modules["ebooklib"] = MagicMock()

    sys.modules["ebooklib.epub"] = MagicMock()
    sys.modules["pdf2image"] = MagicMock()


setup_mocks()


def test_shelf_grid_layout_columns() -> None:
    """Verify that multiple books are placed in different columns."""
    app = Adw.Application(application_id="org.test.eshelf")
    success = [False]

    def on_activate(app: Adw.Application) -> None:
        win = Adw.ApplicationWindow(application=app)
        win.set_default_size(1000, 800)

        grid = ShelfGrid(on_book_selected_callback=lambda b: None)
        books = [
            Book(path=f"/tmp/book{i}.pdf", title=f"Book {i}", author="Author")
            for i in range(10)
        ]
        grid.update_books(books)

        win.set_content(grid)
        win.present()

        GLib.timeout_add(100, check_layout, grid, win, app)

    def check_layout(
        grid: ShelfGrid, win: Adw.ApplicationWindow, app: Adw.Application
    ) -> bool:
        child1 = grid.get_first_child()
        if not child1:
            app.quit()
            return False

        child2 = child1.get_next_sibling()
        if not child2:
            app.quit()
            return False

        alloc1 = child1.allocation
        alloc2 = child2.allocation

        print(f"Child 1: x={alloc1.x}")
        print(f"Child 2: x={alloc2.x}")

        if alloc1.x != alloc2.x:
            success[0] = True

        app.quit()
        return False

    app.connect("activate", on_activate)
    try:
        app.run([])
    except Exception as e:
        print(f"Could not run GTK app test: {e}")

    assert success[0], "Books should be in different columns"
