"""UI component for the book grid."""

from typing import Callable

# noqa: E402
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# noqa: E402
from gi.repository import Gtk

# noqa: E402
from src.models.book import Book

# noqa: E402
from src.ui.book_widget import BookWidget


class ShelfGrid(Gtk.FlowBox):
    """A grid that displays a collection of BookWidgets."""

    def __init__(self, on_book_selected_callback: Callable[[Book], None]) -> None:
        """Initialize the ShelfGrid.

        Args:
            on_book_selected_callback (callable): Callback for when a book is selected.
        """
        super().__init__()
        self.on_book_selected = on_book_selected_callback
        self.set_valign(Gtk.Align.START)
        self.set_halign(Gtk.Align.CENTER)
        self.set_max_children_per_line(10)
        self.set_selection_mode(Gtk.SelectionMode.NONE)
        self.set_column_spacing(12)
        self.set_row_spacing(12)

    def update_books(self, books: list[Book]) -> None:
        """Refresh the grid with a new list of books.

        Args:
            books (list[Book]): List of books to display.
        """
        # Remove existing children
        child = self.get_first_child()
        while child:
            self.remove(child)
            child = self.get_first_child()

        # Add new book widgets
        for book in books:
            widget = BookWidget(book, self.on_book_selected)
            self.append(widget)
