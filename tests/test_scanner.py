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
        added, updated, failed = scanner.scan(tmpdir)

        assert added == 2
        assert updated == 0
        assert len(failed) == 0
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
        added, updated, failed = scanner.scan(tmpdir)

        assert added == 0
        assert updated == 1
        assert len(failed) == 0
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


def test_scanner_invalid_directory() -> None:
    """Test that scan raises ValueError if directory doesn't exist."""
    mock_repo = MagicMock(spec=BookRepository)
    mock_extractor = MagicMock(spec=CoverExtractor)
    scanner = BookScanner(mock_repo, mock_extractor)

    import pytest

    with pytest.raises(ValueError, match="Provided path is not a directory"):
        scanner.scan("/non/existent/directory/path")


def test_scanner_extraction_error() -> None:
    """Test that scanner continues when an ExtractionError occurs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        book1 = Path(tmpdir) / "ok.pdf"
        book1.touch()
        book2 = Path(tmpdir) / "error.pdf"
        book2.touch()

        mock_repo = MagicMock(spec=BookRepository)
        mock_repo.get_book_by_path.return_value = None

        mock_extractor = MagicMock(spec=CoverExtractor)
        mock_extractor.extract.return_value = "/tmp/cover.png"

        mock_metadata_extractor = MagicMock(spec=MetadataExtractor)
        from src.services.exceptions import ExtractionError

        def metadata_side_effect(path: str) -> tuple[str, str]:
            if "error.pdf" in path:
                raise ExtractionError("Failed to extract")
            return ("Title", "Author")

        mock_metadata_extractor.extract.side_effect = metadata_side_effect

        scanner = BookScanner(mock_repo, mock_extractor, mock_metadata_extractor)
        added, updated, failed = scanner.scan(tmpdir)

        assert added == 1
        assert updated == 0
        assert len(failed) == 1
        assert failed[0].endswith("error.pdf")
        assert mock_repo.add_book.call_count == 1


def test_scanner_progress_callback() -> None:
    """Test that the progress callback is called."""
    with tempfile.TemporaryDirectory() as tmpdir:
        for i in range(3):
            (Path(tmpdir) / f"book{i}.pdf").touch()

        mock_repo = MagicMock(spec=BookRepository)
        mock_repo.get_book_by_path.return_value = None
        mock_extractor = MagicMock(spec=CoverExtractor)
        mock_metadata_extractor = MagicMock(spec=MetadataExtractor)
        mock_metadata_extractor.extract.return_value = ("Title", "Author")

        progress_calls = []

        def callback(current: int, total: int) -> None:
            progress_calls.append((current, total))

        scanner = BookScanner(mock_repo, mock_extractor, mock_metadata_extractor)
        added, updated, failed = scanner.scan(tmpdir, progress_callback=callback)

        assert added == 3
        assert updated == 0
        assert len(failed) == 0
        assert len(progress_calls) == 3
        assert progress_calls[0] == (1, 3)
        assert progress_calls[2] == (3, 3)


def test_scanner_updates_on_metadata_change() -> None:
    """Test that the scanner updates books when title or author changes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        book_pdf = Path(tmpdir) / "test_book.pdf"
        book_pdf.touch()

        mock_repo = MagicMock(spec=BookRepository)
        mock_repo.get_book_by_path.return_value = Book(
            path=str(book_pdf.absolute()),
            title="Old Title",
            author="Old Author",
            cover_path="/tmp/cover.png",
        )

        mock_extractor = MagicMock(spec=CoverExtractor)
        mock_extractor.extract.return_value = "/tmp/cover.png"

        mock_metadata_extractor = MagicMock(spec=MetadataExtractor)
        mock_metadata_extractor.extract.return_value = ("New Title", "Old Author")

        scanner = BookScanner(mock_repo, mock_extractor, mock_metadata_extractor)
        added, updated, failed = scanner.scan(tmpdir)

        assert added == 0
        assert updated == 1
        assert len(failed) == 0
        mock_repo.add_book.assert_called_once()
