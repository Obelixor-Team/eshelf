## FILE: AGENTS.md

```md
# Agents Guide: eshelf

## Developer Commands
- `make run`: Run the application (`src/main.py`)
- `make test`: Run tests with coverage (min 80% required)
- `make lint`: Ruff check (with `--fix`) and format
- `make typecheck`: Mypy strict type checking
- `make pre-commit`: Run all pre-commit hooks
- `make clean`: Clean cache files

## Toolchain & Conventions
- **Package Manager**: `uv`
- **Linting/Formatting**: `ruff` using Google docstring convention
- **Type Checking**: `mypy` in strict mode
- **Commits**: Conventional Commits via `commitizen`
- **Formatting**: Use Unicode characters instead of LaTeX for symbols (e.g., use → instead of $\rightarrow$)

## Architecture
- **Entry point**: `src/main.py`
- **Layers**: `ui` → `controller` → `services` → `database`/`models`
- **Source**: `src/`
- **Tests**: `tests/` (mirrors `src/` structure)

## Verification Workflow
Run in order: `make lint` → `make typecheck` → `make test`

```

## FILE: src/config.py

```py
"""Configuration management for eShelf."""

import json
import os
from typing import Any

CONFIG_FILE = os.path.expanduser("~/.config/eshelf/config.json")

DEFAULT_CONFIG = {
    "books_per_line": 6,
    "zoom_level": 1.0,
    "cache_dir": os.path.join(os.path.expanduser("~"), ".cache", "eshelf", "covers"),
}


def load_config() -> dict[str, Any]:
    """Load configuration from file or return defaults."""
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()

    try:
        with open(CONFIG_FILE, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except (json.JSONDecodeError, IOError):
        return DEFAULT_CONFIG.copy()


def save_config(config: dict[str, Any]) -> None:
    """Save configuration to file."""
    # Validate configuration values
    books_per_line = config.get("books_per_line")
    if not isinstance(books_per_line, int) or books_per_line < 1:
        raise ValueError("books_per_line must be a positive integer")

    zoom_level = config.get("zoom_level")
    if not isinstance(zoom_level, (int, float)) or zoom_level < 0.1:
        raise ValueError("zoom_level must be a positive number >= 0.1")

    cache_dir = config.get("cache_dir")
    if not isinstance(cache_dir, str):
        raise ValueError("cache_dir must be a string")

    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

```

## FILE: src/controller/__init__.py

```py
"""Controller package."""

```

## FILE: src/controller/main_controller.py

```py
"""Controller to coordinate between the UI and the backend services."""

import subprocess
from pathlib import Path
from typing import Callable, List, Optional

from src.database.repository import BookRepository
from src.models.book import Book
from src.models.category import Category
from src.services.extractor import CoverExtractor
from src.services.scanner import BookScanner


class MainController:
    """Coordinates book scanning, persistence, and UI updates."""

    def __init__(
        self,
        library_dir: str,
        db_path: str,
        cache_dir: str,
        error_callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize the controller.

        Args:
            library_dir (str): Directory where books are stored.
            db_path (str): Path to the SQLite database.
            cache_dir (str): Path to the thumbnail cache.
            error_callback (callable, optional): Callback to report errors to the UI.
        """
        self.library_dir = library_dir
        self.repository = BookRepository(db_path)
        self.extractor = CoverExtractor(cache_dir)
        self.scanner = BookScanner(self.repository, self.extractor)
        self.error_callback = error_callback

    def get_books(self, category_id: Optional[int] = None) -> List[Book]:
        """Retrieve books from the repository, optionally filtered by category.

        If category_id is None, retrieve all books.
        """
        if category_id is not None:
            return self.repository.get_books_by_category(category_id)
        return self.repository.get_all_books()

    def get_uncategorized_books(self) -> List[Book]:
        """Retrieve books that have no category assigned."""
        return self.repository.get_books_by_category(None)

    def get_categories(self) -> List[Category]:
        """Retrieve all categories."""
        return self.repository.get_all_categories()

    def create_category(self, name: str) -> int:
        """Create a new category."""
        return self.repository.create_category(name)

    def delete_category(self, category_id: int) -> None:
        """Delete a category."""
        self.repository.delete_category(category_id)

    def move_book_to_category(self, book_path: str, category_id: Optional[int]) -> None:
        """Move a book to a specific category."""
        self.repository.update_book_category(book_path, category_id)

    def scan_library(
        self, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> tuple[int, int]:
        """Scan the library for books and return (added, updated) counts."""
        return self.scanner.scan(self.library_dir, progress_callback=progress_callback)

    def import_folder(
        self,
        folder_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> tuple[int, int]:
        """Import books from a specific folder."""
        return self.scanner.scan(folder_path, progress_callback=progress_callback)

    def import_file(self, file_path: str) -> bool:
        """Import a single book file."""
        path = Path(file_path)
        if path.suffix.lower() not in (".pdf", ".epub"):
            return False

        title = path.stem
        author = "Unknown Author"
        cover_path = self.extractor.extract(file_path)

        book = Book(
            path=str(path.absolute()),
            title=title,
            author=author,
            cover_path=cover_path,
        )
        self.repository.add_book(book)
        return True

    def cleanup_library(self) -> int:
        """Remove missing books and return count of removed books."""
        return self.scanner.cleanup_missing(self.library_dir)

    def open_book(self, book: Book) -> None:
        """Open a book using the system's default application."""
        try:
            subprocess.run(["xdg-open", book.path], check=True)
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to open book {book.path}: {e}"
            if self.error_callback:
                self.error_callback(error_msg)
            else:
                print(error_msg)

```

## FILE: src/database/__init__.py

```py
"""Database package."""

```

## FILE: src/database/repository.py

