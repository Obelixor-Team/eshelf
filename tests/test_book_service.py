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


def test_book_service_get_uncategorized_books(
    book_service_env: tuple[BookService, str],
) -> None:
    """Test retrieving uncategorized books."""
    service, _ = book_service_env
    cat_id = service.create_category("Test Cat")

    service.add_book(Book(path="1", title="T1", author="A1", category_id=cat_id))
    service.add_book(Book(path="2", title="T2", author="A2", category_id=None))

    uncat = service.get_uncategorized_books()
    assert len(uncat) == 1
    assert uncat[0].path == "2"
