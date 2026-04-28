"""Controller to coordinate between the UI and the backend services."""

from pathlib import Path
from typing import Callable, List, Optional

from src.database.repository import BookRepository
from src.models.book import Book
from src.services.extractor import CoverExtractor
from src.services.scanner import BookScanner


class MainController:
    """Coordinates book scanning, persistence, and UI updates."""

    def __init__(self, library_dir: str, db_path: str, cache_dir: str):
        """Initialize the controller.

        Args:
            library_dir (str): Directory where books are stored.
            db_path (str): Path to the SQLite database.
            cache_dir (str): Path to the thumbnail cache.
        """
        self.library_dir = library_dir
        self.repository = BookRepository(db_path)
        self.extractor = CoverExtractor(cache_dir)
        self.scanner = BookScanner(self.repository, self.extractor)

    def get_books(self) -> List[Book]:
        """Retrieve all books from the repository."""
        return self.repository.get_all_books()

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
        import subprocess

        try:
            subprocess.run(["xdg-open", book.path], check=True)
        except subprocess.CalledProcessError as e:
            print(f"Failed to open book {book.path}: {e}")