```py
"""Repository for managing book metadata in a SQLite database."""

import sqlite3
from typing import List, Optional

from src.models.book import Book
from src.models.category import Category


class BookRepository:
    """Handles persistence of book metadata using SQLite."""

    def __init__(self, db_path: str):
        """Initialize the repository.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        """Create the categories and books tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    cover_path TEXT,
                    category_id INTEGER,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                    ON DELETE SET NULL
                )
                """
            )
            conn.commit()

    def add_book(self, book: Book) -> None:
        """Add or update a book in the database."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO books (path, title, author, cover_path, category_id)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    title = excluded.title,
                    author = excluded.author,
                    cover_path = excluded.cover_path,
                    category_id = COALESCE(excluded.category_id, books.category_id)
                """,
                (book.path, book.title, book.author, book.cover_path, book.category_id),
            )
            conn.commit()

    def get_all_books(self) -> List[Book]:
        """Retrieve all books from the database."""
        with self._get_connection() as conn:
            query = "SELECT path, title, author, cover_path, category_id FROM books"
            cursor = conn.execute(query)
            return [
                Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                )
                for row in cursor.fetchall()
            ]

    def get_book_by_path(self, path: str) -> Optional[Book]:
        """Find a book by its file path."""
        with self._get_connection() as conn:
            query = (
                "SELECT path, title, author, cover_path, category_id "
                "FROM books WHERE path = ?"
            )
            cursor = conn.execute(query, (path,))
            row = cursor.fetchone()
            if row:
                return Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                )
            return None

    def remove_book(self, path: str) -> None:
        """Remove a book from the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM books WHERE path = ?", (path,))
            conn.commit()

    def update_book_category(self, path: str, category_id: Optional[int]) -> None:
        """Update the category of a book."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE books SET category_id = ? WHERE path = ?",
                (category_id, path),
            )
            conn.commit()

    def create_category(self, name: str) -> int:
        """Create a new category and return its ID."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "INSERT INTO categories (name) VALUES (?)",
                (name,),
            )
            conn.commit()
            last_id = cursor.lastrowid
            if last_id is None:
                raise RuntimeError("Failed to create category: no ID returned")
            return last_id

    def delete_category(self, category_id: int) -> None:
        """Delete a category."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()

    def get_all_categories(self) -> List[Category]:
        """Retrieve all categories from the database."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id, name FROM categories ORDER BY name")
            return [Category(id=row[0], name=row[1]) for row in cursor.fetchall()]

    def get_books_by_category(self, category_id: Optional[int]) -> List[Book]:
        """Retrieve books belonging to a specific category."""
        with self._get_connection() as conn:
            if category_id is None:
                query = (
                    "SELECT path, title, author, cover_path, category_id "
                    "FROM books WHERE category_id IS NULL"
                )
                cursor = conn.execute(query)
            else:
                query = (
                    "SELECT path, title, author, cover_path, category_id "
                    "FROM books WHERE category_id = ?"
                )
                cursor = conn.execute(query, (category_id,))
            return [
                Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                )
                for row in cursor.fetchall()
            ]

    def clear(self) -> None:
        """Remove all books from the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM books")
            conn.commit()

```

## FILE: src/main.py

```py
"""Entry point for the eShelf application."""

import os
import sys
from typing import Any

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw  # noqa: E402

from src.config import DEFAULT_CONFIG, load_config  # noqa: E402
from src.controller.main_controller import MainController  # noqa: E402
from src.ui.main_window import MainWindow  # noqa: E402


def main() -> None:
    """Initialize and run the eShelf application."""
    config = load_config()
    home = os.path.expanduser("~")
    library_dir = os.path.join(home, "Documents", "Books")
    db_path = os.path.join(home, ".local/share/eshelf/library.db")
    cache_dir = str(config.get("cache_dir") or DEFAULT_CONFIG["cache_dir"])

    # Ensure directories exist
    os.makedirs(os.path.dirname(db_path) if db_path else ".", exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(library_dir, exist_ok=True)

    # Initialize Backend
    controller = MainController(library_dir, db_path, cache_dir)

    # Initialize UI
    app = Adw.Application(application_id="ai.opencode.eshelf")

    def on_activate(app: Any) -> None:
        win = MainWindow(application=app)
        win.set_controller(controller)
        win.present()

    app.connect("activate", on_activate)
    app.run(sys.argv)


if __name__ == "__main__":
    main()

```

## FILE: src/models/__init__.py

```py
"""Models package."""

```

## FILE: src/models/book.py

```py
"""Book model for storing book metadata."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Book:
    """Represents a book in the library.

    Attributes:
        path (str): Path to the book file.
        title (str): Title of the book.
        author (str): Author of the book.
        cover_path (Optional[str]): Path to the extracted cover image.
        category_id (Optional[int]): ID of the category the book belongs to.
    """

    path: str
    title: str
    author: str
    cover_path: Optional[str] = None
    category_id: Optional[int] = None

```

## FILE: src/models/category.py

```py
"""Category model for organizing books."""

from dataclasses import dataclass


@dataclass
class Category:
    """Represents a bookshelf category.

    Attributes:
        id (int): Unique identifier for the category.
        name (str): Name of the category.
    """

    id: int
    name: str

```

## FILE: src/services/__init__.py

```py
"""Services package."""

```

## FILE: src/services/extractor.py

