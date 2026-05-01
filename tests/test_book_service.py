"""Tests for the BookService."""

import os
import tempfile
from typing import Generator

import pytest

from src.database.repository import BookRepository
from src.models.book import Book
from src.services.book_service import BookService


@pytest.fixture(scope="function")  # type: ignore
def book_service_env() -> Generator[tuple[BookService, str], None, None]:
    """Fixture to provide a BookService with a temporary database."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test_service.db")
        repo = BookRepository(db_path)
        service = BookService(repo)
        yield service, db_path
        repo.close()


def test_book_service_get_books_pagination(
    book_service_env: tuple[BookService, str],
) -> None:
    """Test that get_books supports pagination."""
    service, _ = book_service_env

    # Add 5 books
    for i in range(5):
        service.add_book(Book(path=str(i), title=f"Title {i}", author=f"Author {i}"))

    # Test limit
    books_limited = service.get_books(limit=2)
    assert len(books_limited) == 2

    # Test offset
    books_offset = service.get_books(limit=2, offset=2)
    assert len(books_offset) == 2
    assert books_offset[0].path != books_limited[0].path


def test_book_service_get_books_no_category(
    book_service_env: tuple[BookService, str],
) -> None:
    """Test retrieving all books (category_id=None)."""
    service, _ = book_service_env
    service.add_book(Book(path="1", title="T1", author="A1"))
    service.add_book(Book(path="2", title="T2", author="A2"))

    books = service.get_books(category_id=None)
    assert len(books) == 2


def test_book_service_search_books(
    book_service_env: tuple[BookService, str],
) -> None:
    """Test searching for books."""
    service, _ = book_service_env
    service.add_book(Book(path="1", title="Python", author="Guido"))
    service.add_book(Book(path="2", title="C++", author="Bjarne"))

    results = service.search_books("Python")
    assert len(results) == 1
    assert results[0].path == "1"


def test_book_service_sort_books(
    book_service_env: tuple[BookService, str],
) -> None:
    """Test sorting books."""
    service, _ = book_service_env
    b1 = Book(path="1", title="B", author="A")
    b2 = Book(path="2", title="A", author="B")
    books = [b1, b2]

    # Sort by title
    sorted_title = service.sort_books(books, "Title")
    assert sorted_title[0].title == "A"

    # Sort by author
    sorted_author = service.sort_books(books, "Author")
    assert sorted_author[0].author == "A"

    # Sort unknown
    assert service.sort_books(books, "Unknown") == books


def test_book_service_update_metadata(
    book_service_env: tuple[BookService, str],
) -> None:
    """Test updating book metadata."""
    service, _ = book_service_env
    service.add_book(Book(path="1", title="T1", author="A1"))

    service.update_book_metadata("1", "T2", "A2")

    books = service.get_books()
    assert books[0].title == "T2"
    assert books[0].author == "A2"


def test_book_service_category_management(
    book_service_env: tuple[BookService, str],
) -> None:
    """Test category management in BookService."""
    service, _ = book_service_env

    # Create
    cat_id = service.create_category("Fiction")
    assert cat_id is not None

    # Get categories
    categories = service.get_categories()
    assert len(categories) == 1
    assert categories[0].name == "Fiction"

    # Move book to category
    service.add_book(Book(path="1", title="T1", author="A1"))
    service.move_book_to_category("1", cat_id)

    # Check categorized
    books = service.get_books(category_id=cat_id)
    assert len(books) == 1

    # Check uncategorized
    uncat = service.get_uncategorized_books()
    assert len(uncat) == 0

    # Delete category
    service.delete_category(cat_id)
    assert len(service.get_categories()) == 0
