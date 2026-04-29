"""Tests for the BookScanner service."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from src.database.repository import BookRepository
from src.models.book import Book
from src.services.extractor import CoverExtractor
from src.services.metadata_extractor import MetadataExtractor
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

        mock_metadata_extractor = MagicMock(spec=MetadataExtractor)
        mock_metadata_extractor.extract.return_value = ("Title", "Author")

        scanner = BookScanner(mock_repo, mock_extractor, mock_metadata_extractor)
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

        mock_metadata_extractor = MagicMock(spec=MetadataExtractor)
        mock_metadata_extractor.extract.return_value = ("test_book", "Unknown Author")

        scanner = BookScanner(mock_repo, mock_extractor, mock_metadata_extractor)
        added, updated = scanner.scan(tmpdir)

        assert added == 0
        assert updated == 1
        mock_repo.add_book.assert_called_once()


def test_scanner_cleanup_missing() -> None:
    """Test cleanup_missing removes non-existent files only within directory."""
    mock_repo = MagicMock(spec=BookRepository)
    with tempfile.TemporaryDirectory() as tmpdir:
        # Book 1: Exists in tmpdir
        book1_path = Path(tmpdir) / "exists.pdf"
        book1_path.touch()
        # Book 2: Missing in tmpdir
        book2_path = Path(tmpdir) / "gone.pdf"
        # Book 3: Missing but NOT in tmpdir
        book3_path = Path("/non/existent/dir/gone.pdf")

        mock_repo.get_all_books.return_value = [
            Book(path=str(book1_path.absolute()), title="Exist", author="A"),
            Book(path=str(book2_path.absolute()), title="Gone1", author="B"),
            Book(path=str(book3_path.absolute()), title="Gone2", author="C"),
        ]

        mock_extractor = MagicMock(spec=CoverExtractor)
        scanner = BookScanner(mock_repo, mock_extractor)

        removed = scanner.cleanup_missing(str(Path(tmpdir).absolute()))

        assert removed == 1
        mock_repo.remove_book.assert_called_once_with(str(book2_path.absolute()))
