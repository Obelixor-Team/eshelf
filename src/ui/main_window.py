"""Main window for the eShelf application."""

import logging
import threading
from typing import Any, Callable, List, Optional, Tuple

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gio, GLib, Gtk  # noqa: E402

from src.config import load_config, save_config  # noqa: E402
from src.controller.main_controller import MainController  # noqa: E402
from src.database.repository import BookRepository  # noqa: E402
from src.models.book import Book  # noqa: E402
from src.ui.dialogs.settings_dialog import SettingsDialog  # noqa: E402
from src.ui.shelf_grid import ShelfGrid  # noqa: E402
from src.ui.sidebar import CategoryRow, Sidebar  # noqa: E402


class MainWindow(Adw.ApplicationWindow):  # type: ignore
    """The main window of the eShelf app."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the main window."""
        super().__init__(**kwargs)
        self.set_title("eShelf")
        self.set_default_size(1000, 600)
        self.logger = logging.getLogger(__name__)

        # UI State
        self._is_initializing = False
        self._save_timeout_id: Optional[int] = None
        self._grid_request_id = 0
        self._shutdown_event = threading.Event()
        self._active_threads: List[threading.Thread] = []
        self.controller: Optional[MainController] = None
        self._error_dialog: Optional[Gtk.MessageDialog] = None

        self.connect("close-request", self.on_close_request)

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
            on_book_dropped=self.on_book_dropped,
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

        # Main stack for content and empty state
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.toolbar_view.set_content(self.stack)

        # The grid
        repo: Optional[BookRepository] = None
        self.grid = ShelfGrid(
            repo,  # type: ignore
            self.on_book_selected,
            self.on_book_right_clicked,
        )
        self.stack.add_named(self.grid, "grid")

        # Empty state page
        self.empty_page = Adw.StatusPage()
        self.empty_page.set_title("No Books Found")
        self.empty_page.set_description(
            "Scan your library or import folders to get started."
        )
        self.empty_page.set_icon_name("library-symbolic")

        # Action buttons for empty state
        self.empty_button_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12
        )
        self.empty_button_box.set_halign(Gtk.Align.CENTER)
        self.empty_page.set_child(self.empty_button_box)

        self.empty_scan_button = Gtk.Button(label="Scan Library")
        self.empty_scan_button.add_css_class("suggested-action")
        self.empty_scan_button.add_css_class("pill")
        self.empty_scan_button.connect("clicked", self.on_scan_clicked)
        self.empty_button_box.append(self.empty_scan_button)

        self.empty_clear_search_button = Gtk.Button(label="Clear Search")
        self.empty_clear_search_button.add_css_class("pill")
        self.empty_clear_search_button.connect("clicked", self.on_clear_search_clicked)
        self.empty_clear_search_button.set_visible(False)
        self.empty_button_box.append(self.empty_clear_search_button)

        self.stack.add_named(self.empty_page, "empty")
        self.stack.set_visible_child_name("empty")

        self.sidebar_visible = True

        # Keyboard shortcuts
        self.setup_shortcuts()

    def _start_worker(self, target: Callable[[], None]) -> None:
        """Start a daemon thread and keep track of it for graceful shutdown."""
        thread = threading.Thread(target=target, daemon=True)
        self._active_threads.append(thread)
        thread.start()

        # Empty state page
        self.empty_page = Adw.StatusPage()
        self.empty_page.set_title("No Books Found")
        self.empty_page.set_description(
            "Scan your library or import folders to get started."
        )
        self.empty_page.set_icon_name("library-symbolic")

        # Action buttons for empty state
        self.empty_button_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL, spacing=12
        )
        self.empty_button_box.set_halign(Gtk.Align.CENTER)
        self.empty_page.set_child(self.empty_button_box)

        self.empty_scan_button = Gtk.Button(label="Scan Library")
        self.empty_scan_button.add_css_class("suggested-action")
        self.empty_scan_button.add_css_class("pill")
        self.empty_scan_button.connect("clicked", self.on_scan_clicked)
        self.empty_button_box.append(self.empty_scan_button)

        self.empty_clear_search_button = Gtk.Button(label="Clear Search")
        self.empty_clear_search_button.add_css_class("pill")
        self.empty_clear_search_button.connect("clicked", self.on_clear_search_clicked)
        self.empty_clear_search_button.set_visible(False)
        self.empty_button_box.append(self.empty_clear_search_button)

        self.stack.add_named(self.empty_page, "empty")

        # Keyboard shortcuts
        self.setup_shortcuts()

    def setup_shortcuts(self) -> None:
        """Set up keyboard shortcuts."""
        # Ctrl+F to focus search
        action = Gio.SimpleAction.new("focus_search", None)
        action.connect("activate", lambda *_: self.search_entry.grab_focus())
        self.add_action(action)
        self.set_active_action_shortcut("focus_search", "<Control>f")

    def set_active_action_shortcut(self, action_name: str, shortcut: str) -> None:
        """Set a shortcut for an action."""
        app = self.get_application()
        if app:
            app.set_accels_for_action(f"win.{action_name}", [shortcut])

    def on_clear_search_clicked(self, button: Gtk.Button) -> None:
        """Clear the search entry."""
        self.search_entry.set_text("")

    def apply_theme(self, appearance: str) -> None:
        """Apply the selected appearance theme."""
        style_manager = Adw.StyleManager.get_default()
        if appearance == "Light":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif appearance == "Dark":
            style_manager.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style_manager.set_color_scheme(Adw.ColorScheme.PREFER_LIGHT)

    def set_controller(self, controller: MainController) -> None:
        """Inject the controller and refresh the view."""
        self.controller = controller
        # Re-initialize grid with the repository now that we have a controller
        self.grid.repository = self.controller.repository
        self.grid.update_books()

        # Provide error callback to the controller
        self.controller.error_callback = self.show_error
        # Restore persisted UI state
        self._is_initializing = True
        try:
            config = load_config()

            # Apply theme
            self.apply_theme(config.get("appearance", "System"))

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
            self._grid_request_id += 1
            initial_request_id = self._grid_request_id

            def worker() -> None:
                books = self._fetch_books(category_id, all_books, None, last_sort)
                GLib.idle_add(self._apply_grid_update, books, initial_request_id)

            threading.Thread(target=worker, daemon=True).start()
        finally:
            self._is_initializing = False

    def show_error(self, message: str) -> None:
        """Show an error message dialog."""

        def _show_error_on_main_thread() -> bool:
            if not self.get_visible():
                return False

            if self._error_dialog:
                # Append to existing dialog if it's already showing
                current_text = self._error_dialog.get_property("body")
                if message not in (current_text or ""):
                    new_text = f"{(current_text or '')}\n{message}"
                    self._error_dialog.set_property("body", new_text)
                self._error_dialog.present()
                return False

            self._error_dialog = Adw.AlertDialog(
                heading="Error",
                body=message,
            )
            self._error_dialog.add_response("ok", "OK")
            self._error_dialog.set_default_response("ok")
            self._error_dialog.set_close_response("ok")

            def on_response(dialog: Adw.AlertDialog, result: Any) -> None:
                dialog.choose_finish(result)
                self._error_dialog = None

            self._error_dialog.choose(self, None, on_response)
            return False

        GLib.idle_add(_show_error_on_main_thread)

    def show_toast(self, message: str) -> None:
        """Show a toast notification."""

        def _show() -> bool:
            if not self.get_visible():
                return False
            toast = Adw.Toast()
            toast.set_title(message)
            self.toast_overlay.add_toast(toast)
            return False

        GLib.idle_add(_show)

    def on_close_request(self, window: Adw.ApplicationWindow) -> bool:
        """Ensure UI state is saved and threads are shut down before closing."""
        self._shutdown_event.set()
        # Join threads briefly to let them clean up
        for thread in self._active_threads:
            if thread.is_alive():
                thread.join(timeout=1.0)
        self.save_ui_state()
        return False

    def request_save_ui_state(self) -> None:
        """Request a debounced save of the UI state."""
        if self._save_timeout_id is not None:
            GLib.source_remove(self._save_timeout_id)
        self._save_timeout_id = GLib.timeout_add(1000, self.save_ui_state)

    def save_ui_state(self) -> bool:
        """Save current UI state to configuration."""
        self._save_timeout_id = None
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
        return False

    def refresh_sidebar(self) -> None:
        """Update the sidebar with current categories."""
        if self.controller:
            categories = self.controller.get_categories()
            self.sidebar.update_categories(categories)

    def _fetch_books(
        self,
        category_id: Optional[int] = None,
        all_books: bool = True,
        search_text: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> List[Book]:
        """Fetch and sort books from the controller."""
        if not self.controller:
            return []
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
        return books

    def _apply_grid_update(self, books: List[Book], request_id: int) -> None:
        """Update the grid if the request is still current."""
        if not self.get_visible():
            return
        if request_id == self._grid_request_id:
            # We don't use this for lazy loading anymore,
            # so we just check for empty state.
            if not books:
                self.stack.set_visible_child_name("empty")
            else:
                self.stack.set_visible_child_name("grid")

    def refresh_grid(
        self,
        category_id: Optional[int] = None,
        all_books: bool = True,
        search_text: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> None:
        """Update the grid with books from the controller."""
        config = load_config()
        self.grid.update_config(config)

        self._grid_request_id += 1
        # Virtual scrolling implies we don't need to fetch a list of books upfront
        # Update category view based on model
        self.grid.update_books(
            category_id, all_books=all_books, search_query=search_text
        )

        # Check total library count for the "real" empty state
        total_library_books = 0
        if self.controller:
            total_library_books = self.controller.repository.get_book_count(
                all_books=True
            )

        if total_library_books == 0:
            # Library is completely empty
            self.stack.set_visible_child_name("empty")
            self.empty_page.set_title("No Books Found")
            self.empty_page.set_description(
                "Scan your library or import folders to get started."
            )
            self.empty_scan_button.set_visible(True)
            self.empty_clear_search_button.set_visible(False)
        elif self.grid.model.do_get_n_items() == 0:
            # Current filter has no results
            self.stack.set_visible_child_name("empty")
            if search_text:
                self.empty_page.set_title("No Results Found")
                self.empty_page.set_description(f'No books matching "{search_text}"')
                self.empty_scan_button.set_visible(False)
                self.empty_clear_search_button.set_visible(True)
            else:
                # Category or Uncategorized is empty
                self.empty_page.set_title("No Books")
                self.empty_page.set_description("This category is currently empty.")
                self.empty_scan_button.set_visible(False)
                self.empty_clear_search_button.set_visible(False)
        else:
            # We have books to show
            self.stack.set_visible_child_name("grid")

    def on_category_selected(self, category_id: Optional[int], all_books: bool) -> None:
        """Handle category selection from sidebar."""
        if self._is_initializing:
            return
        self.refresh_grid(category_id, all_books)
        self.request_save_ui_state()

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

    def on_book_dropped(self, book_path: str, category_id: Optional[int]) -> None:
        """Handle book dropped on a category."""
        if self.controller:
            # We move only the dropped book, or should we move the whole selection?
            # Standard behavior is usually moving the dropped item(s).
            # If the dropped item is part of the selection, move the whole selection.
            selected_books = self.grid.get_selected_books()
            paths = [b.path for b in selected_books]

            if book_path in paths:
                # Move all selected books
                for path in paths:
                    self.controller.move_book_to_category(path, category_id)
            else:
                # Move only the dropped book
                self.controller.move_book_to_category(book_path, category_id)

            self.refresh_grid()

    def on_sidebar_toggle_clicked(self, button: Gtk.Button) -> None:
        """Toggle sidebar visibility."""
        if self.sidebar.get_visible():
            self.sidebar.set_visible(False)
            self.sidebar_toggle.set_icon_name("sidebar-show-symbolic")
        else:
            self.sidebar.set_visible(True)
            self.sidebar_toggle.set_icon_name("sidebar-collapse-symbolic")
        self.request_save_ui_state()

    def on_import_clicked(self, item: Gtk.Button) -> None:
        """Unified import handler."""
        if not self.controller:
            return

        confirm_dialog = Adw.AlertDialog(
            heading="Import Type",
            body="Do you want to import a file or a folder?",
        )
        confirm_dialog.add_response("file", "File")
        confirm_dialog.add_response("folder", "Folder")
        confirm_dialog.add_response("cancel", "Cancel")

        def on_choice(d: Adw.AlertDialog, result: Any) -> None:
            response = d.choose_finish(result)

            def show_picker() -> bool:
                if response == "file":
                    file_dialog = Gtk.FileDialog(title="Select File to Import")
                    file_dialog.set_modal(True)

                    def on_open_response(dialog: Gtk.FileDialog, result: Any) -> None:
                        try:
                            file = dialog.open_finish(result)
                            if file and self.controller:
                                path = file.get_path()
                                self.show_category_dialog(path)
                        except Exception as e:
                            self.show_error(f"Error selecting file: {e}")

                    file_dialog.open(self, None, on_open_response)

                elif response == "folder":
                    folder_dialog = Gtk.FileDialog(title="Select Folder to Import")
                    folder_dialog.set_modal(True)

                    def on_folder_response(dialog: Gtk.FileDialog, result: Any) -> None:
                        try:
                            folder = dialog.select_folder_finish(result)
                            if folder and self.controller:
                                path = folder.get_path()
                                self.show_category_dialog(path)
                        except Exception as e:
                            self.show_error(f"Error selecting folder: {e}")

                    folder_dialog.select_folder(self, None, on_folder_response)
                return False

            GLib.idle_add(show_picker)

        confirm_dialog.choose(self, None, on_choice)

    def _on_import_finished_internal(
        self, result: Optional[Tuple[int, int, List[str]]]
    ) -> bool:
        """Handle import completion."""
        if not self.get_visible():
            return False
        self.import_item.set_sensitive(True)
        self.hide_progress_bar()
        if result:
            added, updated, failed = result
            self.refresh_grid()
            msg = f"Imported: {added} added, {updated} updated, {len(failed)} failed."
            self.show_toast(msg)
        return False

    def _on_import_error_internal(self, e: Exception) -> bool:
        """Handle import error."""
        if not self.get_visible():
            return False
        self.import_item.set_sensitive(True)
        self.hide_progress_bar()
        self.show_error(f"Error: {e}")
        return False

    def show_category_dialog(self, path: str) -> None:
        """Show dialog to select a category for the import."""
        dialog = Gtk.Dialog(title="Select Category", transient_for=self, modal=True)
        content_area = dialog.get_content_area()

        # Category selection
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)
        content_area.append(box)

        label = Gtk.Label(label="Select or create a category:")
        box.append(label)

        combo = Gtk.ComboBoxText()
        combo.append("None", "Uncategorized")

        def refresh_combo() -> None:
            if not self.controller:
                return
            combo.remove_all()
            combo.append("None", "Uncategorized")
            for cat in self.controller.get_categories():
                combo.append(str(cat.id), cat.name)
            combo.set_active_id("None")

        refresh_combo()
        box.append(combo)

        # New category entry
        new_cat_entry = Gtk.Entry(placeholder_text="New category name")
        box.append(new_cat_entry)

        # Recursive option
        recursive_check = Gtk.CheckButton(label="Include subfolders")
        recursive_check.set_active(True)
        box.append(recursive_check)

        add_cat_btn = Gtk.Button(label="Add Category")

        def on_add_category_clicked(button: Gtk.Button) -> None:
            name = new_cat_entry.get_text()
            if name and self.controller:
                try:
                    self.controller.create_category(name)
                    new_cat_entry.set_text("")
                    refresh_combo()
                    self.refresh_sidebar()
                except Exception as e:
                    self.show_error(f"Error creating category: {e}")

        add_cat_btn.connect("clicked", on_add_category_clicked)
        box.append(add_cat_btn)

        # Import button
        import_btn = Gtk.Button(label="Import")
        import_btn.add_css_class("suggested-action")
        box.append(import_btn)

        def on_import_clicked_internal(button: Gtk.Button) -> None:
            cat_id = combo.get_active_id()
            c_id = int(cat_id) if cat_id != "None" else None

            self.import_item.set_sensitive(False)

            def progress_callback(current: int, total: int) -> None:
                GLib.idle_add(self.update_progress, current, total)

            def worker() -> None:
                if not self.controller:
                    GLib.idle_add(self._on_import_finished_internal, None)
                    return
                try:
                    GLib.idle_add(self.show_progress_bar)
                    added, updated, failed = self.controller.import_path(
                        path,
                        c_id,
                        progress_callback=progress_callback,
                        recursive=recursive_check.get_active(),
                    )
                    GLib.idle_add(
                        self._on_import_finished_internal, (added, updated, failed)
                    )
                except Exception as e:
                    GLib.idle_add(self._on_import_error_internal, e)

            threading.Thread(target=worker, daemon=True).start()
            dialog.destroy()

        import_btn.connect("clicked", on_import_clicked_internal)

        dialog.present()

    def show_progress_bar(self) -> None:
        """Show and reset the progress bar."""
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0.0)

    def hide_progress_bar(self) -> None:
        """Hide the progress bar."""
        self.progress_bar.set_visible(False)

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
                if not self._shutdown_event.is_set():
                    GLib.idle_add(self.on_scan_finished, added, updated, failed)

        self._start_worker(scan_worker)

    def update_progress(self, current: int, total: int) -> bool:
        """Update progress bar fraction."""
        if not self.get_visible():
            return False
        fraction = current / total
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"Scanning... {current}/{total}")
        self.progress_bar.set_show_text(True)
        return False

    def on_scan_finished(self, added: int, updated: int, failed: List[str]) -> bool:
        """Handle completion of the scan process."""
        if not self.get_visible():
            return False
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
        self.request_save_ui_state()

    def on_cleanup_clicked(self, button: Gtk.Button) -> None:
        """Handle the cleanup button click."""
        controller = self.controller
        if not controller:
            return

        self.cleanup_item.set_sensitive(False)

        def worker() -> None:
            try:
                removed = controller.cleanup_library()
                if not self._shutdown_event.is_set():
                    GLib.idle_add(self._on_cleanup_finished, removed)
            except Exception as e:
                if not self._shutdown_event.is_set():
                    GLib.idle_add(self._on_cleanup_error, e)

        self._start_worker(worker)

    def _on_cleanup_finished(self, removed: int) -> bool:
        """Handle cleanup completion."""
        if not self.get_visible():
            return False
        self.cleanup_item.set_sensitive(True)
        self.refresh_grid()
        self.show_toast(f"Cleanup complete: {removed} books removed.")
        return False

    def _on_cleanup_error(self, e: Exception) -> bool:
        """Handle cleanup error."""
        if not self.get_visible():
            return False
        self.cleanup_item.set_sensitive(True)
        self.show_error(f"Error during cleanup: {e}")
        return False

    def on_settings_clicked(self, button: Gtk.Button) -> None:
        """Handle the settings button click."""
        dialog = SettingsDialog(
            self, self.controller, self.apply_theme, on_save_cb=self.refresh_grid
        )
        dialog.present()

    def on_book_selected(self, book: Book) -> None:
        """Handle book selection."""
        if self.controller:
            self.controller.open_book(book)

    def on_book_right_clicked(self, widget: Gtk.Widget, book: Book) -> None:
        """Handle book right-click to move to category or edit metadata."""
        if not self.controller:
            return

        # Get selected books
        selected_books = self.grid.get_selected_books()

        # If the right-clicked book is not in selection, select only it
        if book not in selected_books:
            # For now, use the single book if selection doesn't contain it
            selected_books = [book]

        # Create a popover for actions
        popover = Gtk.Popover()
        popover.set_parent(widget)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)
        popover.set_child(box)

        # Action for multiple books
        count = len(selected_books)
        label_suffix = f" ({count} books)" if count > 1 else ""

        # Open action
        # Open action
        open_btn = Gtk.Button(label=f"Open{label_suffix}")

        def on_open_clicked(_: Gtk.Button) -> None:
            for b in selected_books:
                self.on_book_selected(b)
            popover.popdown()

        open_btn.connect("clicked", on_open_clicked)
        box.append(open_btn)

        # Edit metadata action (only if one book)
        if count == 1:
            edit_btn = Gtk.Button(label="Edit Metadata")
            edit_btn.connect(
                "clicked", lambda _: self.on_edit_metadata_clicked(book, popover)
            )
            box.append(edit_btn)

        # Separator
        separator = Gtk.Separator()
        box.append(separator)

        # "Uncategorized" option
        uncat_btn = Gtk.Button(label=f"Move to Uncategorized{label_suffix}")
        uncat_btn.connect(
            "clicked", lambda _: self.move_books(selected_books, None, popover)
        )
        box.append(uncat_btn)

        # Category DropDown
        categories = self.controller.get_categories()
        cat_names = ["None"] + [cat.name for cat in categories]
        cat_map = {cat.name: cat.id for cat in categories}

        model = Gtk.StringList.new(cat_names)
        dropdown = Gtk.DropDown.new(model, None)
        dropdown.set_valign(Gtk.Align.CENTER)

        # Pre-select category if all selected books belong to the same one
        first_cat = selected_books[0].category_id
        if all(b.category_id == first_cat for b in selected_books) and first_cat:
            cat_name = None
            for cat in categories:
                if cat.id == first_cat:
                    cat_name = cat.name
                    break
            if cat_name and cat_name in cat_names:
                dropdown.set_selected(cat_names.index(cat_name))

        def on_category_changed(obj: Gtk.DropDown, *args: Any) -> None:
            selected_item = obj.get_selected_item()
            if not selected_item:
                return
            name = selected_item.get_string()
            if name == "None":
                return
            c_id = cat_map.get(name)
            self.move_books(selected_books, c_id, popover)

        dropdown.connect("notify::selected", on_category_changed)
        box.append(dropdown)

        popover.popup()

    def move_books(
        self,
        books: List[Book],
        category_id: Optional[int],
        popover: Optional[Gtk.Popover] = None,
    ) -> None:
        """Move multiple books to a category and refresh view."""
        if self.controller:
            for book in books:
                self.controller.move_book_to_category(book.path, category_id)
            self.refresh_grid()
            if popover:
                popover.popdown()

    def move_book(
        self,
        book: Book,
        category_id: Optional[int],
        popover: Optional[Gtk.Popover] = None,
    ) -> None:
        """Move a book to a category and refresh view."""
        self.move_books([book], category_id, popover)

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
