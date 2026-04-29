"""UI component for the book grid."""

from typing import Callable, Optional

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk  # noqa: E402

from src.config import load_config  # noqa: E402
from src.models.book import Book  # noqa: E402
from src.ui.book_widget import BookWidget  # noqa: E402


class ShelfGrid(Gtk.Grid):  # type: ignore
    """A grid that displays a collection of BookWidgets."""

    def __init__(
        self,
        on_book_selected_callback: Callable[[Book], None],
        on_book_right_clicked_callback: Optional[
            Callable[[Gtk.Widget, Book], None]
        ] = None,
    ) -> None:
        """Initialize the ShelfGrid."""
        super().__init__()
        self.on_book_selected = on_book_selected_callback
        self.on_book_right_clicked = on_book_right_clicked_callback
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

        # Get column count and zoom from config
        config = load_config()
        cols = config.get("books_per_line", 4)
        zoom_level = config.get("zoom_level", 1.0)

        # Explicit grid with dynamic columns
        for i, book in enumerate(books):
            widget = BookWidget(
                book,
                self.on_book_selected,
                zoom_level=zoom_level,
                on_right_click_callback=self.on_book_right_clicked,
            )
            self.attach(widget, i % cols, i // cols, 1, 1)
