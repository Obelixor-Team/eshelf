"""Dialog for searching inside PDF book contents."""

from __future__ import annotations

import threading
from typing import Any, List, Optional

import fitz  # PyMuPDF
import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, GLib, Gtk, Pango  # noqa: E402

from src.controller.main_controller import MainController  # noqa: E402
from src.models.book import Book  # noqa: E402


class ContentSearchResult:
    """Represents a single search result inside a book."""

    def __init__(self, book: Book, page_number: int, snippet: str) -> None:
        """Initialize the ContentSearchResult.

        Args:
            book: The book where the match was found.
            page_number: The page number (1-indexed) where the match was found.
            snippet: A text snippet showing the context of the match.
        """
        self.book = book
        self.page_number = page_number
        self.snippet = snippet


class ContentSearchDialog(Adw.Dialog):  # type: ignore
    """Dialog for searching inside book contents."""

    def __init__(
        self,
        parent: Gtk.Window,
        controller: MainController,
        **kwargs: Any,
    ) -> None:
        """Initialize the content search dialog.

        Args:
            parent: The parent window.
            controller: The application controller.
            **kwargs: Additional arguments passed to Adw.Dialog.
        """
        super().__init__(**kwargs)
        self.set_title("Search Inside Books")
        # Set size using size request
        self.set_size_request(600, 400)
        # Set transient for parent window to keep it associated
        # Note: Adw.Dialog may not support set_transient_for directly
        # but we'll try it anyway as it's the standard way in GTK
        try:
            self.set_transient_for(parent)
        except AttributeError:
            # If set_transient_for doesn't exist, we'll skip it
            pass

        self.controller = controller
        self._is_searching = False
        self._search_thread: Optional[threading.Thread] = None
        self._shutdown_event = threading.Event()

        self._build_ui()

    def _build_ui(self) -> None:
        """Build the user interface."""
        # Main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        self.set_child(main_box)

        # Search entry
        search_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text(
            "Enter keyword to search inside books..."
        )
        self.search_entry.connect("activate", self.on_search_activated)
        self.search_button = Gtk.Button(label="Search")
        self.search_button.add_css_class("suggested-action")
        self.search_button.connect("clicked", self.on_search_clicked)
        search_box.append(self.search_entry)
        search_box.append(self.search_button)
        main_box.append(search_box)

        # Progress bar
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_visible(False)
        main_box.append(self.progress_bar)

        # Results list
        self.results_list = Gtk.ListBox()
        self.results_list.set_selection_mode(Gtk.SelectionMode.NONE)
        self.results_list.add_css_class("boxed-list")
        # Make the list box expand
        results_scrolled = Gtk.ScrolledWindow()
        results_scrolled.set_vexpand(True)
        results_scrolled.set_child(self.results_list)
        main_box.append(results_scrolled)
        # Set the results scrolled window to expand
        results_scrolled.set_vexpand(True)

        # Status label
        self.status_label = Gtk.Label(label="")
        self.status_label.set_halign(Gtk.Align.START)
        main_box.append(self.status_label)

    def on_search_activated(self, entry: Gtk.SearchEntry) -> None:
        """Handle Enter key in search entry."""
        self.on_search_clicked(self.search_button)

    def on_search_clicked(self, button: Gtk.Button) -> None:
        """Handle search button click."""
        query = self.search_entry.get_text().strip()
        if not query:
            return

        if self._is_searching:
            self._shutdown_event.set()
            return

        self._start_search(query)

    def _start_search(self, query: str) -> None:
        """Start the search in a background thread."""
        self._is_searching = True
        self._shutdown_event.clear()
        self.search_button.set_label("Cancel")
        self.search_entry.set_sensitive(False)
        self.progress_bar.set_visible(True)
        self.progress_bar.set_fraction(0.0)
        self.status_label.set_text("Preparing to search...")
        self._clear_results()

        # Get all books from the controller
        def worker() -> None:
            try:
                books = self.controller.get_books(
                    category_id=None, limit=10000, offset=0
                )  # Get all books
                total_books = len(books)
                if total_books == 0:
                    GLib.idle_add(
                        self._search_finished, [], "No books found in library."
                    )
                    return

                results: List[ContentSearchResult] = []
                for i, book in enumerate(books):
                    if self._shutdown_event.is_set():
                        break

                    # Update progress
                    fraction = (i + 1) / total_books
                    GLib.idle_add(
                        self._update_progress,
                        fraction,
                        f"Searching... {i + 1}/{total_books}",
                    )

                    # Search in this book
                    book_results = self._search_in_book(book.path, query)
                    results.extend(book_results)

                if not self._shutdown_event.is_set():
                    GLib.idle_add(
                        self._search_finished,
                        results,
                        f"Search completed. Found {len(results)} matches.",
                    )
            except Exception as e:  # pylint: disable=broad-except
                if not self._shutdown_event.is_set():
                    GLib.idle_add(self._search_error, str(e))

        self._search_thread = threading.Thread(target=worker, daemon=True)
        self._search_thread.start()

    def _search_in_book(self, file_path: str, query: str) -> List[ContentSearchResult]:
        """Search for query in a single PDF file."""
        results: List[ContentSearchResult] = []
        try:
            doc = fitz.open(file_path)
            for page_num in range(len(doc)):
                if self._shutdown_event.is_set():
                    break
                page = None
                try:
                    page = doc.load_page(page_num)
                    # Try multiple text extraction methods to avoid font/CSS issues
                    text = ""
                    extraction_methods = [
                        lambda p: p.get_text("text"),  # Plain text - safest
                        lambda p: p.get_text("blocks"),  # Blocks with positioning
                        lambda p: p.get_text("words"),  # Individual words
                        lambda p: p.get_text(),  # Default method
                    ]

                    for method in extraction_methods:
                        try:
                            if page is not None:
                                text = method(page)  # type: ignore
                                if text.strip():  # If we got meaningful text, break
                                    break
                        except Exception as method_error:
                            # Log specific method errors at debug level only
                            if page_num % 20 == 0:  # Less frequent logging
                                print(
                                    f"Text extraction method failed on page "
                                    f"{page_num}: {str(method_error)[:50]}"
                                )
                            continue  # Try next method

                    # Simple case-insensitive search
                    if query.lower() in text.lower():
                        # Extract a snippet around the first match
                        idx = text.lower().find(query.lower())
                        start = max(0, idx - 100)
                        end = min(len(text), idx + len(query) + 100)
                        snippet = text[start:end].replace("\n", " ").strip()
                        results.append(
                            ContentSearchResult(
                                book=Book(
                                    path=file_path,
                                    title="Unknown",  # Replace with real book data
                                    author="Unknown",
                                ),
                                page_number=page_num + 1,
                                snippet=snippet,
                            )
                        )
                except fitz.FileDataError as e:
                    # Handle corrupted page data
                    if page_num % 20 == 0:  # Less frequent logging
                        print(
                            f"Skipping corrupted page {page_num} in {file_path}: "
                            f"{str(e)[:50]}"
                        )
                    continue
                except Exception as page_error:  # pylint: disable=broad-except
                    # Handle font/CSS and other page-specific errors
                    error_msg = str(page_error)
                    # Check if this is a font-related error we can safely ignore
                    if any(
                        font_err in error_msg.lower()
                        for font_err in ["cannot locate font", "font", "css", "styles/"]
                    ):
                        # Silently skip font/CSS errors as they're common and
                        # don't prevent text extraction
                        if page_num % 50 == 0:  # Only log occasionally to avoid spam
                            print(
                                f"Font/CSS issue on page {page_num} in {file_path} "
                                "(common, skipping)"
                            )
                    else:
                        # Log other errors but less frequently
                        if page_num % 20 == 0:
                            print(
                                f"Error processing page {page_num} in {file_path}: "
                                f"{error_msg[:100]}"
                            )
                    # Try to get text despite the error
                    try:
                        if page is not None:
                            # Last resort: try to get any text we can
                            text = page.get_text("text")
                            if query.lower() in text.lower():
                                idx = text.lower().find(query.lower())
                                start = max(0, idx - 100)
                                end = min(len(text), idx + len(query) + 100)
                                snippet = text[start:end].replace("\n", " ").strip()
                                results.append(
                                    ContentSearchResult(
                                        book=Book(
                                            path=file_path,
                                            title="Unknown",
                                            author="Unknown",
                                        ),
                                        page_number=page_num + 1,
                                        snippet=snippet,
                                    )
                                )
                    except Exception:
                        # If even this fails, just skip the page
                        pass
                    continue
            doc.close()
        except fitz.FileDataError as e:
            # Handle corrupted or unreadable PDF files
            print(f"Skipping corrupted/unreadable PDF {file_path}: {str(e)[:100]}")
        except Exception as e:  # pylint: disable=broad-except
            # Log the error but continue with other books
            print(f"Error searching in {file_path}: {str(e)[:100]}")
        return results

    def _update_progress(self, fraction: float, text: str) -> None:
        """Update the progress bar."""
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(text)
        self.progress_bar.set_show_text(True)

    def _search_finished(
        self, results: List[ContentSearchResult], status_text: str
    ) -> None:
        """Handle search completion."""
        self._is_searching = False
        self._shutdown_event.set()
        self.search_button.set_label("Search")
        self.search_entry.set_sensitive(True)
        self.progress_bar.set_visible(False)
        self.status_label.set_text(status_text)
        self._display_results(results)

    def _search_error(self, error_text: str) -> None:
        """Handle search error."""
        self._is_searching = False
        self._shutdown_event.set()
        self.search_button.set_label("Search")
        self.search_entry.set_sensitive(True)
        self.progress_bar.set_visible(False)
        self.status_label.set_text(f"Error: {error_text}")
        self._clear_results()

    def _clear_results(self) -> None:
        """Clear the results list."""
        while child := self.results_list.get_first_child():
            self.results_list.remove(child)

    def _display_results(self, results: List[ContentSearchResult]) -> None:
        """Display search results in the list."""
        self._clear_results()
        if not results:
            label = Gtk.Label(label="No matches found.")
            label.set_halign(Gtk.Align.CENTER)
            label.set_valign(Gtk.Align.CENTER)
            self.results_list.append(label)
            return

        # Get all books to map paths to book objects
        all_books_list = self.controller.get_books(limit=None, offset=0)
        all_books = {book.path: book for book in all_books_list}

        for result in results:
            book = all_books.get(result.book.path)
            if not book:
                continue

            row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            row_box.set_margin_start(12)
            row_box.set_margin_end(12)
            row_box.set_margin_top(6)
            row_box.set_margin_bottom(6)

            title_label = Gtk.Label(
                label=f"{book.title} by {book.author}",
                xalign=0,
                ellipsize=Pango.EllipsizeMode.END,
                max_width_chars=50,
            )
            title_label.add_css_class("title-4")
            page_label = Gtk.Label(
                label=f"Page {result.page_number}", xalign=0, halign=Gtk.Align.START
            )
            page_label.add_css_class("caption")
            snippet_label = Gtk.Label(
                label=result.snippet,
                xalign=0,
                wrap=True,
                ellipsize=Pango.EllipsizeMode.END,
                max_width_chars=80,
            )
            snippet_label.add_css_class("caption")
            snippet_label.set_hexpand(True)

            row_box.append(title_label)
            row_box.append(page_label)
            row_box.append(snippet_label)

            row = Gtk.ListBoxRow()
            row.set_child(row_box)
            # Store the book object in the row for later retrieval
            row.book = book
            self.results_list.append(row)

        # Connect row activation (double-click)
        self.results_list.connect("row-activated", self.on_row_activated)

    def on_row_activated(self, list_box: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        """Handle double-click on a result row."""
        if hasattr(row, "book"):
            book = row.book
            self.controller.open_book(book)
        self.close()