```py
"""Service for extracting book covers from PDF and EPUB files."""

from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub
from pdf2image import convert_from_path


class CoverExtractor:
    """Extracts thumbnails from digital book formats."""

    def __init__(self, cache_dir: str):
        """Initialize the extractor.

        Args:
            cache_dir (str): Directory where extracted covers are stored.
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, file_path: str) -> Optional[str]:
        """Extract a cover image from a file and save it to the cache.

        Args:
            file_path (str): Path to the book file.

        Returns:
            Optional[str]: Path to the saved cover image, or None if extraction failed.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            return self._extract_pdf(path)
        elif ext == ".epub":
            return self._extract_epub(path)

        return None

    def _extract_pdf(self, path: Path) -> Optional[str]:
        """Extract the first page of a PDF as a cover image."""
        try:
            # Convert only the first page to an image
            images = convert_from_path(path, first_page=1, last_page=1)
            if not images:
                return None

            cover_image = images[0]
            output_path = self._get_output_path(path)
            cover_image.save(output_path, "PNG")
            return str(output_path)
        except Exception as e:
            print(f"Error extracting PDF cover from {path}: {e}")
            return None

    def _extract_epub(self, path: Path) -> Optional[str]:
        """Extract the cover image from an EPUB file."""
        try:
            book = epub.read_epub(path)
            # EPUBs usually define the cover in the metadata
            cover_id_meta = book.get_metadata("cover")
            cover_item = None
            if cover_id_meta:
                cover_item = book.get_item_with_id(cover_id_meta[0][0])

            if not cover_item:
                # Fallback: search for common cover image names
                for item in book.get_items():
                    if (
                        item.get_type() == ebooklib.ITEM_IMAGE
                        and "cover" in item.get_name().lower()
                    ):
                        cover_item = item
                        break

            if not cover_item:
                return None

            output_path = self._get_output_path(path)
            with open(output_path, "wb") as f:
                f.write(cover_item.get_content())

            return str(output_path)
        except Exception as e:
            print(f"Error extracting EPUB cover from {path}: {e}")
            return None

    def _get_output_path(self, path: Path) -> Path:
        """Generate a unique output path for the cover image based on the file path."""
        # Use a simple hash or just the filename to avoid issues with special characters
        import hashlib

        file_hash = hashlib.sha256(str(path.absolute()).encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.png"

```

## FILE: src/services/scanner.py

```py
"""Service for scanning directories for books and updating the library."""

from pathlib import Path
from typing import Callable, Optional, Tuple

from src.database.repository import BookRepository
from src.models.book import Book
from src.services.extractor import CoverExtractor


class BookScanner:
    """Scans directories for PDF and EPUB files and updates the repository."""

    def __init__(self, repository: BookRepository, extractor: CoverExtractor):
        """Initialize the scanner.

        Args:
            repository (BookRepository): The repository to persist book metadata.
            extractor (CoverExtractor): The extractor to generate cover images.
        """
        self.repository = repository
        self.extractor = extractor

    def scan(
        self,
        directory: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[int, int]:
        """Scan a directory for books and update the repository.

        Args:
            directory (str): The directory path to scan.
            progress_callback (callable, optional): Callback for progress updates.

        Returns:
            Tuple[int, int]: A tuple containing (added_count, updated_count).
        """
        added = 0
        updated = 0

        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ValueError(f"Provided path is not a directory: {directory}")

        # Find all supported files first to determine total count
        all_files = [
            f for f in dir_path.rglob("*") if f.suffix.lower() in (".pdf", ".epub")
        ]
        total_files = len(all_files)

        # Scan for supported files
        for index, file in enumerate(all_files, 1):
            if progress_callback:
                progress_callback(index, total_files)

            file_path = str(file.absolute())

            # Basic metadata extraction (filename as title)
            # In a real app, we'd use a library to get actual metadata from the file
            title = file.stem
            author = "Unknown Author"

            # Check if book already exists
            existing_book = self.repository.get_book_by_path(file_path)

            # Extract cover only if necessary
            cover_path = None
            if (
                existing_book
                and existing_book.cover_path
                and Path(existing_book.cover_path).exists()
            ):
                cover_path = existing_book.cover_path
            else:
                cover_path = self.extractor.extract(file_path)

            if existing_book:
                if (
                    existing_book.title != title
                    or existing_book.author != author
                    or existing_book.cover_path != cover_path
                ):
                    book = Book(
                        path=file_path,
                        title=title,
                        author=author,
                        cover_path=cover_path,
                        category_id=existing_book.category_id,
                    )
                    self.repository.add_book(book)
                    updated += 1
            else:
                book = Book(
                    path=file_path,
                    title=title,
                    author=author,
                    cover_path=cover_path,
                )
                self.repository.add_book(book)
                added += 1

        return added, updated

    def cleanup_missing(self, directory: str) -> int:
        """Remove books from the repository that no longer exist on disk.

        Args:
            directory (str): The directory path to verify against.

        Returns:
            int: Number of books removed.
        """
        removed = 0
        all_books = self.repository.get_all_books()

        for book in all_books:
            if book.path.startswith(directory) and not Path(book.path).exists():
                self.repository.remove_book(book.path)
                removed += 1

        return removed

```

## FILE: src/ui/__init__.py

```py
"""UI package."""

```

## FILE: src/ui/book_widget.py

