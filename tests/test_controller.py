"""Tests for the MainController."""

import os
import tempfile
from datetime import datetime
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from src.controller.main_controller import MainController
from src.models.book import Book


@pytest.fixture  # type: ignore
def controller_env() -> Generator[tuple[MainController, str], None, None]:
    """Fixture to provide a controller with a temporary database and cache."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        cache_dir = os.path.join(tmpdir, "cache")
        lib_dir = os.path.join(tmpdir, "lib")
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(lib_dir, exist_ok=True)

        with (
            patch("src.controller.main_controller.BookRepository"),
            patch("src.controller.main_controller.CoverExtractor"),
            patch("src.controller.main_controller.BookScanner"),
        ):
            controller = MainController(lib_dir, db_path, cache_dir)
            yield controller, lib_dir


def test_controller_get_books(controller_env: tuple[MainController, str]) -> None:
    """Test retrieving books via controller."""
    controller, _ = controller_env
    mock_service = MagicMock()
    mock_service.get_books.return_value = [Book(path="1", title="T1", author="A1")]
    controller.book_service = mock_service

    books = controller.get_books()
    assert len(books) == 1
    assert books[0].title == "T1"


def test_controller_scan_library(controller_env: tuple[MainController, str]) -> None:
    """Test scanning library via controller."""
    controller, lib_dir = controller_env
    mock_scanner = MagicMock()
    mock_scanner.scan.return_value = (1, 0)
    controller.scanner = mock_scanner

    added, updated = controller.scan_library()
    assert added == 1
    assert updated == 0
    mock_scanner.scan.assert_called_once_with(lib_dir, progress_callback=None)


def test_controller_cleanup_library(controller_env: tuple[MainController, str]) -> None:
    """Test cleanup via controller."""
    controller, lib_dir = controller_env
    mock_scanner = MagicMock()
    mock_scanner.cleanup_missing.return_value = 5
    controller.scanner = mock_scanner

    removed = controller.cleanup_library()
    assert removed == 5
    mock_scanner.cleanup_missing.assert_called_once_with(lib_dir)


@patch("subprocess.run")
def test_controller_open_book(
    mock_run: MagicMock, controller_env: tuple[MainController, str]
) -> None:
    """Test opening a book."""
    controller, _ = controller_env
    book = Book(path="/path/to/book.pdf", title="Title", author="Author")

    controller.open_book(book)
    mock_run.assert_called_once_with(["xdg-open", "/path/to/book.pdf"], check=True)


def test_controller_import_folder(controller_env: tuple[MainController, str]) -> None:
    """Test importing a folder via controller."""
    controller, _ = controller_env
    mock_scanner = MagicMock()
    mock_scanner.scan.return_value = (2, 1)
    controller.scanner = mock_scanner

    added, updated = controller.import_folder("/path/to/folder")
    assert added == 2
    assert updated == 1
    mock_scanner.scan.assert_called_once_with("/path/to/folder", progress_callback=None)


def test_controller_import_file_success(
    controller_env: tuple[MainController, str],
) -> None:
    """Test importing a valid book file."""
    controller, _ = controller_env
    mock_service = MagicMock()
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = "/cache/cover.jpg"
    controller.book_service = mock_service
    controller.extractor = mock_extractor

    # Mock metadata extractor
    controller.metadata_extractor = MagicMock()
    controller.metadata_extractor.extract.return_value = ("Book Title", "Book Author")

    success = controller.import_file("/path/to/book.pdf")
    assert success is True
    mock_service.add_book.assert_called_once()
    args = mock_service.add_book.call_args[0][0]
    assert args.title == "Book Title"
    assert args.author == "Book Author"
    assert args.cover_path == "/cache/cover.jpg"


def test_controller_import_file_invalid(
    controller_env: tuple[MainController, str],
) -> None:
    """Test importing an invalid file."""
    controller, _ = controller_env
    success = controller.import_file("/path/to/image.png")
    assert success is False


def test_controller_update_metadata(controller_env: tuple[MainController, str]) -> None:
    """Test updating book metadata via controller."""
    controller, _ = controller_env
    mock_service = MagicMock()
    controller.book_service = mock_service

    controller.update_book_metadata("/path/to/book.pdf", "New Title", "New Author")
    mock_service.update_book_metadata.assert_called_once_with(
        "/path/to/book.pdf", "New Title", "New Author"
    )


def test_controller_sort_books(controller_env: tuple[MainController, str]) -> None:
    """Test sorting books via controller."""
    controller, _ = controller_env
    books = [
        Book(path="1", title="B", author="X"),
        Book(path="2", title="A", author="Y"),
    ]

    assert controller.sort_books(books, "Title")[0].title == "A"
    assert controller.sort_books(books, "Author")[0].author == "X"

    # Test Recently Added (mock created_at)
    books[0].created_at = datetime(2023, 1, 1)
    books[1].created_at = datetime(2023, 1, 2)
    assert controller.sort_books(books, "Recently Added")[0].path == "2"


def test_controller_category_filtering(
    controller_env: tuple[MainController, str],
) -> None:
    """Test retrieving books by category and uncategorized."""
    controller, _ = controller_env
    mock_service = MagicMock()
    controller.book_service = mock_service

    controller.get_books(category_id=123)
    mock_service.get_books.assert_called_with(123)

    controller.get_uncategorized_books()
    mock_service.get_uncategorized_books.assert_called_once()


def test_controller_import_file_failure(
    controller_env: tuple[MainController, str],
) -> None:
    """Test importing a file that fails metadata extraction."""
    controller, _ = controller_env

    # Mock metadata extractor to fail (it doesn't raise, just returns defaults)
    # But let's mock the path suffix check
    with patch("src.controller.main_controller.Path") as mock_path:
        mock_path.return_value.suffix = ".txt"
        success = controller.import_file("/path/to/file.txt")
        assert success is False
