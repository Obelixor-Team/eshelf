"""Service for scanning directories for books and updating the library."""

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from src.config import SUPPORTED_EXTENSIONS
from src.database.repository import BookRepository
from src.models.book import Book
from src.services.exceptions import ExtractionError
from src.services.extractor import CoverExtractor
from src.services.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class BookScanner:
    """Scans directories for supported book files and updates the repository."""

    def __init__(
        self,
        repository: BookRepository,
        extractor: CoverExtractor,
        metadata_extractor: Optional[MetadataExtractor] = None,
    ):
        """Initialize the scanner.

        Args:
            repository (BookRepository): The repository to persist book metadata.
            extractor (CoverExtractor): The extractor to generate cover images.
            metadata_extractor (MetadataExtractor, optional): Metadata extractor.
        """
        self.repository = repository
        self.extractor = extractor
        self.metadata_extractor = metadata_extractor or MetadataExtractor()

    def _process_file(self, file: Path) -> Tuple[Optional[Book], Optional[str]]:
        """Process a single file and return (Book, failed_file_path)."""
        file_path = str(file.absolute())

        if file.stat().st_size == 0:
            logger.warning(f"Skipping empty book file: {file_path}")
            return None, file_path

        # Extract metadata
        try:
            title, author = self.metadata_extractor.extract(file_path)
        except Exception as e:
            logger.warning(
                f"Skipping book {file_path} due to metadata extraction error: {e}"
            )
            return None, file_path

        # Check existing book/extract cover
        try:
            existing_book = self.repository.get_book_by_path(file_path)
            cover_path = None
            if (
                existing_book
                and existing_book.cover_path
                and Path(existing_book.cover_path).exists()
            ):
                cover_path = existing_book.cover_path
            else:
                cover_path = self.extractor.extract(file_path)
        except ExtractionError as e:
            logger.error(f"Skipping book {file_path} due to extraction error: {e}")
            return None, file_path

        if existing_book:
            if (
                existing_book.title != title
                or existing_book.author != author
                or existing_book.cover_path != cover_path
            ):
                return Book(
                    path=file_path,
                    title=title,
                    author=author,
                    cover_path=cover_path,
                    category_id=existing_book.category_id,
                    created_at=existing_book.created_at,
                ), None
        else:
            return Book(
                path=file_path,
                title=title,
                author=author,
                cover_path=cover_path,
                created_at=datetime.now(),
            ), None
        return None, None

    def scan(
        self,
        directory: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        recursive: bool = True,
    ) -> Tuple[int, int, List[str]]:
        """Scan a directory for books and update the repository."""
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise ValueError(f"Provided path is not a directory: {directory}")

        all_files = [
            f
            for f in dir_path.glob("**/*" if recursive else "*")
            if f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
        total_files = len(all_files)
        added = 0
        updated = 0
        failed_files: List[str] = []

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {
                executor.submit(self._process_file, f): f for f in all_files
            }
            for i, future in enumerate(future_to_file, 1):
                if progress_callback:
                    progress_callback(i, total_files)

                book, failed_path = future.result()

                if failed_path:
                    failed_files.append(failed_path)
                    continue

                if book is None:
                    continue

                existing = self.repository.get_book_by_path(book.path)
                if existing:
                    self.repository.add_book(book)
                    updated += 1
                else:
                    self.repository.add_book(book)
                    added += 1

        return added, updated, failed_files

    def cleanup_all(self, directories: List[str]) -> int:
        """Remove books that are no longer monitored or missing."""
        removed = 0
        all_books = self.repository.get_all_books()
        dir_paths = [Path(d).absolute() for d in directories]

        for book in all_books:
            book_path = Path(book.path).absolute()
            exists = book_path.exists()

            in_monitored_dir = any(
                book_path.is_relative_to(lib_path) for lib_path in dir_paths
            )

            if not exists or not in_monitored_dir:
                self.repository.remove_book(book.path)
                removed += 1

        return removed
