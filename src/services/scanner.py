"""Service for scanning directories for books and updating the library."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from src.database.repository import BookRepository
from src.models.book import Book
from src.services.exceptions import ExtractionError
from src.services.extractor import CoverExtractor
from src.services.metadata_extractor import MetadataExtractor

logger = logging.getLogger(__name__)


class BookScanner:
    """Scans directories for PDF and EPUB files and updates the repository."""

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

    def scan(
        self,
        directory: str,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> Tuple[int, int, List[str]]:
        """Scan a directory for books and update the repository.

        Args:
            directory (str): The directory path to scan.
            progress_callback (callable, optional): Callback for progress updates.

        Returns:
            Tuple[int, int, List[str]]:
                A tuple containing (added_count, updated_count, failed_files).
        """
        added = 0
        updated = 0
        failed_files: List[str] = []

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

            # Extract metadata
            try:
                title, author = self.metadata_extractor.extract(file_path)
            except Exception as e:
                logger.error(
                    f"Skipping book {file_path} due to metadata extraction error: {e}"
                )
                failed_files.append(file_path)
                continue

            # Check if book already exists
            try:
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
            except ExtractionError as e:
                logger.error(f"Skipping book {file_path} due to extraction error: {e}")
                failed_files.append(file_path)
                continue

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
                        created_at=existing_book.created_at,
                    )
                    self.repository.add_book(book)
                    updated += 1
            else:
                book = Book(
                    path=file_path,
                    title=title,
                    author=author,
                    cover_path=cover_path,
                    created_at=datetime.now(),
                )
                self.repository.add_book(book)
                added += 1

        return added, updated, failed_files

    def cleanup_missing(self, directory: str) -> int:
        """Remove books from the repository that no longer exist on disk.

        Args:
            directory (str): The directory path to verify against.

        Returns:
            int: Number of books removed.
        """
        removed = 0
        all_books = self.repository.get_all_books()

        dir_path = Path(directory)
        for book in all_books:
            try:
                Path(book.path).relative_to(dir_path)
            except ValueError:
                continue

            if not Path(book.path).exists():
                self.repository.remove_book(book.path)
                removed += 1

        return removed
