"""Main window for the eShelf application."""

from typing import Any, Optional

import gi
from gi.repository import GLib

from src.config import load_config, save_config

gi.require_version("Gtk", "4.0")  # noqa: E402
gi.require_version("Adw", "1")  # noqa: E402

from gi.repository import Adw, Gtk  # noqa: E402

from src.controller.main_controller import MainController  # noqa: E402
from src.models.book import Book  # noqa: E402
from src.ui.shelf_grid import ShelfGrid  # noqa: E402
from src.ui.sidebar import Sidebar  # noqa: E402


class MainWindow(Adw.ApplicationWindow):  # type: ignore
    """The main window of the eShelf app."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the main window."""
        super().__init__(**kwargs)
        self.set_title("eShelf")
        self.set_default_size(1000, 600)

        self.controller: Optional[MainController] = None

        # Main layout
        self.main_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.set_content(self.main_layout)

        # Sidebar setup
        self.sidebar = Sidebar(
            on_category_selected=self.on_category_selected,
            on_category_created=self.on_category_created,
            on_category_deleted=self.on_category_deleted,
        )
        self.sidebar.set_size_request(250, -1)
        self.main_layout.append(self.sidebar)

        # Content setup
        self.toolbar_view = Adw.ToolbarView()
        self.toolbar_view.set_hexpand(True)
        self.main_layout.append(self.toolbar_view)

        # Header bar
        self.header_bar = Adw.HeaderBar()
        self.toolbar_view.add_top_bar(self.header_bar)

        # Sidebar toggle button
        self.sidebar_toggle = Gtk.Button(icon_name="sidebar-show-symbolic")
        self.sidebar_toggle.connect("clicked", self.on_sidebar_toggle_clicked)
        self.header_bar.pack_start(self.sidebar_toggle)

        # Burger menu button
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu")

        # Create the menu
        self.menu = Gtk.Popover()
        self.menu_button.set_popover(self.menu)

        # Menu container
        menu_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        menu_box.set_margin_top(6)
        menu_box.set_margin_bottom(6)
        menu_box.set_margin_start(6)
        menu_box.set_margin_end(6)
        self.menu.set_child(menu_box)

        # Menu items
        self.import_file_item = Gtk.Button(label="Import File")
        self.import_file_item.connect("clicked", self.on_import_file_clicked)

        self.import_folder_item = Gtk.Button(label="Import Folder")
        self.import_folder_item.connect("clicked", self.on_import_folder_clicked)

        self.cleanup_item = Gtk.Button(label="Cleanup Library")
        self.cleanup_item.connect("clicked", self.on_cleanup_clicked)

        self.settings_item = Gtk.Button(label="Settings")
        self.settings_item.connect("clicked", self.on_settings_clicked)

        menu_box.append(self.import_file_item)
        menu_box.append(self.import_folder_item)
        menu_box.append(self.cleanup_item)
        menu_box.append(self.settings_item)

        self.header_bar.pack_start(self.menu_button)

        # Scan button
        self.scan_button = Gtk.Button(label="Scan Library")
        self.scan_button.connect("clicked", self.on_scan_clicked)
        self.header_bar.pack_start(self.scan_button)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        self.progress_bar.set_valign(Gtk.Align.CENTER)
        self.header_bar.pack_start(self.progress_bar)

        # Scrollable area for the grid
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_hexpand(True)
        self.scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.toolbar_view.set_content(self.scrolled_window)

        # The grid
        self.grid = ShelfGrid(self.on_book_selected, self.on_book_right_clicked)
        self.scrolled_window.set_child(self.grid)

    def set_controller(self, controller: MainController) -> None:
        """Inject the controller and refresh the view."""
        self.controller = controller
        self.refresh_grid()
        self.refresh_sidebar()

    def refresh_sidebar(self) -> None:
        """Update the sidebar with current categories."""
        if self.controller:
            categories = self.controller.get_categories()
            self.sidebar.update_categories(categories)

    def refresh_grid(
        self, category_id: Optional[int] = None, all_books: bool = True
    ) -> None:
        """Update the grid with books from the controller."""
        if self.controller:
            if all_books:
                books = self.controller.get_books(None)
            elif category_id is None:
                books = self.controller.get_uncategorized_books()
            else:
                books = self.controller.get_books(category_id)
            self.grid.update_books(books)

    def on_category_selected(self, category_id: Optional[int], all_books: bool) -> None:
        """Handle category selection from sidebar."""
        self.refresh_grid(category_id, all_books)

    def on_category_created(self, name: str) -> None:
        """Handle new category creation."""
        if self.controller:
            self.controller.create_category(name)
            self.refresh_sidebar()

    def on_category_deleted(self, category_id: int) -> None:
        """Handle category deletion."""
        if self.controller:
            self.controller.delete_category(category_id)
            self.refresh_sidebar()

    def on_sidebar_toggle_clicked(self, button: Gtk.Button) -> None:
        """Toggle sidebar visibility."""
        if self.sidebar.get_visible():
            self.sidebar.set_visible(False)
            self.sidebar_toggle.set_icon_name("sidebar-show-symbolic")
        else:
            self.sidebar.set_visible(True)
            self.sidebar_toggle.set_icon_name("sidebar-collapse-symbolic")

    def on_import_file_clicked(self, item: Gtk.Button) -> None:
        """Handle import file action."""
        if not self.controller:
            return

        dialog = Gtk.FileDialog(title="Select Book File")

        # Create a filter for PDF and EPUB files
        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name("Books")
        filter_pdf.add_pattern("*.pdf")
        filter_pdf.add_pattern("*.epub")

        # Create a Gio.ListStore to hold the filter
        from gi.repository import Gio

        filters = Gio.ListStore()
        filters.append(filter_pdf)

        dialog.set_filters(filters)

        def on_open_response(dialog: Any, result: Any) -> None:
            try:
                file = dialog.open_finish(result)
                controller = self.controller
                if file and controller:
                    path = file.get_path()
                    success = controller.import_file(path)
                    if success:
                        self.refresh_grid()
            except Exception as e:
                print(f"Error importing file: {e}")

        dialog.open(self, None, on_open_response)

    def on_import_folder_clicked(self, item: Gtk.Button) -> None:
        """Handle import folder action."""
        if not self.controller:
            return

        dialog = Gtk.FileDialog(title="Select Books Folder")

        def on_open_response(dialog: Any, result: Any) -> None:
            try:
                folder = dialog.select_folder_finish(result)
                controller = self.controller
                if folder and controller:
                    path = folder.get_path()
                    added, updated = controller.import_folder(path)
                    self.refresh_grid()
                    print(f"Folder import complete: {added} added, {updated} updated.")
            except Exception as e:
                print(f"Error importing folder: {e}")

        dialog.select_folder(self, None, on_open_response)

    def on_scan_clicked(self, button: Gtk.Button) -> None:
        """Handle the scan button click."""
        if not self.controller:
            return

        # UI state for scanning
        self.scan_button.set_sensitive(False)
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0.0)

        import threading

        def scan_worker() -> None:
            def progress_update(current: int, total: int) -> None:
                GLib.idle_add(self.update_progress, current, total)

            controller = self.controller
            if controller:
                added, updated = controller.scan_library(
                    progress_callback=progress_update
                )
                GLib.idle_add(self.on_scan_finished, added, updated)

        thread = threading.Thread(target=scan_worker, daemon=True)
        thread.start()

    def update_progress(self, current: int, total: int) -> bool:
        """Update progress bar fraction."""
        fraction = current / total
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"Scanning... {current}/{total}")
        self.progress_bar.set_show_text(True)
        return False

    def on_scan_finished(self, added: int, updated: int) -> bool:
        """Handle completion of the scan process."""
        self.scan_button.set_sensitive(True)
        self.progress_bar.set_visible(False)
        self.refresh_grid()
        print(f"Scan complete: {added} added, {updated} updated.")
        return False

    def on_cleanup_clicked(self, button: Gtk.Button) -> None:
        """Handle the cleanup button click."""
        if self.controller:
            removed = self.controller.cleanup_library()
            self.refresh_grid()
            print(f"Cleanup complete: {removed} books removed.")

    def on_settings_clicked(self, button: Gtk.Button) -> None:
        """Handle the settings button click."""
        config = load_config()

        dialog = Gtk.Dialog(title="Settings", transient_for=self, modal=True)
        dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
        dialog.add_button("Save", Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        content_area.set_margin_top(12)
        content_area.set_margin_bottom(12)
        content_area.set_margin_start(12)
        content_area.set_margin_end(12)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        content_area.append(box)

        def create_setting_row(label_text: str, key: str) -> Gtk.SpinButton:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            label = Gtk.Label(label=label_text, xalign=0)
            adjustment = Gtk.Adjustment(
                value=config.get(key, 0), lower=1, upper=10, step_increment=1
            )
            spin = Gtk.SpinButton(adjustment=adjustment)
            row.append(label)
            row.append(spin)
            box.append(row)
            return spin

        books_per_line_spin: Gtk.SpinButton = create_setting_row(
            "Books per line:", "books_per_line"
        )

        # Zoom level setting
        zoom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        zoom_label = Gtk.Label(label="Cover zoom:", xalign=0)
        zoom_adjustment = Gtk.Adjustment(
            value=config.get("zoom_level", 1.0),
            lower=0.5,
            upper=3.0,
            step_increment=0.1,
        )

        zoom_spin: Gtk.SpinButton = Gtk.SpinButton(adjustment=zoom_adjustment, digits=1)
        zoom_row.append(zoom_label)
        zoom_row.append(zoom_spin)
        box.append(zoom_row)

        # Cache directory setting
        cache_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        cache_label = Gtk.Label(label="Cache directory:", xalign=0)
        cache_entry = Gtk.Entry(text=config.get("cache_dir", ""))
        cache_entry.set_hexpand(True)

        def on_browse_clicked(button: Gtk.Button) -> None:
            folder_dialog = Gtk.FileDialog(title="Select Cache Directory")

            def on_folder_response(dialog: Any, result: Any) -> None:
                try:
                    folder = dialog.select_folder_finish(result)
                    if folder:
                        cache_entry.set_text(folder.get_path())
                except Exception as e:
                    print(f"Error selecting folder: {e}")

            folder_dialog.select_folder(dialog, on_folder_response)

        browse_button = Gtk.Button(label="Browse")
        browse_button.connect("clicked", on_browse_clicked)

        cache_row.append(cache_label)
        cache_row.append(cache_entry)
        cache_row.append(browse_button)
        box.append(cache_row)

        def on_response(dialog: Gtk.Dialog, response_id: int) -> None:
            if response_id == Gtk.ResponseType.OK:
                new_config = {
                    "books_per_line": int(books_per_line_spin.get_value()),
                    "zoom_level": float(zoom_spin.get_value()),
                    "cache_dir": cache_entry.get_text(),
                }
                save_config(new_config)
                self.refresh_grid()
            dialog.destroy()

        dialog.connect("response", on_response)
        dialog.present()

    def on_book_selected(self, book: Book) -> None:
        """Handle book selection."""
        if self.controller:
            self.controller.open_book(book)

    def on_book_right_clicked(self, widget: Gtk.Widget, book: Book) -> None:
        """Handle book right-click to move to category."""
        if not self.controller:
            return

        # Create a popover for category selection
        popover = Gtk.Popover()
        popover.set_parent(widget)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        popover.set_child(box)

        # "Uncategorized" option
        uncat_btn = Gtk.Button(label="Move to Uncategorized")
        uncat_btn.connect("clicked", lambda _: self.move_book(book, None))
        box.append(uncat_btn)

        # Category options
        categories = self.controller.get_categories()
        for cat in categories:
            btn = Gtk.Button(label=f"Move to {cat.name}")
            btn.connect("clicked", lambda _, c_id=cat.id: self.move_book(book, c_id))
            box.append(btn)

        popover.popup()

    def move_book(self, book: Book, category_id: Optional[int]) -> None:
        """Move a book to a category and refresh view."""
        if self.controller:
            self.controller.move_book_to_category(book.path, category_id)
            self.refresh_grid()
