"""Tests for the BookScanner service."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.database.repository import BookRepository
from src.models.book import Book
from src.services.extractor import CoverExtractor
from src.services.scanner import BookScanner


def test_scanner_finds_books() -> None:
    """Test that the scanner finds supported files and adds them to the repo."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create some dummy book files
        book_pdf = Path(tmpdir) / "test_book.pdf"
        book_pdf.touch()
        book_epub = Path(tmpdir) / "another_book.epub"
        book_epub.touch()
        ignored_file = Path(tmpdir) / "notes.txt"
        ignored_file.touch()

        # Mock dependencies
        mock_repo = MagicMock(spec=BookRepository)
        mock_repo.get_book_by_path.return_value = None

        mock_extractor = MagicMock(spec=CoverExtractor)
        mock_extractor.extract.return_value = "/tmp/cover.png"

        scanner = BookScanner(mock_repo, mock_extractor)
        added, updated = scanner.scan(tmpdir)

        assert added == 2
        assert updated == 0
        assert mock_repo.add_book.call_count == 2


def test_scanner_updates_existing_books() -> None:
    """Test that the scanner updates books with new covers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        book_pdf = Path(tmpdir) / "test_book.pdf"
        book_pdf.touch()

        # Mock repo to return an existing book with a different cover
        mock_repo = MagicMock(spec=BookRepository)
        mock_repo.get_book_by_path.return_value = Book(
            path=str(book_pdf.absolute()),
            title="test_book",
            author="Unknown Author",
            cover_path="/old/cover.png",
        )

        mock_extractor = MagicMock(spec=CoverExtractor)
        mock_extractor.extract.return_value = "/new/cover.png"

        scanner = BookScanner(mock_repo, mock_extractor)
        added, updated = scanner.scan(tmpdir)

        assert added == 0
        assert updated == 1
        mock_repo.add_book.assert_called_once()


def test_scanner_cleanup_missing() -> None:
    """Test that cleanup_missing removes non-existent files."""
    mock_repo = MagicMock(spec=BookRepository)
    # Return one existing and one missing book
    with tempfile.NamedTemporaryFile() as tmp_file:
        mock_repo.get_all_books.return_value = [
            Book(path=tmp_file.name, title="Exist", author="A"),
            Book(path="/non/existent/path", title="Gone", author="B"),
        ]

        mock_extractor = MagicMock(spec=CoverExtractor)
        scanner = BookScanner(mock_repo, mock_extractor)

        removed = scanner.cleanup_missing("/tmp")

        assert removed == 1
        mock_repo.remove_book.assert_called_once_with("/non/existent/path")
