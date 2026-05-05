"""Dialog for application settings."""

import logging
from typing import Any, Callable, Optional

import gi

from src.config import load_config, save_config

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gtk  # noqa: E402


class SettingsDialog(Adw.PreferencesWindow):  # type: ignore
    """Dialog for application preferences."""

    def __init__(
        self,
        parent: Gtk.Window,
        controller: Any,
        apply_theme_cb: Callable[[str], None],
        on_save_cb: Optional[Callable[[], None]] = None,
    ) -> None:
        """Initialize the settings dialog."""
        super().__init__(transient_for=parent, modal=True)
        self.set_title("Settings")
        self.controller = controller
        self.apply_theme_cb = apply_theme_cb
        self.on_save_cb = on_save_cb
        self.config = load_config()

        page = Adw.PreferencesPage()
        self.set_content(page)

        self._setup_appearance(page)
        self._setup_general(page)
        self._setup_library_dirs(page)
        self._setup_storage(page)
        self._setup_danger_zone(page)

    def _setup_appearance(self, page: Adw.PreferencesPage) -> None:
        """Set up appearance settings."""
        group = Adw.PreferencesGroup(title="Appearance")
        page.add(group)

        appearance_row = Adw.ComboRow(title="Appearance")
        appearance_model = Gtk.StringList.new(["System", "Light", "Dark"])
        appearance_row.set_model(appearance_model)

        current = self.config.get("appearance", "System")
        mapping = {"System": 0, "Light": 1, "Dark": 2}
        appearance_row.set_selected(mapping.get(current, 0))

        def on_appearance_changed(row: Adw.ComboRow, params: Any) -> None:
            selected = row.get_selected_item().get_string()
            self.apply_theme_cb(selected)
            self.config["appearance"] = selected
            save_config(self.config)

        appearance_row.connect("notify::selected", on_appearance_changed)
        group.add(appearance_row)

    def _setup_general(self, page: Adw.PreferencesPage) -> None:
        """Set up all settings groups."""
        # General
        group = Adw.PreferencesGroup(title="General")
        page.add(group)

        self.books_per_line_spin = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(
                value=self.config.get("books_per_line", 6),
                lower=1,
                upper=10,
                step_increment=1,
            )
        )
        row = Adw.ActionRow(title="Books per line")
        row.add_suffix(self.books_per_line_spin)
        group.add(row)

        self.zoom_spin = Gtk.SpinButton(
            adjustment=Gtk.Adjustment(
                value=self.config.get("zoom_level", 1.0),
                lower=0.5,
                upper=3.0,
                step_increment=0.1,
            ),
            digits=1,
        )
        row = Adw.ActionRow(title="Cover zoom")
        row.add_suffix(self.zoom_spin)
        group.add(row)

        self.show_titles_switch = Gtk.Switch(
            active=self.config.get("show_titles", True)
        )
        row = Adw.ActionRow(title="Show Titles")
        row.add_suffix(self.show_titles_switch)
        group.add(row)

    def _setup_library_dirs(self, page: Adw.PreferencesPage) -> None:
        """Set up library directory settings."""
        group = Adw.PreferencesGroup(title="Library Directories")
        page.add(group)
        self.library_rows = []
        for lib_path in self.config.get("library_dirs", []):
            row = self._create_library_row(lib_path, group)
            group.add(row)
            self.library_rows.append(row)

        add_btn = Gtk.Button(label="Add Library", icon_name="list-add-symbolic")
        add_btn.connect("clicked", lambda _: self._on_add_library(group))
        group.add(add_btn)

    def _setup_storage(self, page: Adw.PreferencesPage) -> None:
        """Set up storage settings."""
        group = Adw.PreferencesGroup(title="Storage")
        page.add(group)
        self.cache_entry = Gtk.Entry(text=self.config.get("cache_dir", ""))
        row = Adw.ActionRow(title="Cache directory")
        row.add_suffix(self.cache_entry)
        group.add(row)

    def _setup_danger_zone(self, page: Adw.PreferencesPage) -> None:
        """Set up danger zone."""
        group = Adw.PreferencesGroup(title="Danger Zone")
        page.add(group)

        clear_btn = Gtk.Button(label="Clear Database & Images")
        clear_btn.add_css_class("destructive-action")
        clear_btn.connect("clicked", self._on_clear_library)
        row = Adw.ActionRow(title="Clear Library")
        row.add_suffix(clear_btn)
        group.add(row)

        # Save Button Footer
        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", self._on_save)

        footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        footer_box.set_halign(Gtk.Align.END)
        footer_box.set_margin_top(12)
        footer_box.append(save_btn)

        button_group = Adw.PreferencesGroup()
        button_group.add(footer_box)
        page.add(button_group)

    def _create_library_row(
        self, path: str, group: Adw.PreferencesGroup
    ) -> Adw.ActionRow:
        row = Adw.ActionRow(title=path)
        btn = Gtk.Button(icon_name="user-trash-symbolic")
        btn.add_css_class("flat")
        btn.connect("clicked", lambda _: group.remove(row))
        row.add_suffix(btn)
        return row

    def _on_save(self, btn: Any) -> None:
        print("DEBUG: SettingsDialog _on_save called")
        self.config.update(
            {
                "books_per_line": int(self.books_per_line_spin.get_value()),
                "zoom_level": float(self.zoom_spin.get_value()),
                "library_dirs": [
                    r.get_title() for r in self.library_rows if r.get_parent()
                ],
                "cache_dir": self.cache_entry.get_text(),
                "show_titles": self.show_titles_switch.get_active(),
            }
        )
        save_config(self.config)
        if self.on_save_cb:
            print("DEBUG: Calling on_save_cb")
            self.on_save_cb()
        else:
            print("DEBUG: on_save_cb is None")
        self.close()

    def _on_clear_library(self, btn: Any) -> None:
        self.controller.clear_library()
        self.close()

    def _on_add_library(self, group: Adw.PreferencesGroup) -> None:
        """Handle adding a library folder."""
        dialog = Gtk.FileDialog(title="Select Library Directory")

        def on_response(d: Gtk.FileDialog, result: Any) -> None:
            try:
                folder = d.select_folder_finish(result)
                if folder:
                    path = folder.get_path()
                    if path not in [r.get_title() for r in self.library_rows]:
                        row = self._create_library_row(path, group)
                        group.add(row)
                        self.library_rows.append(row)
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error(f"Error selecting folder: {e}")

        dialog.select_folder(self, None, on_response)
