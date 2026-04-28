"""Tests for the Book model."""

from src.models.book import Book


def test_book_creation() -> None:
    """Test that a Book object can be created with correct attributes."""
    book = Book(path="/path/to/book.pdf", title="Test Book", author="Test Author")
    assert book.path == "/path/to/book.pdf"
    assert book.title == "Test Book"
    assert book.author == "Test Author"
    assert book.cover_path is None
