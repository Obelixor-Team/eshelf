"""UI component representing a single book on the shelf."""

from typing import Callable

# noqa: E402
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

# noqa: E402
from gi.repository import Adw, GdkPixbuf, Gtk

# noqa: E402
from src.models.book import Book


class BookWidget(Adw.Bin):
    """A widget that displays a book's cover and title."""

    def __init__(self, book: Book, on_click_callback: Callable[[Book], None]) -> None:
        """Initialize the BookWidget.

        Args:
            book (Book): The book to display.
            on_click_callback (callable): Callback function when the book is clicked.
        """
        super().__init__()
        self.book = book

        # Layout container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(box)

        # Cover image
        image = Gtk.Image()
        if book.cover_path:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                book.cover_path, width=120, height=180, preserve_aspect_ratio=True
            )
            image.set_from_pixbuf(pixbuf)
        else:
            # Fallback to a generic book icon
            image.set_from_icon_name("book-cover")

        box.append(image)

        # Title label
        label = Gtk.Label(label=book.title)
        label.set_ellipsize(3)  # Pango.EllipsizeMode.END
        label.set_max_width_chars(15)
        label.set_halign(Gtk.Align.CENTER)
        box.append(label)

        # Make the widget clickable
        gesture = Gtk.GestureClick()
        gesture.connect("released", lambda *args: on_click_callback(self.book))
        self.add_controller(gesture)
