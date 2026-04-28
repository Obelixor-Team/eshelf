"""Tests for the MainController."""

from unittest.mock import MagicMock, patch

from src.controller.main_controller import MainController
from src.models.book import Book


def test_controller_get_books() -> None:
    """Test retrieving books via controller."""
    mock_repo = MagicMock()
    mock_repo.get_all_books.return_value = [Book(path="1", title="T1", author="A1")]

    controller = MainController("lib", "db", "cache")
    controller.repository = mock_repo

    books = controller.get_books()
    assert len(books) == 1
    assert books[0].title == "T1"


def test_controller_scan_library() -> None:
    """Test scanning library via controller."""
    mock_scanner = MagicMock()
    mock_scanner.scan.return_value = (1, 0)

    controller = MainController("lib", "db", "cache")
    controller.scanner = mock_scanner

    added, updated = controller.scan_library()
    assert added == 1
    assert updated == 0
    mock_scanner.scan.assert_called_once_with("lib")


def test_controller_cleanup_library() -> None:
    """Test cleanup via controller."""
    mock_scanner = MagicMock()
    mock_scanner.cleanup_missing.return_value = 5

    controller = MainController("lib", "db", "cache")
    controller.scanner = mock_scanner

    removed = controller.cleanup_library()
    assert removed == 5
    mock_scanner.cleanup_missing.assert_called_once_with("lib")


@patch("subprocess.run")
def test_controller_open_book(mock_run: MagicMock) -> None:
    """Test opening a book."""
    controller = MainController("lib", "db", "cache")
    book = Book(path="/path/to/book.pdf", title="Title", author="Author")

    controller.open_book(book)
    mock_run.assert_called_once_with(["xdg-open", "/path/to/book.pdf"], check=True)


def test_controller_import_folder() -> None:
    """Test importing a folder via controller."""
    mock_scanner = MagicMock()
    mock_scanner.scan.return_value = (2, 1)

    controller = MainController("lib", "db", "cache")
    controller.scanner = mock_scanner

    added, updated = controller.import_folder("/path/to/folder")
    assert added == 2
    assert updated == 1
    mock_scanner.scan.assert_called_once_with("/path/to/folder")


def test_controller_import_file_success() -> None:
    """Test importing a valid book file."""
    mock_repo = MagicMock()
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = "/cache/cover.jpg"

    controller = MainController("lib", "db", "cache")
    controller.repository = mock_repo
    controller.extractor = mock_extractor

    success = controller.import_file("/path/to/book.pdf")
    assert success is True
    mock_repo.add_book.assert_called_once()
    args = mock_repo.add_book.call_args[0][0]
    assert args.title == "book"
    assert args.cover_path == "/cache/cover.jpg"


def test_controller_import_file_invalid() -> None:
    """Test importing an invalid file."""
    controller = MainController("lib", "db", "cache")
    success = controller.import_file("/path/to/image.png")
    assert success is False
