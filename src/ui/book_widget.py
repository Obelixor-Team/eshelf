"""UI component representing a single book on the shelf."""

import logging
from typing import Callable, Optional

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("Gdk", "4.0")

from gi.repository import Gdk, Gtk, Pango  # noqa: E402

from src.models.book import Book  # noqa: E402


class BookWidget(Gtk.Box):  # type: ignore
    """A widget that displays a book's cover and title."""

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        zoom_level: float = 1.0,
    ) -> None:
        """Initialize the BookWidget.

        Args:
            zoom_level (float): Zoom factor for the cover size.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.on_click_callback: Optional[Callable[[Book], None]] = None
        self.on_right_click_callback: Optional[Callable[[Gtk.Widget, Book], None]] = (
            None
        )
        self.book: Optional[Book] = None
        self.zoom_level = zoom_level

        width = int(120 * zoom_level)
        height = int(180 * zoom_level)

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_size_request(width, -1)

        # Cover image
        self.image = Gtk.Picture()
        self.image.set_size_request(width, height)
        self.image.set_halign(Gtk.Align.CENTER)
        self.image.set_valign(Gtk.Align.CENTER)
        self.image.set_content_fit(Gtk.ContentFit.CONTAIN)
        self.append(self.image)

        # Title label
        self.label = Gtk.Label()
        self.label.set_ellipsize(Pango.EllipsizeMode.END)
        self.label.set_max_width_chars(15)
        self.label.set_width_chars(15)
        self.label.set_wrap(True)
        self.label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        self.label.set_justify(Gtk.Justification.CENTER)
        self.label.set_halign(Gtk.Align.CENTER)
        self.append(self.label)

        # Click gestures
        click_gesture = Gtk.GestureClick()
        click_gesture.set_button(1)  # Left click
        click_gesture.connect("pressed", self._on_clicked)
        self.add_controller(click_gesture)

        self.right_click_gesture = Gtk.GestureClick()
        self.right_click_gesture.set_button(3)  # Right click
        self.right_click_gesture.connect("pressed", self.on_right_clicked)
        self.add_controller(self.right_click_gesture)

    def bind(
        self,
        book: Book,
        on_click_callback: Callable[[Book], None],
        on_right_click_callback: Optional[Callable[[Gtk.Widget, Book], None]] = None,
    ) -> None:
        """Bind a book to this widget."""
        self.book = book
        self.on_click_callback = on_click_callback
        self.on_right_click_callback = on_right_click_callback

        self.label.set_label(book.title)

        if book.cover_path:
            try:
                texture = Gdk.Texture.new_from_filename(book.cover_path)
                self.image.set_paintable(texture)
            except Exception as e:
                self.logger.error(f"Error loading cover image: {e}")
                self.image.set_paintable(None)
        else:
            self.image.set_paintable(None)

    def _on_clicked(
        self,
        gesture: Gtk.GestureClick,
        n_press: int,
        x: float,
        y: float,
    ) -> None:
        """Handle book click. Open on double click."""
        # Only open on double click (n_press=2)
        if n_press == 2 and self.book and self.on_click_callback:
            self.on_click_callback(self.book)

    def on_right_clicked(
        self,
        gesture: Gtk.GestureClick,
        n_press: int,
        x: float,
        y: float,
    ) -> None:
        """Handle right click to show context menu."""
        if self.book and self.on_right_click_callback:
            self.on_right_click_callback(self, self.book)
