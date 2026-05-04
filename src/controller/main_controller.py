"""Controller to coordinate between the UI and the backend services."""

import logging
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from src.config import SUPPORTED_EXTENSIONS
from src.database.repository import BookRepository
from src.models.book import Book
from src.models.category import Category
from src.services.book_service import BookService
from src.services.exceptions import ExtractionError
from src.services.extractor import CoverExtractor
from src.services.metadata_extractor import MetadataExtractor
from src.services.scanner import BookScanner


class MainController:
    """Coordinates book scanning, persistence, and UI updates."""

    logger = logging.getLogger(__name__)

    def __init__(
        self,
        library_dirs: List[str],
        db_path: str,
        cache_dir: str,
        error_callback: Optional[Callable[[str], None]] = None,
    ):
        """Initialize the controller.

        Args:
            library_dirs (List[str]): Directories where books are stored.
            db_path (str): Path to the SQLite database.
            cache_dir (str): Path to the thumbnail cache.
            error_callback (callable, optional): Callback to report errors to the UI.
        """
        self.library_dirs = library_dirs
        self.repository = BookRepository(db_path)
        self.book_service = BookService(self.repository)
        self.extractor = CoverExtractor(cache_dir)
        self.metadata_extractor = MetadataExtractor()
        self.scanner = BookScanner(
            self.repository, self.extractor, self.metadata_extractor
        )
        self.error_callback = error_callback

    def get_books(
        self,
        category_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Book]:
        """Retrieve books from the repository, optionally filtered by category."""
        return self.book_service.get_books(category_id, limit=limit, offset=offset)

    def get_uncategorized_books(self) -> List[Book]:
        """Retrieve books that have no category assigned."""
        return self.book_service.get_uncategorized_books()

    def get_categories(self) -> List[Category]:
        """Retrieve all categories."""
        return self.book_service.get_categories()

    def search_books(self, query: str) -> List[Book]:
        """Search for books by title or author."""
        return self.book_service.search_books(query)

    def sort_books(self, books: List[Book], sort_by: str) -> List[Book]:
        """Sort books based on the given option."""
        return self.book_service.sort_books(books, sort_by)

    def create_category(self, name: str) -> int:
        """Create a new category."""
        return self.book_service.create_category(name)

    def delete_category(self, category_id: int) -> None:
        """Delete a category."""
        self.book_service.delete_category(category_id)

    def move_book_to_category(self, book_path: str, category_id: Optional[int]) -> None:
        """Move a book to a specific category."""
        self.book_service.move_book_to_category(book_path, category_id)

    def scan_library(
        self, progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[int, int, List[str]]:
        """Scan the library for books and return (added, updated, failed) counts."""
        total_added = 0
        total_updated = 0
        all_failed = []

        # Find all files first to provide accurate global progress
        all_files = []
        for lib_dir in self.library_dirs:
            dir_path = Path(lib_dir)
            if not dir_path.is_dir():
                continue
            all_files.extend(
                [
                    f
                    for f in dir_path.glob("**/*")
                    if f.suffix.lower() in SUPPORTED_EXTENSIONS
                ]
            )

        total_files = len(all_files)
        if total_files == 0:
            return 0, 0, []

        processed_count = 0
        for lib_dir in self.library_dirs:
            if not Path(lib_dir).is_dir():
                continue

            def wrapped_callback(current: int, total: int) -> None:
                if progress_callback:
                    # 'total' here is per-directory, but we use global 'total_files'
                    progress_callback(processed_count + current, total_files)

            added, updated, failed = self.scanner.scan(
                lib_dir,
                progress_callback=wrapped_callback if progress_callback else None,
            )
            total_added += added
            total_updated += updated

            # We need to increment processed_count by the number of files in this dir
            dir_files = [
                f
                for f in Path(lib_dir).glob("**/*")
                if f.suffix.lower() in SUPPORTED_EXTENSIONS
            ]
            processed_count += len(dir_files)
            all_failed.extend(failed)

        return total_added, total_updated, all_failed

    def import_folder(
        self,
        folder_path: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        recursive: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """Import books from a specific folder."""
        added, updated, failed = self.scanner.scan(
            folder_path, progress_callback=progress_callback, recursive=recursive
        )
        return added, updated, failed

    def import_file(self, file_path: str) -> bool:
        """Import a single book file."""
        path = Path(file_path)
        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            return False

        try:
            title, author = self.metadata_extractor.extract(file_path)
            cover_path = self.extractor.extract(file_path)

            book = Book(
                path=str(path.absolute()),
                title=title,
                author=author,
                cover_path=cover_path,
            )
            self.book_service.add_book(book)
            return True
        except ExtractionError as e:
            error_msg = str(e)
            if self.error_callback:
                self.error_callback(error_msg)
            else:
                self.logger.error(error_msg)
            return False

    def import_path(
        self,
        path: str,
        category_id: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        recursive: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """Import a file or folder into a specific category."""
        target = Path(path)
        if target.is_file():
            success = self.import_file(path)
            if success and category_id:
                self.move_book_to_category(path, category_id)
            return (1 if success else 0, 0, [] if success else [path])
        elif target.is_dir():
            # Get list of existing books to identify newly imported ones
            existing_paths = {b.path for b in self.repository.get_all_books()}

            added, updated, failed = self.import_folder(
                path, progress_callback=progress_callback, recursive=recursive
            )

            if category_id:
                # Identify newly added books
                all_books = self.repository.get_all_books()
                for book in all_books:
                    if book.path not in existing_paths:
                        self.move_book_to_category(book.path, category_id)

            return added, updated, failed
        return (0, 0, [path])

    def cleanup_library(self) -> int:
        """Remove missing books and return count of removed books."""
        return self.scanner.cleanup_all(self.library_dirs)

    def clear_library(self) -> None:
        """Clear the database and remove all cached cover images."""
        self.logger.info("Starting clear_library")
        try:
            self.repository.clear()
            self.logger.info("Repository cleared successfully")
        except Exception as e:
            self.logger.error(f"Failed to clear repository: {e}")
            raise

        # Remove all files in the cache directory
        cache_path = Path(self.extractor.cache_dir)
        self.logger.info(f"Clearing cache at {cache_path}")
        if cache_path.exists() and cache_path.is_dir():
            count = 0
            for item in cache_path.iterdir():
                if item.is_file():
                    try:
                        item.unlink()
                        count += 1
                    except Exception as e:
                        self.logger.error(f"Failed to delete {item}: {e}")
            self.logger.info(f"Removed {count} files from cache")
        else:
            self.logger.debug(f"Cache path {cache_path} is invalid")

    def update_book_metadata(self, book_path: str, title: str, author: str) -> None:
        """Update the metadata for a book."""
        self.book_service.update_book_metadata(book_path, title, author)

    def open_book(self, book: Book) -> None:
        """Open a book using the system's default application."""
        try:
            self.book_service.open_book(book)
        except RuntimeError as e:
            if self.error_callback:
                self.error_callback(str(e))
            else:
                self.logger.error(str(e))