```py
"""UI component representing a single book on the shelf."""

from typing import Callable, Optional

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gdk, Gtk, Pango  # noqa: E402

from src.models.book import Book  # noqa: E402


class BookWidget(Gtk.Box):  # type: ignore
    """A widget that displays a book's cover and title."""

    def __init__(
        self,
        book: Book,
        on_click_callback: Callable[[Book], None],
        zoom_level: float = 1.0,
        on_right_click_callback: Optional[Callable[[Gtk.Widget, Book], None]] = None,
    ) -> None:
        """Initialize the BookWidget.

        Args:
            book (Book): The book to display.
            on_click_callback (callable): Callback function when the book is clicked.
            zoom_level (float): Zoom factor for the cover size.
            on_right_click_callback (callable): Callback function when the book is
                right-clicked.
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.on_right_click_callback = on_right_click_callback

        width = int(120 * zoom_level)
        height = int(180 * zoom_level)

        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_hexpand(False)
        self.set_vexpand(False)
        self.set_size_request(width, -1)
        self.book = book

        # Cover image
        image = Gtk.Picture()
        image.set_size_request(width, height)
        image.set_halign(Gtk.Align.CENTER)
        image.set_valign(Gtk.Align.CENTER)
        image.set_content_fit(Gtk.ContentFit.CONTAIN)
        if book.cover_path:
            try:
                texture = Gdk.Texture.new_from_filename(book.cover_path)
                image.set_paintable(texture)
            except Exception as e:
                print(f"Error loading cover image: {e}")

        self.append(image)

        # Title label
        label = Gtk.Label(label=book.title)
        label.set_ellipsize(Pango.EllipsizeMode.END)
        label.set_max_width_chars(15)
        label.set_width_chars(15)
        label.set_wrap(True)
        label.set_wrap_mode(Pango.WrapMode.WORD_CHAR)
        label.set_justify(Gtk.Justification.CENTER)
        label.set_halign(Gtk.Align.CENTER)
        self.append(label)

        # Click gestures
        click_gesture = Gtk.GestureClick()
        click_gesture.set_button(1)  # Left click
        click_gesture.connect("released", self._on_clicked, on_click_callback)
        self.add_controller(click_gesture)

        if self.on_right_click_callback:
            right_click_gesture = Gtk.GestureClick()
            right_click_gesture.set_button(3)  # Right click
            right_click_gesture.connect("released", self.on_right_clicked)
            self.add_controller(right_click_gesture)

    def _on_clicked(
        self,
        gesture: Gtk.GestureClick,
        n_press: int,
        x: float,
        y: float,
        callback: Callable[[Book], None],
    ) -> None:
        """Handle book click. Only open on double click."""
        if n_press == 2:
            callback(self.book)

    def on_right_clicked(
        self,
        gesture: Gtk.GestureClick,
        n_press: int,
        x: float,
        y: float,
    ) -> None:
        """Handle right click to show context menu."""
        if self.on_right_click_callback:
            self.on_right_click_callback(self, self.book)

```

## FILE: src/ui/main_window.py

```py
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
        # Provide error callback to the controller
        self.controller.error_callback = self.show_error
        self.refresh_grid()
        self.refresh_sidebar()

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
            self.refresh_grid(None, True)

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

        dialog = Adw.Dialog(title="Settings", modal=True)
        dialog.set_transient_for(self)
        dialog.set_default_size(400, 300)

        # Main container for the dialog content
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        dialog.set_child(main_box)

        # Preferences content in a scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        main_box.append(scrolled)

        page = Adw.PreferencesPage()
        scrolled.set_child(page)

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

        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_bottom(12)
        button_box.set_margin_end(12)
        button_box.set_margin_start(12)
        main_box.append(button_box)

        def on_save_clicked(button: Gtk.Button) -> None:
            try:
                new_config = {
                    "books_per_line": int(books_per_line_spin.get_value()),
                    "zoom_level": float(zoom_spin.get_value()),
                    "cache_dir": cache_entry.get_text(),
                }
                save_config(new_config)
                self.grid.update_config(new_config)
                self.refresh_grid()
                dialog.destroy()
            except ValueError as e:
                self.show_error(str(e))

        save_btn = Gtk.Button(label="Save")
        save_btn.add_css_class("suggested-action")
        save_btn.connect("clicked", on_save_clicked)
        button_box.append(save_btn)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: dialog.destroy())
        button_box.append(cancel_btn)

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

```

## FILE: src/ui/shelf_grid.py

```py
"""UI component for the book grid."""

from typing import Any, Callable, Optional

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk  # noqa: E402

from src.config import load_config  # noqa: E402
from src.models.book import Book  # noqa: E402
from src.ui.book_widget import BookWidget  # noqa: E402


class ShelfGrid(Gtk.Grid):  # type: ignore
    """A grid that displays a collection of BookWidgets."""

    def __init__(
        self,
        on_book_selected_callback: Callable[[Book], None],
        on_book_right_clicked_callback: Optional[
            Callable[[Gtk.Widget, Book], None]
        ] = None,
    ) -> None:
        """Initialize the ShelfGrid."""
        super().__init__()
        self.on_book_selected = on_book_selected_callback
        self.on_book_right_clicked = on_book_right_clicked_callback
        self._config = load_config()
        self.set_column_spacing(24)
        self.set_row_spacing(24)
        self.set_halign(Gtk.Align.CENTER)
        self.set_valign(Gtk.Align.START)
        self.set_margin_top(18)
        self.set_margin_bottom(18)
        self.set_margin_start(18)
        self.set_margin_end(18)

    def update_config(self, config: dict[str, Any]) -> None:
        """Update the cached configuration."""
        self._config = config

    def update_books(self, books: list[Book]) -> None:
        """Refresh the grid with a new list of books."""
        # Remove existing children
        child = self.get_first_child()
        while child:
            self.remove(child)
            child = self.get_first_child()

        # Use cached config for column count and zoom
        cols = self._config.get("books_per_line", 4)
        zoom_level = self._config.get("zoom_level", 1.0)

        # Explicit grid with dynamic columns
        for i, book in enumerate(books):
            widget = BookWidget(
                book,
                self.on_book_selected,
                zoom_level=zoom_level,
                on_right_click_callback=self.on_book_right_clicked,
            )
            self.attach(widget, i % cols, i // cols, 1, 1)

```

## FILE: src/ui/sidebar.py

```py
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

```

## FILE: tests/__init__.py

```py
"""Tests package."""

```

## FILE: tests/test_book.py

