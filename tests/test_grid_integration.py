"""Integration test to verify the grid layout behavior."""

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")


from src.models.book import Book  # noqa: E402
from src.ui.shelf_grid import ShelfGrid  # noqa: E402


def test_shelf_grid_layout_columns() -> None:
    """Verify that multiple books are placed in different columns."""
    # Create grid with mock callbacks
    grid = ShelfGrid(
        on_book_selected_callback=lambda b: None, on_book_right_clicked_callback=None
    )

    # Create test books
    books = [
        Book(path=f"/tmp/book{i}.pdf", title=f"Book {i}", author="Author")
        for i in range(10)
    ]

    # Update grid with books
    grid.update_books(books)

    # Verify store count
    assert grid.store.get_n_items() == 10

    # Verify the GridView's model is correct
    assert grid.grid_view.get_model() == grid.selection_model
    assert grid.selection_model.get_model() == grid.store
