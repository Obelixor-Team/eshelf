"""Main window for the eShelf application."""

import threading
from typing import Any, List, Optional

import gi
from gi.repository import GLib

from src.config import load_config, save_config

gi.require_version("Gtk", "4.0")  # noqa: E402
gi.require_version("Adw", "1")  # noqa: E402

from gi.repository import Adw, Gtk  # noqa: E402

from src.controller.main_controller import MainController  # noqa: E402
from src.models.book import Book  # noqa: E402
from src.ui.shelf_grid import ShelfGrid  # noqa: E402
from src.ui.sidebar import CategoryRow, Sidebar  # noqa: E402


class MainWindow(Adw.ApplicationWindow):  # type: ignore
    """The main window of the eShelf app."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the main window."""
        super().__init__(**kwargs)
        self.set_title("eShelf")
        self.set_default_size(1000, 600)
        self._is_initializing = False

        self.controller: Optional[MainController] = None

        # Main layout
        self.main_layout = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)

        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        self.toast_overlay.set_child(self.main_layout)

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
        self.import_item = Gtk.Button(label="Import")
        self.import_item.connect("clicked", self.on_import_clicked)

        self.cleanup_item = Gtk.Button(label="Cleanup Library")
        self.cleanup_item.connect("clicked", self.on_cleanup_clicked)

        self.settings_item = Gtk.Button(label="Settings")
        self.settings_item.connect("clicked", self.on_settings_clicked)

        menu_box.append(self.import_item)
        menu_box.append(self.cleanup_item)
        menu_box.append(self.settings_item)

        self.header_bar.pack_start(self.menu_button)

        # Scan button
        self.scan_button = Gtk.Button(label="Scan Library")
        self.scan_button.connect("clicked", self.on_scan_clicked)
        self.header_bar.pack_start(self.scan_button)

        # Search entry
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Search title or author...")
        self.search_entry.connect("search-changed", self.on_search_changed)
        self.header_bar.pack_start(self.search_entry)

        # Sort options
        sort_model = Gtk.StringList()
        sort_model.append("Title")
        sort_model.append("Author")
        sort_model.append("Recently Added")
        self.sort_combo = Gtk.DropDown(model=sort_model)
        self.sort_combo.set_selected(0)
        self.sort_combo.connect("notify::selected", self.on_sort_changed)
        self.header_bar.pack_start(self.sort_combo)

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
        # Provide error callback to the controller
        self.controller.error_callback = self.show_error

        # Restore persisted UI state
        self._is_initializing = True
        try:
            config = load_config()

            # Sidebar visibility
            self.sidebar.set_visible(config.get("sidebar_visible", True))
            if not self.sidebar.get_visible():
                self.sidebar_toggle.set_icon_name("sidebar-show-symbolic")
            else:
                self.sidebar_toggle.set_icon_name("sidebar-collapse-symbolic")

            # Sort option
            last_sort = config.get("last_sort_option", "Title")
            # Find index of last_sort in combo
            model = self.sort_combo.get_model()
            for i in range(model.get_n_items()):
                item = model.get_item(i)
                if item.get_string() == last_sort:
                    self.sort_combo.set_selected(i)
                    break

            self.refresh_sidebar()

            # Active category
            last_cat_id = config.get("last_category_identifier", "all")
            category_id = None
            all_books = True

            if last_cat_id == "all":
                self.sidebar.select_category(None, True)
            elif last_cat_id == "uncategorized":
                self.sidebar.select_category(None, False)
                all_books = False
            else:
                try:
                    potential_id = int(last_cat_id)
                    existing_categories = {
                        cat.id for cat in self.controller.get_categories()
                    }
                    if potential_id in existing_categories:
                        category_id = potential_id
                        self.sidebar.select_category(category_id, False)
                        all_books = False
                    else:
                        self.sidebar.select_category(None, True)
                except ValueError:
                    self.sidebar.select_category(None, True)

            # Final grid refresh with category and sort
            self.refresh_grid(
                category_id=category_id, all_books=all_books, sort_by=last_sort
            )
        finally:
            self._is_initializing = False

    def show_error(self, message: str) -> None:
        """Show an error message dialog."""
        dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Error",
            body=message,
        )
        dialog.add_response("ok", "OK")
        dialog.set_default_response("ok")
        dialog.present()

    def show_toast(self, message: str) -> None:
        """Show a toast notification."""

        def _show() -> None:
            toast = Adw.Toast()
            toast.set_title(message)
            self.toast_overlay.add_toast(toast)

        GLib.idle_add(_show)

    def save_ui_state(self) -> None:
        """Save current UI state to configuration."""
        config = load_config()

        # Sidebar visibility
        config["sidebar_visible"] = self.sidebar.get_visible()

        # Sort option
        item = self.sort_combo.get_selected_item()
        config["last_sort_option"] = item.get_string() if item is not None else "Title"

        # Active category
        selected_row = self.sidebar.list_box.get_selected_row()
        if selected_row and isinstance(selected_row, CategoryRow):
            config["last_category_identifier"] = selected_row.identifier
        else:
            config["last_category_identifier"] = "all"

        save_config(config)

    def refresh_sidebar(self) -> None:
        """Update the sidebar with current categories."""
        if self.controller:
            categories = self.controller.get_categories()
            self.sidebar.update_categories(categories)

    def refresh_grid(
        self,
        category_id: Optional[int] = None,
        all_books: bool = True,
        search_text: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> None:
        """Update the grid with books from the controller."""
        if self.controller:
            if search_text:
                books = self.controller.search_books(search_text)
            elif all_books:
                books = self.controller.get_books(None)
            elif category_id is None:
                books = self.controller.get_uncategorized_books()
            else:
                books = self.controller.get_books(category_id)

            if sort_by:
                books = self.controller.sort_books(books, sort_by)

            self.grid.update_books(books)

    def on_category_selected(self, category_id: Optional[int], all_books: bool) -> None:
        """Handle category selection from sidebar."""
        if self._is_initializing:
            return
        self.refresh_grid(category_id, all_books)
        self.save_ui_state()

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
            self.refresh_grid(None, True)

    def on_sidebar_toggle_clicked(self, button: Gtk.Button) -> None:
        """Toggle sidebar visibility."""
        if self.sidebar.get_visible():
            self.sidebar.set_visible(False)
            self.sidebar_toggle.set_icon_name("sidebar-show-symbolic")
        else:
            self.sidebar.set_visible(True)
            self.sidebar_toggle.set_icon_name("sidebar-collapse-symbolic")
        self.save_ui_state()

    def on_import_clicked(self, item: Gtk.Button) -> None:
        """Unified import handler."""
        if not self.controller:
            return

        dialog = Gtk.FileDialog(title="Select File or Folder to Import")
        dialog.set_modal(True)

        def on_choice(d: Adw.MessageDialog, response: str) -> None:
            if response == "file":
                file_dialog = Gtk.FileDialog(title="Select File to Import")
                file_dialog.set_modal(True)
                file_dialog.open(self, None, on_open_response)
            elif response == "folder":
                folder_dialog = Gtk.FileDialog(title="Select Folder to Import")
                folder_dialog.set_modal(True)
                folder_dialog.select_folder(self, None, on_folder_response)

        def on_open_response(dialog: Gtk.FileDialog, result: Any) -> None:
            try:
                file = dialog.open_finish(result)
                if file and self.controller:
                    self.show_category_dialog(file.get_path())
            except Exception as e:
                self.show_error(f"Error selecting file: {e}")

        def on_folder_response(dialog: Gtk.FileDialog, result: Any) -> None:
            try:
                folder = dialog.select_folder_finish(result)
                if folder and self.controller:
                    self.show_category_dialog(folder.get_path())
            except Exception as e:
                self.show_error(f"Error selecting folder: {e}")

        confirm_dialog.connect("response", on_choice)
        confirm_dialog.show()

    def show_category_dialog(self, path: str) -> None:
        """Show dialog to select a category for the import."""
        dialog = Adw.PreferencesDialog()
        dialog.set_title("Select Category")

        page = Adw.PreferencesPage()
        dialog.add(page)

        group = Adw.PreferencesGroup(title="Target Category")
        page.add(group)

        # Category list (or None for Uncategorized)
        combo = Gtk.ComboBoxText()
        combo.append("None", "Uncategorized")
        categories = self.controller.get_categories()
        for cat in categories:
            combo.append(str(cat.id), cat.name)
        combo.set_active_id("None")

        row = Adw.ActionRow(title="Category")
        row.add_suffix(combo)
        group.add(row)

        def on_import_confirmed(button: Gtk.Button) -> None:
            cat_id = combo.get_active_id()
            c_id = int(cat_id) if cat_id != "None" else None

            def worker() -> None:
                try:
                    added, updated, failed = self.controller.import_path(path, c_id)
                    GLib.idle_add(self.refresh_grid)
                    msg = f"Imported: {added} added, {updated} updated, {len(failed)} failed."
                    GLib.idle_add(self.show_toast, msg)
                except Exception as e:
                    GLib.idle_add(self.show_error, f"Error: {e}")

            threading.Thread(target=worker, daemon=True).start()
            dialog.close()

        save_btn = Gtk.Button(label="Import")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", on_import_confirmed)

        button_group = Adw.PreferencesGroup()
        button_group.add(save_btn)
        page.add(button_group)

        dialog.show()

    def on_scan_clicked(self, button: Gtk.Button) -> None:
        """Handle the scan button click."""
        if not self.controller:
            return

        # UI state for scanning
        self.scan_button.set_sensitive(False)
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0.0)

        def scan_worker() -> None:
            def progress_update(current: int, total: int) -> None:
                GLib.idle_add(self.update_progress, current, total)

            controller = self.controller
            if controller:
                added, updated, failed = controller.scan_library(
                    progress_callback=progress_update
                )
                GLib.idle_add(self.on_scan_finished, added, updated, failed)

        thread = threading.Thread(target=scan_worker, daemon=True)
        thread.start()

    def update_progress(self, current: int, total: int) -> bool:
        """Update progress bar fraction."""
        fraction = current / total
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"Scanning... {current}/{total}")
        self.progress_bar.set_show_text(True)
        return False

    def on_scan_finished(self, added: int, updated: int, failed: List[str]) -> bool:
        """Handle completion of the scan process."""
        self.scan_button.set_sensitive(True)
        self.progress_bar.set_visible(False)
        self.refresh_grid()
        if failed:
            msg = f"Scan complete: {added} added, {updated} updated"
            if failed:
                msg += f", {len(failed)} failed"
            self.show_toast(msg)
        else:
            self.show_toast(f"Scan complete: {added} added, {updated} updated.")
        return False

    def on_search_changed(self, entry: Gtk.SearchEntry) -> None:
        """Handle search text changes."""
        search_text = entry.get_text()
        self.refresh_grid(search_text=search_text)

    def on_sort_changed(self, combo: Gtk.DropDown) -> None:
        """Handle sort option changes."""
        item = combo.get_selected_item()
        if item is not None:
            sort_option = item.get_string()
        else:
            sort_option = "Title"
        self.refresh_grid(sort_by=sort_option)
        self.save_ui_state()

    def on_cleanup_clicked(self, button: Gtk.Button) -> None:
        """Handle the cleanup button click."""
        controller = self.controller
        if not controller:
            return

        def worker() -> None:
            try:
                removed = controller.cleanup_library()
                GLib.idle_add(self.refresh_grid)
                GLib.idle_add(
                    self.show_toast, f"Cleanup complete: {removed} books removed."
                )
            except Exception as e:
                GLib.idle_add(self.show_error, f"Error during cleanup: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def on_settings_clicked(self, button: Gtk.Button) -> None:
        """Handle the settings button click."""
        config = load_config()

        dialog = Adw.PreferencesDialog()
        dialog.set_title("Settings")

        page = Adw.PreferencesPage()
        dialog.add(page)

        group = Adw.PreferencesGroup(title="General")
        page.add(group)

        # Books per line
        books_per_line_row = Adw.ActionRow(title="Books per line")
        books_per_line_spin = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(
                value=config.get("books_per_line", 6),
                lower=1,
                upper=10,
                step_increment=1,
            )
        )
        books_per_line_row.add_suffix(books_per_line_spin)
        group.add(books_per_line_row)

        # Zoom level
        zoom_row = Adw.ActionRow(title="Cover zoom")
        zoom_spin = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(
                value=config.get("zoom_level", 1.0),
                lower=0.5,
                upper=3.0,
                step_increment=0.1,
            ),
            digits=1,
        )
        zoom_row.add_suffix(zoom_spin)
        group.add(zoom_row)

        # Library directory
        library_row = Adw.ActionRow(title="Library directory")
        library_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        library_entry = Gtk.Entry(text=config.get("library_dir", ""))
        library_entry.set_hexpand(True)

        def on_library_browse_clicked(button: Gtk.Button) -> None:
            folder_dialog = Gtk.FileDialog(title="Select Library Directory")

            def on_library_folder_response(dialog: Any, result: Any) -> None:
                try:
                    folder = dialog.select_folder_finish(result)
                    if folder:
                        library_entry.set_text(folder.get_path())
                except Exception as e:
                    self.show_error(f"Error selecting folder: {e}")

            folder_dialog.select_folder(self, on_library_folder_response)

        library_browse_button = Gtk.Button(icon_name="folder-open-symbolic")
        library_browse_button.connect("clicked", on_library_browse_clicked)
        library_box.append(library_entry)
        library_box.append(library_browse_button)
        library_row.add_suffix(library_box)
        group.add(library_row)

        # Cache directory
        cache_row = Adw.ActionRow(title="Cache directory")
        cache_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
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
                    self.show_error(f"Error selecting folder: {e}")

            folder_dialog.select_folder(self, on_folder_response)

        browse_button = Gtk.Button(icon_name="folder-open-symbolic")
        browse_button.connect("clicked", on_browse_clicked)
        cache_box.append(cache_entry)
        cache_box.append(browse_button)
        cache_row.add_suffix(cache_box)
        group.add(cache_row)

        # Clear library
        clear_group = Adw.PreferencesGroup(title="Danger Zone")
        clear_row = Adw.ActionRow(title="Clear Library")
        clear_btn = Gtk.Button(label="Clear Database & Images")
        clear_btn.add_css_class("destructive-action")

        def on_clear_clicked(button: Gtk.Button) -> None:
            # Confirm dialog
            confirm_dialog = Adw.MessageDialog(
                transient_for=self,
                heading="Clear Library?",
                body=(
                    "This will permanently delete all book metadata and cached cover "
                    "images. This cannot be undone."
                ),
            )
            confirm_dialog.add_response("cancel", "Cancel")
            confirm_dialog.add_response("clear", "Clear")
            confirm_dialog.set_response_appearance(
                "clear", Adw.ResponseAppearance.DESTRUCTIVE
            )
            confirm_dialog.set_default_response("cancel")
            confirm_dialog.set_close_response("cancel")

            def on_response(d: Adw.MessageDialog, response: str) -> None:
                if response == "clear" and self.controller:
                    try:
                        self.controller.clear_library()
                        self.refresh_grid()
                        self.show_toast("Library cleared successfully.")
                        dialog.close()
                    except Exception as e:
                        self.show_error(f"Error clearing library: {e}")

            confirm_dialog.connect("response", on_response)
            confirm_dialog.show()

        clear_btn.connect("clicked", on_clear_clicked)
        clear_row.add_suffix(clear_btn)
        clear_group.add(clear_row)
        page.add(clear_group)

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_bottom(12)
        button_box.set_margin_end(12)
        button_box.set_margin_start(12)

        # Add button box to a preferences group to fit in the preferences page
        button_group = Adw.PreferencesGroup()
        button_group.add(button_box)
        page.add(button_group)

        def on_save_clicked(button: Gtk.Button) -> None:
            try:
                new_config = {
                    "books_per_line": int(books_per_line_spin.get_value()),
                    "zoom_level": float(zoom_spin.get_value()),
                    "library_dir": library_entry.get_text(),
                    "cache_dir": cache_entry.get_text(),
                }
                save_config(new_config)
                self.grid.update_config(new_config)
                self.refresh_grid()
                dialog.close()
            except ValueError as e:
                self.show_error(str(e))

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", on_save_clicked)
        button_box.append(save_btn)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: dialog.close())
        button_box.append(cancel_btn)

        dialog.present()

    def on_book_selected(self, book: Book) -> None:
        """Handle book selection."""
        if self.controller:
            self.controller.open_book(book)

    def on_book_right_clicked(self, widget: Gtk.Widget, book: Book) -> None:
        """Handle book right-click to move to category or edit metadata."""
        if not self.controller:
            return

        # Create a popover for actions
        popover = Gtk.Popover()
        popover.set_parent(widget)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        popover.set_child(box)

        # Open action
        open_btn = Gtk.Button(label="Open")
        open_btn.connect("clicked", lambda _: self.on_book_selected(book))
        box.append(open_btn)

        # Edit metadata action
        edit_btn = Gtk.Button(label="Edit Metadata")
        edit_btn.connect(
            "clicked", lambda _: self.on_edit_metadata_clicked(book, popover)
        )
        box.append(edit_btn)

        # Separator
        separator = Gtk.Separator()
        box.append(separator)

        # "Uncategorized" option
        uncat_btn = Gtk.Button(label="Move to Uncategorized")
        uncat_btn.connect("clicked", lambda _: self.move_book(book, None, popover))
        box.append(uncat_btn)

        # Category options
        categories = self.controller.get_categories()
        for cat in categories:
            btn = Gtk.Button(label=f"Move to {cat.name}")
            btn.connect(
                "clicked", lambda _, c_id=cat.id: self.move_book(book, c_id, popover)
            )
            box.append(btn)

        popover.popup()

    def move_book(
        self,
        book: Book,
        category_id: Optional[int],
        popover: Optional[Gtk.Popover] = None,
    ) -> None:
        """Move a book to a category and refresh view."""
        if self.controller:
            self.controller.move_book_to_category(book.path, category_id)
            self.refresh_grid()
            if popover:
                popover.popdown()

    def on_edit_metadata_clicked(self, book: Book, popover: Gtk.Popover) -> None:
        """Show a dialog to edit book metadata."""
        if popover:
            popover.popdown()

        dialog = Adw.Dialog(title="Edit Metadata")

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(12)
        box.set_margin_bottom(12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        dialog.set_child(box)

        title_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        title_label = Gtk.Label(label="Title", xalign=0)
        title_entry = Gtk.Entry(text=book.title)
        title_row.append(title_label)
        title_row.append(title_entry)
        box.append(title_row)

        author_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        author_label = Gtk.Label(label="Author", xalign=0)
        author_entry = Gtk.Entry(text=book.author)
        author_row.append(author_label)
        author_row.append(author_entry)
        box.append(author_row)

        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        box.append(button_box)

        def on_save_clicked(button: Gtk.Button) -> None:
            if self.controller:
                self.controller.update_book_metadata(
                    book.path, title_entry.get_text(), author_entry.get_text()
                )
                self.refresh_grid()
                dialog.close()

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", on_save_clicked)
        button_box.append(save_btn)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: dialog.close())
        button_box.append(cancel_btn)

        dialog.present()