```py
"""Tests for the Book model."""

from src.models.book import Book


def test_book_creation() -> None:
    """Test that a Book object can be created with correct attributes."""
    book = Book(path="/path/to/book.pdf", title="Test Book", author="Test Author")
    assert book.path == "/path/to/book.pdf"
    assert book.title == "Test Book"
    assert book.author == "Test Author"
    assert book.cover_path is None

```

## FILE: tests/test_config.py

```py
"""Tests for configuration management."""

import json
import os
import shutil
import tempfile
from typing import Generator

import pytest

import src.config
from src.config import load_config, save_config


@pytest.fixture  # type: ignore
def mock_config_file() -> Generator[str, None, None]:
    """Fixture to provide a temporary config file path and monkeypatch CONFIG_FILE."""
    test_dir = tempfile.mkdtemp()
    test_config_path = os.path.join(test_dir, "config.json")

    original_config_file = src.config.CONFIG_FILE
    src.config.CONFIG_FILE = test_config_path

    yield test_config_path

    src.config.CONFIG_FILE = original_config_file
    shutil.rmtree(test_dir)


def test_load_config_defaults(mock_config_file: str) -> None:
    """Test that load_config returns defaults if no file exists."""
    # Ensure config file doesn't exist (it shouldn't by default in temp dir)
    config = load_config()
    assert config["books_per_line"] == src.config.DEFAULT_CONFIG["books_per_line"]
    assert config["zoom_level"] == src.config.DEFAULT_CONFIG["zoom_level"]
    assert "cache_dir" in config


def test_save_and_load_config(mock_config_file: str) -> None:
    """Test that config can be saved and loaded correctly."""
    test_config = {
        "books_per_line": 5,
        "zoom_level": 1.5,
        "cache_dir": "/tmp/eshelf_cache",
    }

    save_config(test_config)
    loaded_config = load_config()

    assert loaded_config["books_per_line"] == 5
    assert loaded_config["zoom_level"] == 1.5
    assert loaded_config["cache_dir"] == "/tmp/eshelf_cache"


def test_load_config_partial(mock_config_file: str) -> None:
    """Test that loading partial config merges with defaults."""
    # Create a partial config file
    with open(mock_config_file, "w") as f:
        json.dump({"books_per_line": 20}, f)

    config = load_config()
    assert config["books_per_line"] == 20
    assert config["zoom_level"] == src.config.DEFAULT_CONFIG["zoom_level"]

```

## FILE: tests/test_controller.py

```py
"""Tests for the MainController."""

from unittest.mock import MagicMock, patch

from src.controller.main_controller import MainController
from src.models.book import Book


def test_controller_get_books() -> None:
    """Test retrieving books via controller."""
    with (
        patch("src.controller.main_controller.BookRepository"),
        patch("src.controller.main_controller.CoverExtractor"),
        patch("src.controller.main_controller.BookScanner"),
    ):
        mock_repo = MagicMock()
        mock_repo.get_all_books.return_value = [Book(path="1", title="T1", author="A1")]

        controller = MainController("lib", "db", "cache")
        controller.repository = mock_repo

        books = controller.get_books()
        assert len(books) == 1
        assert books[0].title == "T1"


def test_controller_scan_library() -> None:
    """Test scanning library via controller."""
    with (
        patch("src.controller.main_controller.BookRepository"),
        patch("src.controller.main_controller.CoverExtractor"),
        patch("src.controller.main_controller.BookScanner"),
    ):
        mock_scanner = MagicMock()
        mock_scanner.scan.return_value = (1, 0)

        controller = MainController("lib", "db", "cache")
        controller.scanner = mock_scanner

        added, updated = controller.scan_library()
        assert added == 1
        assert updated == 0
        mock_scanner.scan.assert_called_once_with("lib", progress_callback=None)


def test_controller_cleanup_library() -> None:
    """Test cleanup via controller."""
    with (
        patch("src.controller.main_controller.BookRepository"),
        patch("src.controller.main_controller.CoverExtractor"),
        patch("src.controller.main_controller.BookScanner"),
    ):
        mock_scanner = MagicMock()
        mock_scanner.cleanup_missing.return_value = 5

        controller = MainController("lib", "db", "cache")
        controller.scanner = mock_scanner

        removed = controller.cleanup_library()
        assert removed == 5
        mock_scanner.cleanup_missing.assert_called_once_with("lib")


@patch("subprocess.run")
def test_controller_open_book(mock_run: MagicMock) -> None:
    """Test opening a book."""
    with (
        patch("src.controller.main_controller.BookRepository"),
        patch("src.controller.main_controller.CoverExtractor"),
        patch("src.controller.main_controller.BookScanner"),
    ):
        controller = MainController("lib", "db", "cache")
        book = Book(path="/path/to/book.pdf", title="Title", author="Author")

        controller.open_book(book)
        mock_run.assert_called_once_with(["xdg-open", "/path/to/book.pdf"], check=True)


def test_controller_import_folder() -> None:
    """Test importing a folder via controller."""
    with (
        patch("src.controller.main_controller.BookRepository"),
        patch("src.controller.main_controller.CoverExtractor"),
        patch("src.controller.main_controller.BookScanner"),
    ):
        mock_scanner = MagicMock()
        mock_scanner.scan.return_value = (2, 1)

        controller = MainController("lib", "db", "cache")
        controller.scanner = mock_scanner

        added, updated = controller.import_folder("/path/to/folder")
        assert added == 2
        assert updated == 1
        mock_scanner.scan.assert_called_once_with(
            "/path/to/folder", progress_callback=None
        )


def test_controller_import_file_success() -> None:
    """Test importing a valid book file."""
    with (
        patch("src.controller.main_controller.BookRepository"),
        patch("src.controller.main_controller.CoverExtractor"),
        patch("src.controller.main_controller.BookScanner"),
    ):
        mock_repo = MagicMock()
        mock_extractor = MagicMock()
        mock_extractor.extract.return_value = "/cache/cover.jpg"

        controller = MainController("lib", "db", "cache")
        controller.repository = mock_repo
        controller.extractor = mock_extractor

        success = controller.import_file("/path/to/book.pdf")
        assert success is True
        mock_repo.add_book.assert_called_once()
        args = mock_repo.add_book.call_args[0][0]
        assert args.title == "book"
        assert args.cover_path == "/cache/cover.jpg"


def test_controller_import_file_invalid() -> None:
    """Test importing an invalid file."""
    with (
        patch("src.controller.main_controller.BookRepository"),
        patch("src.controller.main_controller.CoverExtractor"),
        patch("src.controller.main_controller.BookScanner"),
    ):
        controller = MainController("lib", "db", "cache")
        success = controller.import_file("/path/to/image.png")
        assert success is False

```

