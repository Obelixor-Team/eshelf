"""UI component representing a single book on the shelf."""

from typing import Callable, Optional

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gdk, Gtk, Pango  # noqa: E402

from src.config import load_config  # noqa: E402
from src.models.book import Book  # noqa: E402


class BookWidget(Gtk.Box):  # type: ignore
    """A widget that displays a book's cover and title."""

    def __init__(
        self,
        book: Book,
        on_click_callback: Callable[[Book], None],
        on_right_click_callback: Optional[Callable[[Gtk.Widget, Book], None]] = None,
    ) -> None:
        """Initialize the BookWidget.

        Args:
            book (Book): The book to display.
            on_click_callback (callable): Callback function when the book is clicked.
            on_right_click_callback (callable): Callback function when the book is
                right-clicked.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.on_right_click_callback = on_right_click_callback

        config = load_config()
        width = int(120 * config.get("zoom_level", 1.0))
        height = int(180 * config.get("zoom_level", 1.0))

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_size_request(width, -1)
        self.book = book

        # Cover image
        image = Gtk.Picture()
        image.set_size_request(width, height)
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)
        image.set_content_fit(Gtk.ContentFit.CONTAIN)
        if book.cover_path:
            try:
                texture = Gdk.Texture.new_from_filename(book.cover_path)
                image.set_paintable(texture)
            except Exception as e:
                print(f"Error loading cover image: {e}")

        self.append(image)

        # Title label
        label = Gtk.Label(label=book.title)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_max_width_chars(15)
        label.set_width_chars(15)
        label.set_wrap(True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_halign(Gtk.Align.CENTER)
        self.append(label)

        # Click gestures
        click_gesture = Gtk.GestureClick()
        click_gesture.set_button(1)  # Left click
        click_gesture.connect("released", lambda *args: on_click_callback(self.book))
        self.add_controller(click_gesture)

        if self.on_right_click_callback:
            right_click_gesture = Gtk.GestureClick()
            right_click_gesture.set_button(3)  # Right click
            right_click_gesture.connect("released", self.on_right_clicked)
            self.add_controller(right_click_gesture)

    def on_right_clicked(self, gesture: Gtk.GestureClick, n_press: int) -> None:
        """Handle right click to show context menu."""
        if self.on_right_click_callback:
            self.on_right_click_callback(self, self.book)
