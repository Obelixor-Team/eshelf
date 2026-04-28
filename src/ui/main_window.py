"""Main window for the eShelf application."""

from typing import Any, Optional

import gi

# noqa: E402
gi.require_version("Gtk", "4.0")
# noqa: E402
gi.require_version("Adw", "1")

# noqa: E402
from gi.repository import Adw, Gtk

# noqa: E402
from src.controller.main_controller import MainController

# noqa: E402
from src.models.book import Book

# noqa: E402
from src.ui.shelf_grid import ShelfGrid


class MainWindow(Adw.ApplicationWindow):  # type: ignore
    """The main window of the eShelf app."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the main window."""
        super().__init__(**kwargs)
        self.set_title("eShelf")
        self.set_default_size(800, 600)

        self.controller: Optional[MainController] = None

        # Main layout
        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(self.content_box)

        # Header bar
        self.header_bar = Adw.HeaderBar()
        self.content_box.append(self.header_bar)

        # Scan button
        self.scan_button = Gtk.Button(label="Scan Library")
        self.scan_button.connect("clicked", self.on_scan_clicked)
        self.header_bar.pack_start(self.scan_button)

        # Cleanup button
        self.cleanup_button = Gtk.Button(label="Cleanup")
        self.cleanup_button.connect("clicked", self.on_cleanup_clicked)
        self.header_bar.pack_start(self.cleanup_button)

        # Scrollable area for the grid
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.content_box.append(self.scrolled_window)

        # The grid
        self.grid = ShelfGrid(self.on_book_selected)
        self.scrolled_window.set_child(self.grid)

    def set_controller(self, controller: MainController) -> None:
        """Inject the controller and refresh the view."""
        self.controller = controller
        self.refresh_grid()

    def refresh_grid(self) -> None:
        """Update the grid with books from the controller."""
        if self.controller:
            books = self.controller.get_books()
            self.grid.update_books(books)

    def on_scan_clicked(self, button: Gtk.Button) -> None:
        """Handle the scan button click."""
        if self.controller:
            added, updated = self.controller.scan_library()
            self.refresh_grid()
            print(f"Scan complete: {added} added, {updated} updated.")

    def on_cleanup_clicked(self, button: Gtk.Button) -> None:
        """Handle the cleanup button click."""
        if self.controller:
            removed = self.controller.cleanup_library()
            self.refresh_grid()
            print(f"Cleanup complete: {removed} books removed.")

    def on_book_selected(self, book: Book) -> None:
        """Handle book selection."""
        if self.controller:
            self.controller.open_book(book)
