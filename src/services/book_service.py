"""Service for managing book metadata and categories."""

from typing import List, Optional

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
        """Sort books based on the given option."""
        if sort_by == "Title":
            return sorted(books, key=lambda b: b.title.lower())
        elif sort_by == "Author":
            return sorted(books, key=lambda b: b.author.lower())
        elif sort_by == "Recently Added":
            return sorted(
                books,
                key=lambda b: b.created_at or b.path,  # Fallback for None
                reverse=True,
            )
        return books

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
