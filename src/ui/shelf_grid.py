"""UI component for the book grid using Gtk.GridView."""

from typing import Any, Callable, Optional

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio, Gtk  # noqa: E402

from src.config import load_config  # noqa: E402
from src.models.book import Book, BookObject  # noqa: E402
from src.ui.book_widget import BookWidget  # noqa: E402


class ShelfGrid(Gtk.Box):  # type: ignore
    """A grid that displays a collection of books using Gtk.GridView."""

    def __init__(
        self,
        on_book_selected_callback: Callable[[Book], None],
        on_book_right_clicked_callback: Optional[
            Callable[[Gtk.Widget, Book], None]
        ] = None,
    ) -> None:
        """Initialize the ShelfGrid."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.on_book_selected = on_book_selected_callback
        self.on_book_right_clicked = on_book_right_clicked_callback
        self._config = load_config()

        # Model
        self.store = Gio.ListStore.new(BookObject)

        # Factory
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        # Selection Model
        self.selection_model = Gtk.SingleSelection.new(self.store)

        # Grid View
        self.grid_view = Gtk.GridView(
            model=self.selection_model,
            factory=factory,
        )
        self.grid_view.set_max_columns(20)
        self.grid_view.set_min_columns(1)
        self.grid_view.set_enable_rubberband(True)

        # Styling
        self.grid_view.set_margin_top(18)
        self.grid_view.set_margin_bottom(18)
        self.grid_view.set_margin_start(18)
        self.grid_view.set_margin_end(18)

        # Scrolled Window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_child(self.grid_view)
        scrolled.set_vexpand(True)

        self.append(scrolled)

    def _on_factory_setup(
        self, factory: Gtk.ListItemFactory, list_item: Gtk.ListItem
    ) -> None:
        """Create the widget for a list item."""
        zoom_level = self._config.get("zoom_level", 1.0)
        widget = BookWidget(zoom_level=zoom_level)
        # Wrap the widget in a box to enforce alignment/sizing
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        w, h = int(120 * zoom_level), int(168 * zoom_level)
        box.set_size_request(w, h)
        box.set_valign(Gtk.Align.CENTER)
        box.set_vexpand(False)
        box.append(widget)
        list_item.set_child(box)

    def _on_factory_bind(
        self, factory: Gtk.ListItemFactory, list_item: Gtk.ListItem
    ) -> None:
        """Bind the data to the widget."""
        book_obj = list_item.get_item()
        box = list_item.get_child()
        widget = box.get_first_child()
        show_titles = self._config.get("show_titles", True)
        if isinstance(book_obj, BookObject) and isinstance(widget, BookWidget):
            widget.bind(
                book_obj.book,
                self.on_book_selected,
                self.on_book_right_clicked,
                show_title=show_titles,
            )

    def update_config(self, config: dict[str, Any]) -> None:
        """Update the cached configuration."""
        self._config = config
        # We might need to recreate the factory or refresh widgets if zoom changes
        # For now, let's just trigger a reload of the store if needed,
        # but Gtk.GridView doesn't easily support dynamic widget resizing after setup
        # without some tricks. We'll stick to full refresh for config changes.

    def update_books(self, books: list[Book]) -> None:
        """Refresh the grid with a new list of books."""
        self.store.remove_all()
        for book in books:
            self.store.append(BookObject(book))