## FILE: tests/test_extractor.py

```py
"""Tests for the CoverExtractor service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.extractor import CoverExtractor


def test_extract_unsupported_format() -> None:
    """Test that unsupported formats return None."""
    extractor = CoverExtractor("/tmp/eshelf_cache")
    assert extractor.extract("book.txt") is None


@patch("src.services.extractor.convert_from_path")
def test_extract_pdf_success(mock_convert: MagicMock) -> None:
    """Test successful PDF cover extraction."""
    # Mock pdf2image.convert_from_path to return a mock image
    mock_image = MagicMock()
    mock_convert.return_value = [mock_image]

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.pdf")

    assert result is not None
    assert "test.pdf" not in result  # Should be a hash
    mock_image.save.assert_called_once()


@patch("src.services.extractor.epub.read_epub")
def test_extract_epub_success(mock_read_epub: MagicMock) -> None:
    """Test successful EPUB cover extraction."""
    # Mock EPUB book and items
    mock_book = MagicMock()
    mock_item = MagicMock()
    mock_item.get_type.return_value = 9  # ITEM_IMAGE is 9 in ebooklib
    mock_item.get_name.return_value = "cover.jpg"
    mock_item.get_content.return_value = b"fake_image_data"

    mock_book.get_metadata.return_value = "cover_id"
    mock_book.get_item_with_id.return_value = mock_item
    mock_read_epub.return_value = mock_book

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.epub")

    assert result is not None
    assert Path(result).exists()

    # Cleanup
    Path(result).unlink()


@patch("src.services.extractor.epub.read_epub")
def test_extract_epub_failure(mock_read_epub: MagicMock) -> None:
    """Test EPUB extraction failure."""
    mock_book = MagicMock()
    mock_book.get_metadata.return_value = None
    mock_book.get_items.return_value = []
    mock_read_epub.return_value = mock_book

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.epub")

    assert result is None

```

## FILE: tests/test_grid_integration.py

```py
"""Integration test to verify the grid layout behavior."""

import sys
from unittest.mock import MagicMock

import gi  # noqa: E402

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Adw, GLib  # noqa: E402

from src.models.book import Book  # noqa: E402
from src.ui.shelf_grid import ShelfGrid  # noqa: E402


# Mock ebooklib and other potentially missing dependencies
def setup_mocks() -> None:
    """Mock ebooklib and other potentially missing dependencies."""
    sys.modules["ebooklib"] = MagicMock()

    sys.modules["ebooklib.epub"] = MagicMock()
    sys.modules["pdf2image"] = MagicMock()


setup_mocks()


def test_shelf_grid_layout_columns() -> None:
    """Verify that multiple books are placed in different columns."""
    app = Adw.Application(application_id="org.test.eshelf")
    success = [False]

    def on_activate(app: Adw.Application) -> None:
        win = Adw.ApplicationWindow(application=app)
        win.set_default_size(1000, 800)

        grid = ShelfGrid(on_book_selected_callback=lambda b: None)
        books = [
            Book(path=f"/tmp/book{i}.pdf", title=f"Book {i}", author="Author")
            for i in range(10)
        ]
        grid.update_books(books)

        win.set_content(grid)
        win.present()

        GLib.timeout_add(100, check_layout, grid, win, app)

    def check_layout(
        grid: ShelfGrid, win: Adw.ApplicationWindow, app: Adw.Application
    ) -> bool:
        child1 = grid.get_first_child()
        if not child1:
            app.quit()
            return False

        child2 = child1.get_next_sibling()
        if not child2:
            app.quit()
            return False

        alloc1 = child1.get_allocation()
        alloc2 = child2.get_allocation()

        print(f"Child 1: x={alloc1.x}")
        print(f"Child 2: x={alloc2.x}")

        if alloc1.x != alloc2.x:
            success[0] = True

        app.quit()
        return False

    app.connect("activate", on_activate)
    try:
        app.run([])
    except Exception as e:
        print(f"Could not run GTK app test: {e}")

    assert success[0], "Books should be in different columns"

```

## FILE: tests/test_main.py

```py
"""Tests for the main entry point."""

from unittest.mock import MagicMock, patch

from src.main import main


@patch("src.main.MainController")
@patch("src.main.Adw.Application")
@patch("os.makedirs")
def test_main_execution(
    mock_makedirs: MagicMock,
    mock_adw_app: MagicMock,
    mock_controller: MagicMock,
) -> None:
    """Test that main() initializes the controller and application."""
    mock_app_instance = mock_adw_app.return_value

    main()

    # Verify controller initialization
    mock_controller.assert_called_once()

    # Verify application initialization
    mock_adw_app.assert_called_once()

    # Verify application run was called
    mock_app_instance.run.assert_called_once()

```

