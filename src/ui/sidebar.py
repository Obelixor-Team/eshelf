"""Sidebar for category selection and management."""

from typing import Callable, Optional

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402

from src.models.category import Category  # noqa: E402


class CategoryRow(Gtk.ListBoxRow):  # type: ignore
    """Custom ListBoxRow that stores a category identifier."""

    def __init__(self, identifier: str):
        """Initialize the CategoryRow."""
        super().__init__()
        self.identifier = identifier


class Sidebar(Adw.Bin):  # type: ignore
    """Sidebar for navigating book categories."""

    def __init__(
        self,
        on_category_selected: Callable[[Optional[int], bool], None],
        on_category_created: Callable[[str], None],
        on_category_deleted: Callable[[int], None],
    ) -> None:
        """Initialize the Sidebar.

        Args:
            on_category_selected (Callable): Callback when a category is selected.
            on_category_created (Callable): Callback when a new category is created.
            on_category_deleted (Callable): Callback when a category is deleted.
        """
        super().__init__()
        self.on_category_selected = on_category_selected
        self.on_category_created = on_category_created
        self.on_category_deleted = on_category_deleted

        # Main container
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(self.main_box)

        # Header
        header = Gtk.Label(label="Bookshelves", xalign=0)
        header.set_margin_top(12)
        header.set_margin_bottom(12)
        header.set_margin_start(12)
        header.set_margin_end(12)
        header.add_css_class("title-4")
        self.main_box.append(header)

        # Category list
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.connect("row-selected", self.on_row_selected)
        self.list_box.add_css_class("navigation-sidebar")

        # Wrap in scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_child(self.list_box)
        self.main_box.append(scrolled)

        # Footer for adding categories
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        footer.set_margin_top(12)
        footer.set_margin_bottom(12)
        footer.set_margin_start(12)
        footer.set_margin_end(12)

        self.category_entry = Gtk.Entry(placeholder_text="New category...")
        self.add_button = Gtk.Button(icon_name="list-add-symbolic")
        self.add_button.connect("clicked", self.on_add_clicked)

        footer.append(self.category_entry)
        footer.append(self.add_button)
        self.main_box.append(footer)

    def update_categories(self, categories: list[Category]) -> None:
        """Refresh the category list."""
        # Clear current items
        while child := self.list_box.get_first_child():
            self.list_box.remove(child)

        # "All Books" item
        all_row = self._create_row("All Books", "all")
        self.list_box.append(all_row)

        # "Uncategorized" item
        uncat_row = self._create_row("Uncategorized", "uncategorized")
        self.list_box.append(uncat_row)

        # Custom categories
        for cat in categories:
            row = self._create_row(cat.name, str(cat.id))
            # Add a delete button to each category row
            del_btn = Gtk.Button(icon_name="edit-delete-symbolic")
            del_btn.set_valign(Gtk.Align.CENTER)
            del_btn.connect("clicked", self.on_delete_clicked, cat.id)

            # Row content box
            row_box = row.get_child()
            if isinstance(row_box, Gtk.Box):
                row_box.append(del_btn)

            self.list_box.append(row)

    def select_category(self, category_id: Optional[int], all_books: bool) -> None:
        """Programmatically select a category in the list."""
        if category_id is None:
            identifier = "all" if all_books else "uncategorized"
        else:
            identifier = str(category_id)

        row = self.list_box.get_first_child()
        while row:
            if isinstance(row, CategoryRow) and row.identifier == identifier:
                self.list_box.select_row(row)
                return
            row = row.get_next_sibling()

    def _create_row(self, label_text: str, identifier: str) -> CategoryRow:
        row = CategoryRow(identifier)
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)

        label = Gtk.Label(label=label_text, xalign=0)
        label.set_hexpand(True)
        box.append(label)

        row.set_child(box)
        return row

    def on_row_selected(
        self, list_box: Gtk.ListBox, row: Optional[CategoryRow]
    ) -> None:
        """Handle row selection change."""
        if not row:
            return

        identifier = row.identifier
        if identifier == "all":
            self.on_category_selected(None, True)
        elif identifier == "uncategorized":
            self.on_category_selected(None, False)
        elif identifier is not None:
            self.on_category_selected(int(identifier), False)

    def on_add_clicked(self, button: Gtk.Button) -> None:
        """Handle adding a new category."""
        name = self.category_entry.get_text().strip()
        if name:
            self.on_category_created(name)
            self.category_entry.set_text("")

    def on_delete_clicked(self, button: Gtk.Button, category_id: int) -> None:
        """Handle deleting a category."""
        self.on_category_deleted(category_id)
