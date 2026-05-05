"""Tests for the MainController."""

import os
import subprocess
import tempfile
from datetime import datetime
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from src.controller.main_controller import MainController
from src.models.book import Book
from src.services.exceptions import ExtractionError


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
            controller = MainController([lib_dir], db_path, cache_dir)
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
    mock_scanner.scan.return_value = (1, 0, [])
    controller.scanner = mock_scanner

    # Mock the internal globbing to return a file so total_files > 0
    mock_file = MagicMock()
    mock_file.suffix = ".pdf"
    with patch("src.controller.main_controller.Path.glob") as mock_glob:
        mock_glob.return_value = [mock_file]
        added, updated, failed = controller.scan_library()

    assert added == 1
    assert updated == 0
    assert len(failed) == 0
    # The scanner.scan is called once per lib_dir
    assert mock_scanner.scan.call_count == 1
    call_args = mock_scanner.scan.call_args
    assert call_args[0][0] == lib_dir


def test_controller_cleanup_library(controller_env: tuple[MainController, str]) -> None:
    """Test cleanup via controller."""
    controller, lib_dir = controller_env
    # Add a book that doesn't exist. Path needs to be inside the temporary dir
    # to be 'monitored' but it does not exist on disk.
    ghost_path = os.path.join(lib_dir, "ghost.pdf")
    book = Book(path=ghost_path, title="Ghost", author="None")

    # Mock repository behavior
    controller.repository.get_all_books.return_value = [book]

    removed = controller.cleanup_library()
    assert removed == 1
    controller.repository.remove_book.assert_called_with(ghost_path)


@patch("subprocess.run")
def test_controller_open_book(
    mock_run: MagicMock, controller_env: tuple[MainController, str]
) -> None:
    """Test opening a book with the system default application."""
    controller, _ = controller_env
    # Mock the return object of subprocess.run
    mock_run.return_value.check_returncode.return_value = None
    book = Book(path="/path/to/book.pdf", title="Title", author="Author")

    controller.open_book(book)
    mock_run.assert_called_once_with(
        ["xdg-open", "/path/to/book.pdf"],
        check=True,
        capture_output=True,
        text=True,
    )


def test_controller_import_folder(controller_env: tuple[MainController, str]) -> None:
    """Test importing a folder via controller."""
    controller, _ = controller_env
    mock_scanner = MagicMock()
    mock_scanner.scan.return_value = (2, 1, [])
    controller.scanner = mock_scanner

    added, updated, failed = controller.import_folder("/path/to/folder")
    assert added == 2
    assert updated == 1
    assert len(failed) == 0
    mock_scanner.scan.assert_called_once_with(
        "/path/to/folder", progress_callback=None, recursive=True
    )


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
    mock_service.get_books.assert_called_with(123, limit=None, offset=0)

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


def test_controller_category_management(
    controller_env: tuple[MainController, str],
) -> None:
    """Test category creation, deletion and retrieval via controller."""
    controller, _ = controller_env
    mock_service = MagicMock()
    controller.book_service = mock_service

    # Get categories
    controller.get_categories()
    mock_service.get_categories.assert_called_once()

    # Create category
    controller.create_category("Fiction")
    mock_service.create_category.assert_called_once_with("Fiction")

    # Delete category
    controller.delete_category(1)
    mock_service.delete_category.assert_called_once_with(1)

    # Move book
    controller.move_book_to_category("/path/to/book.pdf", 1)
    mock_service.move_book_to_category.assert_called_once_with("/path/to/book.pdf", 1)


def test_controller_clear_library(controller_env: tuple[MainController, str]) -> None:
    """Test clearing the library."""
    controller, _ = controller_env
    mock_repo = MagicMock()
    controller.repository = mock_repo

    # Mock cache dir to exist and have a file
    with (
        patch("src.controller.main_controller.Path.exists", return_value=True),
        patch("src.controller.main_controller.Path.is_dir", return_value=True),
        patch("src.controller.main_controller.Path.iterdir") as mock_iter,
    ):
        mock_file = MagicMock()
        mock_iter.return_value = [mock_file]

        controller.clear_library()

        mock_repo.clear.assert_called_once()
        mock_file.unlink.assert_called_once()


def test_controller_import_path(controller_env: tuple[MainController, str]) -> None:
    """Test import_path for files, folders, and invalid paths."""
    controller, _ = controller_env

    # Mock import_file and import_folder
    controller.import_file = MagicMock(return_value=True)
    controller.import_folder = MagicMock(return_value=(1, 0, []))
    controller.move_book_to_category = MagicMock()

    with patch("src.controller.main_controller.Path") as mock_path:
        # Case 1: Is file
        mock_path.return_value.is_file.return_value = True
        mock_path.return_value.is_dir.return_value = False
        res = controller.import_path("/path/to/file.pdf", category_id=1)
        assert res == (1, 0, [])
        controller.import_file.assert_called_with("/path/to/file.pdf")
        controller.move_book_to_category.assert_called_with("/path/to/file.pdf", 1)

        # Case 2: Is dir
        mock_path.return_value.is_file.return_value = False
        mock_path.return_value.is_dir.return_value = True
        res = controller.import_path("/path/to/dir", category_id=1)
        assert res == (1, 0, [])
        controller.import_folder.assert_called_with(
            "/path/to/dir", progress_callback=None, recursive=True
        )

        # Case 3: Neither
        mock_path.return_value.is_file.return_value = False
        mock_path.return_value.is_dir.return_value = False
        res = controller.import_path("/path/to/invalid")
        assert res == (0, 0, ["/path/to/invalid"])


@patch("subprocess.run")
def test_controller_open_book_failure(
    mock_run: MagicMock, controller_env: tuple[MainController, str]
) -> None:
    """Test opening a book fails."""
    controller, _ = controller_env
    controller.error_callback = MagicMock()

    mock_run.side_effect = subprocess.CalledProcessError(
        1, ["xdg-open"], stderr="Error"
    )
    book = Book(path="/path/to/book.pdf", title="Title", author="Author")

    controller.open_book(book)
    controller.error_callback.assert_called_once()


def test_controller_import_file_extraction_error(
    controller_env: tuple[MainController, str],
) -> None:
    """Test importing a file that raises an ExtractionError."""
    controller, _ = controller_env
    controller.error_callback = MagicMock()

    with patch("src.controller.main_controller.Path") as mock_path:
        mock_path.return_value.suffix = ".pdf"
        mock_path.return_value.name = "book.pdf"
        # Mock metadata extractor to raise ExtractionError
        with patch(
            "src.controller.main_controller.MetadataExtractor.extract",
            side_effect=ExtractionError("Extraction failed"),
        ):
            success = controller.import_file("/path/to/book.pdf")
            assert success is False
            expected_msg = (
                "Could not extract metadata from book.pdf.\n\n"
                "The file may be corrupted or in an unsupported format."
            )
            controller.error_callback.assert_called_once_with(expected_msg)