## FILE: tests/test_repository.py

```py
"""Tests for the BookRepository."""

import os
import tempfile

from src.database.repository import BookRepository
from src.models.book import Book


def test_repository_add_and_get() -> None:
    """Test adding and retrieving a book."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = BookRepository(db_path)

        book = Book(
            path="/path/to/book.pdf",
            title="Test Title",
            author="Test Author",
            cover_path="/path/to/cover.png",
        )
        repo.add_book(book)

        retrieved = repo.get_book_by_path("/path/to/book.pdf")
        assert retrieved == book

        all_books = repo.get_all_books()
        assert len(all_books) == 1
        assert all_books[0] == book


def test_repository_update_book() -> None:
    """Test updating an existing book."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = BookRepository(db_path)

        book = Book(path="/path/to/book.pdf", title="Original Title", author="Author")
        repo.add_book(book)

        updated_book = Book(
            path="/path/to/book.pdf",
            title="New Title",
            author="Author",
        )
        repo.add_book(updated_book)

        retrieved = repo.get_book_by_path("/path/to/book.pdf")
        assert retrieved is not None
        assert retrieved.title == "New Title"
        assert len(repo.get_all_books()) == 1


def test_repository_remove_book() -> None:
    """Test removing a book."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = BookRepository(db_path)

        book = Book(
            path="/path/to/book.pdf",
            title="Title",
            author="Author",
        )
        repo.add_book(book)

        repo.remove_book("/path/to/book.pdf")
        assert repo.get_book_by_path("/path/to/book.pdf") is None
        assert len(repo.get_all_books()) == 0


def test_repository_clear() -> None:
    """Test clearing the database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = BookRepository(db_path)

        repo.add_book(Book(path="1", title="T1", author="A1"))
        repo.add_book(Book(path="2", title="T2", author="A2"))

        repo.clear()
        assert len(repo.get_all_books()) == 0


def test_repository_category_management() -> None:
    """Test category creation, deletion, and book association."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = BookRepository(db_path)

        # Test category creation
        cat_id = repo.create_category("Sci-Fi")
        assert cat_id > 0
        categories = repo.get_all_categories()
        assert len(categories) == 1
        assert categories[0].name == "Sci-Fi"

        # Test associating book with category
        book = Book(path="1", title="T1", author="A1", category_id=cat_id)
        repo.add_book(book)

        # Test retrieving books by category
        sci_fi_books = repo.get_books_by_category(cat_id)
        assert len(sci_fi_books) == 1
        assert sci_fi_books[0].path == "1"

        # Test retrieving uncategorized books
        book2 = Book(path="2", title="T2", author="A2", category_id=None)
        repo.add_book(book2)
        uncat_books = repo.get_books_by_category(None)
        assert len(uncat_books) == 1
        assert uncat_books[0].path == "2"

        # Test updating book category
        repo.update_book_category("2", cat_id)
        sci_fi_books_updated = repo.get_books_by_category(cat_id)
        assert len(sci_fi_books_updated) == 2
        uncat_books_updated = repo.get_books_by_category(None)
        assert len(uncat_books_updated) == 0

        # Test deleting category
        repo.delete_category(cat_id)
        assert len(repo.get_all_categories()) == 0
        # Books should become uncategorized (due to ON DELETE SET NULL)
        uncat_after_del = repo.get_books_by_category(None)
        assert len(uncat_after_del) == 2


def test_repository_update_book_preserves_category() -> None:
    """Test that updating a book preserves its category if not provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = BookRepository(db_path)

        cat_id = repo.create_category("Tech")
        book = Book(
            path="/path/to/book.pdf",
            title="Original",
            author="Author",
            category_id=cat_id,
        )
        repo.add_book(book)

        # Update book without providing category_id (it will be None)
        updated_book = Book(
            path="/path/to/book.pdf",
            title="Updated",
            author="Author",
        )
        repo.add_book(updated_book)

        retrieved = repo.get_book_by_path("/path/to/book.pdf")
        assert retrieved is not None
        assert retrieved.title == "Updated"
        assert retrieved.category_id == cat_id

```

## FILE: tests/test_scanner.py

```py
"""Tests for the BookScanner service."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.database.repository import BookRepository
from src.models.book import Book
from src.services.extractor import CoverExtractor
from src.services.scanner import BookScanner


def test_scanner_finds_books() -> None:
    """Test that the scanner finds supported files and adds them to the repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some dummy book files
        book_pdf = Path(tmpdir) / "test_book.pdf"
        book_pdf.touch()
        book_epub = Path(tmpdir) / "another_book.epub"
        book_epub.touch()
        ignored_file = Path(tmpdir) / "notes.txt"
        ignored_file.touch()

        # Mock dependencies
        mock_repo = MagicMock(spec=BookRepository)
        mock_repo.get_book_by_path.return_value = None

        mock_extractor = MagicMock(spec=CoverExtractor)
        mock_extractor.extract.return_value = "/tmp/cover.png"

        scanner = BookScanner(mock_repo, mock_extractor)
        added, updated = scanner.scan(tmpdir)

        assert added == 2
        assert updated == 0
        assert mock_repo.add_book.call_count == 2


def test_scanner_updates_existing_books() -> None:
    """Test that the scanner updates books with new covers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        book_pdf = Path(tmpdir) / "test_book.pdf"
        book_pdf.touch()

        # Mock repo to return an existing book with a different cover
        mock_repo = MagicMock(spec=BookRepository)
        mock_repo.get_book_by_path.return_value = Book(
            path=str(book_pdf.absolute()),
            title="test_book",
            author="Unknown Author",
            cover_path="/old/cover.png",
        )

        mock_extractor = MagicMock(spec=CoverExtractor)
        mock_extractor.extract.return_value = "/new/cover.png"

        scanner = BookScanner(mock_repo, mock_extractor)
        added, updated = scanner.scan(tmpdir)

        assert added == 0
        assert updated == 1
        mock_repo.add_book.assert_called_once()


def test_scanner_cleanup_missing() -> None:
    """Test cleanup_missing removes non-existent files only within directory."""
    mock_repo = MagicMock(spec=BookRepository)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Book 1: Exists in tmpdir
        book1_path = Path(tmpdir) / "exists.pdf"
        book1_path.touch()
        # Book 2: Missing in tmpdir
        book2_path = Path(tmpdir) / "gone.pdf"
        # Book 3: Missing but NOT in tmpdir
        book3_path = Path("/non/existent/dir/gone.pdf")

        mock_repo.get_all_books.return_value = [
            Book(path=str(book1_path.absolute()), title="Exist", author="A"),
            Book(path=str(book2_path.absolute()), title="Gone1", author="B"),
            Book(path=str(book3_path.absolute()), title="Gone2", author="C"),
        ]

        mock_extractor = MagicMock(spec=CoverExtractor)
        scanner = BookScanner(mock_repo, mock_extractor)

        removed = scanner.cleanup_missing(str(Path(tmpdir).absolute()))

        assert removed == 1
        mock_repo.remove_book.assert_called_once_with(str(book2_path.absolute()))

```

