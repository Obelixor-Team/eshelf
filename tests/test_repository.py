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
