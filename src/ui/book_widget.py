"""UI component representing a single book on the shelf."""

from typing import Callable

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gdk, Gtk  # noqa: E402

from src.config import load_config  # noqa: E402
from src.models.book import Book  # noqa: E402


class BookWidget(Gtk.Box):  # type: ignore
    """A widget that displays a book's cover and title."""

    def __init__(self, book: Book, on_click_callback: Callable[[Book], None]) -> None:
        """Initialize the BookWidget.

        Args:
            book (Book): The book to display.
            on_click_callback (callable): Callback function when the book is clicked.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        config = load_config()
        width = config.get("cover_width", 120)
        height = config.get("cover_height", 180)

        # Strictly define the size of the widget
        self.set_size_request(width, height + 40)  # image height + label space
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_halign(Gtk.Align.START)
        self.set_valign(Gtk.Align.START)
        self.book = book

        # Cover image
        image = Gtk.Picture()
        config = load_config()
        zoom = config.get("zoom_level", 1.0)
        width = int(120 * zoom)
        height = int(180 * zoom)
        image.set_size_request(width, height)
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)
        image.set_hexpand(False)
        image.set_vexpand(False)
        image.set_content_fit(Gtk.ContentFit.CONTAIN)
        if book.cover_path:
            try:
                texture = Gdk.Texture.new_from_filename(book.cover_path)
                image.set_paintable(texture)
            except Exception as e:
                print(f"Error loading cover image: {e}")
        else:
            pass

        self.append(image)

        # Title label
        label = Gtk.Label(label=book.title)
        label.set_ellipsize(3)  # Pango.EllipsizeMode.END
        label.set_max_width_chars(15)
        label.set_wrap(True)
        label.set_halign(Gtk.Align.CENTER)
        self.append(label)

        # Make the widget clickable
        gesture = Gtk.GestureClick()
        gesture.connect("released", lambda *args: on_click_callback(self.book))
        self.add_controller(gesture)