## FILE: tests/test_ui.py

```py
"""Tests for UI components."""

from unittest.mock import MagicMock, patch

from src.models.book import Book
from src.ui.book_widget import BookWidget
from src.ui.main_window import MainWindow
from src.ui.shelf_grid import ShelfGrid


def test_book_widget_initialization() -> None:
    """Test that BookWidget initializes with correct book."""
    book = Book(path="/path/to/book.pdf", title="Test Book", author="Author")
    callback = MagicMock()
    widget = BookWidget(book, callback)
    assert widget.book == book


def test_shelf_grid_update_books() -> None:
    """Test that ShelfGrid correctly adds book widgets."""
    callback = MagicMock()
    grid = ShelfGrid(callback)
    books = [
        Book(path="1", title="T1", author="A1"),
        Book(path="2", title="T2", author="A2"),
    ]
    grid.update_books(books)
    # FlowBox doesn't have a simple 'get_children' but we can check first child
    assert grid.get_first_child() is not None


def test_main_window_controller_integration() -> None:
    """Test MainWindow's interaction with the controller."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        # Manually set some necessary attributes that would be set by __init__
        win.controller = None
        win.grid = MagicMock()

        controller = MagicMock()
        controller.get_books.return_value = [Book(path="1", title="T1", author="A1")]

        win.set_controller(controller)
        assert win.controller == controller
        controller.get_books.assert_called_once()
        win.grid.update_books.assert_called_once()


def test_main_window_event_handlers() -> None:
    """Test MainWindow event handlers call correct controller methods."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
        patch("threading.Thread") as mock_thread,
    ):
        win = MainWindow()
        controller = MagicMock()
        controller.scan_library.return_value = (1, 1)
        controller.cleanup_library.return_value = 1
        win.controller = controller

        # Test scan
        win.on_scan_clicked(MagicMock())
        mock_thread.assert_called_once()
        # Execute the scan worker synchronously for testing
        scan_worker = mock_thread.call_args[1]["target"]
        scan_worker()
        controller.scan_library.assert_called_once()

        # Test cleanup
        win.on_cleanup_clicked(MagicMock())
        controller.cleanup_library.assert_called_once()

        # Test book selection
        book = Book(path="1", title="T1", author="A1")
        win.on_book_selected(book)
        controller.open_book.assert_called_once_with(book)


def test_main_window_import_handlers() -> None:
    """Test MainWindow import handlers."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        controller = MagicMock()
        win.controller = controller

        # Test import file (without controller)
        win.controller = None
        win.on_import_file_clicked(MagicMock())

        # Test import folder (without controller)
        win.on_import_folder_clicked(MagicMock())

        # Test import file (with controller) - we mock FileDialog
        win.controller = controller
        with patch("src.ui.main_window.Gtk.FileDialog") as mock_dialog:
            win.on_import_file_clicked(MagicMock())
            mock_dialog.assert_called_once()

        with patch("src.ui.main_window.Gtk.FileDialog") as mock_dialog:
            win.on_import_folder_clicked(MagicMock())
            mock_dialog.assert_called_once()


def test_main_window_helper_methods() -> None:
    """Test MainWindow helper methods."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        win.progress_bar = MagicMock()
        win.scan_button = MagicMock()
        win.grid = MagicMock()
        win.controller = MagicMock()

        # Test update_progress
        win.update_progress(5, 10)
        win.progress_bar.set_fraction.assert_called_with(0.5)

        # Test on_scan_finished
        win.on_scan_finished(1, 1)
        win.scan_button.set_sensitive.assert_called_with(True)
        win.progress_bar.set_visible.assert_called_with(False)
        win.refresh_grid()  # Should not crash

        # Test refresh_grid
        win.controller.get_books.return_value = []
        win.refresh_grid()
        win.controller.get_books.assert_called()
        win.grid.update_books.assert_called()


def test_main_window_settings_clicked() -> None:
    """Test that opening settings creates a dialog."""
    with (
        patch("src.ui.main_window.Adw.ApplicationWindow.__init__", return_value=None),
        patch.object(MainWindow, "set_title"),
        patch.object(MainWindow, "set_default_size"),
        patch.object(MainWindow, "set_content"),
    ):
        win = MainWindow()
        with patch("src.ui.main_window.Adw.Dialog") as mock_dialog:
            win.on_settings_clicked(MagicMock())
            mock_dialog.assert_called_once()

```

