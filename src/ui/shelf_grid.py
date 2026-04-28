"""UI component for the book grid."""

from typing import Callable

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk  # noqa: E402

from src.config import load_config  # noqa: E402
from src.models.book import Book  # noqa: E402
from src.ui.book_widget import BookWidget  # noqa: E402


class ShelfGrid(Gtk.Grid):  # type: ignore
    """A grid that displays a collection of BookWidgets."""

    def __init__(self, on_book_selected_callback: Callable[[Book], None]) -> None:
        """Initialize the ShelfGrid."""
        super().__init__()
        self.on_book_selected = on_book_selected_callback
        self.set_column_spacing(24)
        self.set_row_spacing(24)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_margin_top(18)
        self.set_margin_bottom(18)
        self.set_margin_start(18)
        self.set_margin_end(18)

    def update_books(self, books: list[Book]) -> None:
        """Refresh the grid with a new list of books."""
        # Remove existing children
        child = self.get_first_child()
        while child:
            self.remove(child)
            child = self.get_first_child()

        # Get column count from config
        config = load_config()
        cols = config.get("books_per_line", 4)

        # Explicit grid with dynamic columns
        for i, book in enumerate(books):
            widget = BookWidget(book, self.on_book_selected)
            self.attach(widget, i % cols, i // cols, 1, 1)
