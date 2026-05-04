"""Service for managing book metadata and categories."""

import logging
import subprocess
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.database.repository import BookRepository
from src.models.book import Book
from src.models.category import Category


class BookService:
    """Handles business logic for book and category management."""

    def __init__(self, repository: BookRepository):
        """Initialize the book service.

        Args:
            repository (BookRepository): The repository for persistence.
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)

        # Strategy pattern for sorting
        self._sort_strategies: Dict[str, Callable[[List[Book]], List[Book]]] = {
            "Title": lambda books: sorted(books, key=lambda b: b.title.lower()),
            "Author": lambda books: sorted(books, key=lambda b: b.author.lower()),
            "Recently Added": lambda books: sorted(
                books,
                key=lambda b: b.created_at or b.path,
                reverse=True,
            ),
        }

    def get_books(
        self,
        category_id: Optional[int] = None,
        limit: Optional[int] = None,
        offset: int = 0,
    ) -> List[Book]:
        """Retrieve books, optionally filtered by category, with optional pagination."""
        if category_id is not None:
            return self.repository.get_books_by_category(category_id)
        return list(self.repository.get_all_books(limit=limit, offset=offset))

    def get_uncategorized_books(self) -> List[Book]:
        """Retrieve books with no category assigned."""
        return self.repository.get_books_by_category(None)

    def get_categories(self) -> List[Category]:
        """Retrieve all categories."""
        return self.repository.get_all_categories()

    def search_books(self, query: str) -> List[Book]:
        """Search for books by title or author."""
        return self.repository.search_books(query)

    def sort_books(self, books: List[Book], sort_by: str) -> List[Book]:
        """Sort books based on the given option using registered strategies."""
        strategy = self._sort_strategies.get(sort_by)
        if strategy:
            return strategy(books)
        return books

    def register_sort_strategy(
        self, name: str, strategy: Callable[[List[Book]], List[Book]]
    ) -> None:
        """Register a new sorting strategy."""
        self._sort_strategies[name] = strategy

    def open_book(self, book: Book) -> None:
        """Open a book using the system's default application."""
        try:
            subprocess.run(
                ["xdg-open", book.path],
                check=True,
                capture_output=True,
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            file_ext = Path(book.path).suffix.upper().lstrip(".")
            error_msg = (
                f"Could not open {file_ext} file.\n\n"
                "Please ensure you have a default application installed "
                "for this file type (e.g., Evince or Okular for PDF, "
                "Foliate for EPUB)."
            )
            self.logger.error(f"Failed to open book {book.path}: {e}")
            raise RuntimeError(error_msg) from e

    def add_book(self, book: Book) -> bool:
        """Add a book to the database. Return True if added, False if updated."""
        exists = self.repository.get_book_by_path(book.path) is not None
        self.repository.add_book(book)
        return not exists

    def create_category(self, name: str) -> int:
        """Create a new category."""
        return self.repository.create_category(name)

    def delete_category(self, category_id: int) -> None:
        """Delete a category."""
        self.repository.delete_category(category_id)

    def move_book_to_category(self, book_path: str, category_id: Optional[int]) -> None:
        """Move a book to a specific category."""
        self.repository.update_book_category(book_path, category_id)

    def update_book_metadata(self, book_path: str, title: str, author: str) -> None:
        """Update the metadata for a book."""
        self.repository.update_book_metadata(book_path, title, author)
