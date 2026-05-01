"""Tests for the CoverExtractor service."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import ebooklib

from src.services.extractor import CoverExtractor


def test_extract_unsupported_format() -> None:
    """Test that unsupported formats return None."""
    extractor = CoverExtractor("/tmp/eshelf_cache")
    assert extractor.extract("book.txt") is None


@patch("src.services.extractor.convert_from_path")
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.stat")
def test_extract_pdf_success(
    mock_stat: MagicMock, mock_mkdir: MagicMock, mock_convert: MagicMock
) -> None:
    """Test successful PDF cover extraction."""
    mock_image = MagicMock()
    mock_convert.return_value = [mock_image]
    mock_stat.return_value.st_size = 1024
    mock_stat.return_value.st_mtime = 1234567890

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.pdf")

    assert result is not None
    assert result.endswith(".png")
    mock_image.save.assert_called_once()


@patch("src.services.extractor.convert_from_path")
@patch("pathlib.Path.mkdir")
def test_extract_pdf_no_images(mock_mkdir: MagicMock, mock_convert: MagicMock) -> None:
    """Test PDF extraction when no images are returned."""
    mock_convert.return_value = []
    extractor = CoverExtractor("/tmp/eshelf_cache")
    assert extractor.extract("test.pdf") is None


@patch("src.services.extractor.convert_from_path")
@patch("pathlib.Path.mkdir")
def test_extract_pdf_failure(mock_mkdir: MagicMock, mock_convert: MagicMock) -> None:
    """Test PDF extraction failure."""
    mock_convert.side_effect = Exception("PDF error")
    extractor = CoverExtractor("/tmp/eshelf_cache")
    assert extractor.extract("test.pdf") is None


@patch("src.services.extractor.Image")
@patch("src.services.extractor.epub.read_epub")
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.stat")
def test_extract_epub_success_metadata(
    mock_stat: MagicMock,
    mock_mkdir: MagicMock,
    mock_read_epub: MagicMock,
    mock_image: MagicMock,
) -> None:
    """Test successful EPUB cover extraction via metadata."""
    mock_book = MagicMock()
    mock_item = MagicMock()
    mock_item.get_content.return_value = b"fake_image_data"

    mock_book.get_metadata.return_value = [("cover_id", "cover_id")]
    mock_book.get_item_with_id.return_value = mock_item
    mock_read_epub.return_value = mock_book

    mock_stat.return_value.st_size = 1024
    mock_stat.return_value.st_mtime = 1234567890

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.epub")

    assert result is not None
    assert result.endswith(".png")
    mock_image.open.assert_called_once()


@patch("src.services.extractor.Image")
@patch("src.services.extractor.epub.read_epub")
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.stat")
def test_extract_epub_success_fallback(
    mock_stat: MagicMock,
    mock_mkdir: MagicMock,
    mock_read_epub: MagicMock,
    mock_image: MagicMock,
) -> None:
    """Test successful EPUB cover extraction via fallback search."""
    mock_book = MagicMock()
    mock_item = MagicMock()
    mock_item.get_type.return_value = ebooklib.ITEM_IMAGE
    mock_item.get_name.return_value = "cover.jpg"
    mock_item.get_content.return_value = b"fake_image_data"

    mock_book.get_metadata.return_value = None
    mock_book.get_items.return_value = [mock_item]
    mock_read_epub.return_value = mock_book

    mock_stat.return_value.st_size = 1024
    mock_stat.return_value.st_mtime = 1234567890

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.epub")

    assert result is not None
    assert result.endswith(".png")
    mock_image.open.assert_called_once()


@patch("src.services.extractor.epub.read_epub")
@patch("pathlib.Path.mkdir")
def test_extract_epub_no_cover(
    mock_mkdir: MagicMock, mock_read_epub: MagicMock
) -> None:
    """Test EPUB extraction when no cover is found."""
    mock_book = MagicMock()
    mock_book.get_metadata.return_value = None
    mock_book.get_items.return_value = []
    mock_read_epub.return_value = mock_book

    extractor = CoverExtractor("/tmp/eshelf_cache")
    assert extractor.extract("test.epub") is None


@patch("src.services.extractor.epub.read_epub")
@patch("pathlib.Path.mkdir")
def test_extract_epub_failure(mock_mkdir: MagicMock, mock_read_epub: MagicMock) -> None:
    """Test EPUB extraction failure."""
    mock_read_epub.side_effect = Exception("EPUB error")
    extractor = CoverExtractor("/tmp/eshelf_cache")
    assert extractor.extract("test.epub") is None


@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.stat")
def test_get_output_path_success(mock_stat: MagicMock, mock_mkdir: MagicMock) -> None:
    """Test output path generation from file content."""
    mock_stat.return_value.st_size = 100
    mock_stat.return_value.st_mtime = 1234567890

    # Mock open for reading file content
    with patch("builtins.open", mock_open(read_data=b"some data")):
        extractor = CoverExtractor("/tmp/eshelf_cache")
        path = Path("test.pdf")
        result = extractor._get_output_path(path)
        assert result.suffix == ".png"
        assert result.parent == Path("/tmp/eshelf_cache")


@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.stat")
def test_get_output_path_fallback(mock_stat: MagicMock, mock_mkdir: MagicMock) -> None:
    """Test output path generation fallback to path hash on error."""
    mock_stat.return_value.st_size = 100
    mock_stat.return_value.st_mtime = 1234567890

    # Force OSError when opening the file
    with patch("builtins.open", side_effect=OSError("Read error")):
        extractor = CoverExtractor("/tmp/eshelf_cache")
        path = Path("test.pdf")
        result = extractor._get_output_path(path)
        assert result.suffix == ".png"
        assert result.parent == Path("/tmp/eshelf_cache")
