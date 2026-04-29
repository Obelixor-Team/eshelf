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


def test_repository_update_metadata() -> None:
    """Test updating book metadata directly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        repo = BookRepository(db_path)

        book = Book(path="/path/to/book.pdf", title="Old Title", author="Old Author")
        repo.add_book(book)

        repo.update_book_metadata("/path/to/book.pdf", "New Title", "New Author")
        retrieved = repo.get_book_by_path("/path/to/book.pdf")
        assert retrieved is not None
        assert retrieved.title == "New Title"
        assert retrieved.author == "New Author"
