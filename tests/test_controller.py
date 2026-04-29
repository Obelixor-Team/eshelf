"""Tests for the MainController."""

import os
import tempfile
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from src.controller.main_controller import MainController
from src.models.book import Book


@pytest.fixture
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
    mock_repo = MagicMock()
    mock_repo.get_all_books.return_value = [Book(path="1", title="T1", author="A1")]
    controller.repository = mock_repo

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
    mock_repo = MagicMock()
    mock_extractor = MagicMock()
    mock_extractor.extract.return_value = "/cache/cover.jpg"
    controller.repository = mock_repo
    controller.extractor = mock_extractor

    success = controller.import_file("/path/to/book.pdf")
    assert success is True
    mock_repo.add_book.assert_called_once()
    args = mock_repo.add_book.call_args[0][0]
    assert args.title == "book"
    assert args.cover_path == "/cache/cover.jpg"


def test_controller_import_file_invalid(
    controller_env: tuple[MainController, str],
) -> None:
    """Test importing an invalid file."""
    controller, _ = controller_env
    success = controller.import_file("/path/to/image.png")
    assert success is False
