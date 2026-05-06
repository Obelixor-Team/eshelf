"""UI component for the book grid using Gtk.GridView."""

from typing import Any, Callable, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk  # noqa: E402

from src.config import load_config  # noqa: E402
from src.database.repository import BookRepository  # noqa: E402
from src.models.book import Book, BookObject  # noqa: E402
from src.models.book_model import BookListModel  # noqa: E402
from src.ui.book_widget import BookWidget  # noqa: E402


class ShelfGrid(Gtk.Box):  # type: ignore
    """A grid that displays a collection of books using Gtk.GridView."""

    def __init__(
        self,
        repository: BookRepository,
        on_book_selected_callback: Callable[[Book], None],
        on_book_right_clicked_callback: Optional[
            Callable[[Gtk.Widget, Book], None]
        ] = None,
    ) -> None:
        """Initialize the ShelfGrid."""
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self.repository = repository
        self.on_book_selected = on_book_selected_callback
        self.on_book_right_clicked = on_book_right_clicked_callback
        self._config = load_config()

        self._current_category_id: Optional[int] = None
        self._current_all_books: bool = True
        self._current_search_query: Optional[str] = None

        # Model
        self.model = BookListModel(self.repository)

        # Factory
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        # Selection Model
        self.selection_model = Gtk.MultiSelection.new(self.model)

        # Grid View
        cols = self._config.get("books_per_line", 6)
        self.grid_view = Gtk.GridView(
            model=self.selection_model,
            factory=factory,
        )
        self.grid_view.set_max_columns(cols)
        self.grid_view.set_min_columns(cols)
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
        widget = BookWidget(
            zoom_level=zoom_level, get_selected_books_callback=self.get_selected_books
        )
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
        """Update the cached configuration and force a grid refresh."""
        self._config = config
        cols = self._config.get("books_per_line", 6)
        self.grid_view.set_max_columns(cols)
        self.grid_view.set_min_columns(cols)
        self.grid_view.queue_resize()
        # Refresh with current filters
        self.update_books(
            self._current_category_id,
            self._current_all_books,
            self._current_search_query,
        )

    def update_books(
        self,
        category_id: Optional[int] = None,
        all_books: bool = True,
        search_query: Optional[str] = None,
    ) -> None:
        """Refresh the grid with a new model or invalidate the existing one."""
        if (
            self.model is not None
            and self.model.repository == self.repository
            and self.model.repository is not None
            and self._current_category_id == category_id
            and self._current_all_books == all_books
            and self._current_search_query == search_query
        ):
            self.model.invalidate_cache()
            self.queue_draw()
            return

        self._current_category_id = category_id
        self._current_all_books = all_books
        self._current_search_query = search_query
        self.model = BookListModel(
            self.repository,
            category_id=self._current_category_id,
            all_books=self._current_all_books,
            search_query=self._current_search_query,
        )
        self.selection_model.set_model(self.model)
        self.queue_draw()

    def get_selected_books(self) -> list[Book]:
        """Return the list of currently selected books."""
        selection = self.selection_model.get_selection()
        selected_books = []
        for i in range(self.model.do_get_n_items()):
            if selection.contains(i):
                book_obj = self.model.do_get_item(i)
                if isinstance(book_obj, BookObject):
                    selected_books.append(book_obj.book)
        return selected_books
