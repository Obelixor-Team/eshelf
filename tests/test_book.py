"""Tests for the Book model."""

from src.models.book import Book, BookObject


def test_book_creation() -> None:
    """Test that a Book object can be created with correct attributes."""
    book = Book(path="/path/to/book.pdf", title="Test Book", author="Test Author")
    assert book.path == "/path/to/book.pdf"
    assert book.title == "Test Book"
    assert book.author == "Test Author"
    assert book.cover_path is None


def test_book_object_wrapper() -> None:
    """Test the BookObject GObject wrapper."""
    book = Book(
        path="/path/to/book.pdf",
        title="Test Book",
        author="Test Author",
        cover_path="/path/to/cover.jpg",
    )
    book_obj = BookObject(book)
    assert book_obj.title == "Test Book"
    assert book_obj.author == "Test Author"
    assert book_obj.cover_path == "/path/to/cover.jpg"
