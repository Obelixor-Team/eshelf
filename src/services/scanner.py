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
