    def on_import_clicked(self, item: Gtk.Button) -> None:
        """Unified import handler."""
        if not self.controller:
            return

        confirm_dialog = Adw.MessageDialog(
            transient_for=self,
            heading="Import Type",
            body="Do you want to import a file or a folder?",
        )
        confirm_dialog.add_response("file", "File")
        confirm_dialog.add_response("folder", "Folder")
        confirm_dialog.add_response("cancel", "Cancel")

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

        def on_choice(d: Adw.MessageDialog, response: str) -> None:
            if response == "file":
                file_dialog = Gtk.FileDialog(title="Select File to Import")
                file_dialog.set_modal(True)
                file_dialog.open(self, None, on_open_response)
            elif response == "folder":
                folder_dialog = Gtk.FileDialog(title="Select Folder to Import")
                folder_dialog.set_modal(True)
                folder_dialog.select_folder(self, None, on_folder_response)

        confirm_dialog.connect("response", on_choice)
        confirm_dialog.show()
