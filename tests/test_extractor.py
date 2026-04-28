"""Tests for the CoverExtractor service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.extractor import CoverExtractor


def test_extract_unsupported_format() -> None:
    """Test that unsupported formats return None."""
    extractor = CoverExtractor("/tmp/eshelf_cache")
    assert extractor.extract("book.txt") is None


@patch("src.services.extractor.convert_from_path")
def test_extract_pdf_success(mock_convert: MagicMock) -> None:
    """Test successful PDF cover extraction."""
    # Mock pdf2image.convert_from_path to return a mock image
    mock_image = MagicMock()
    mock_convert.return_value = [mock_image]

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.pdf")

    assert result is not None
    assert "test.pdf" not in result  # Should be a hash
    mock_image.save.assert_called_once()


@patch("src.services.extractor.epub.read_epub")
def test_extract_epub_success(mock_read_epub: MagicMock) -> None:
    """Test successful EPUB cover extraction."""
    # Mock EPUB book and items
    mock_book = MagicMock()
    mock_item = MagicMock()
    mock_item.get_type.return_value = 9  # ITEM_IMAGE is 9 in ebooklib
    mock_item.get_name.return_value = "cover.jpg"
    mock_item.get_content.return_value = b"fake_image_data"

    mock_book.get_metadata.return_value = "cover_id"
    mock_book.get_item_with_id.return_value = mock_item
    mock_read_epub.return_value = mock_book

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.epub")

    assert result is not None
    assert Path(result).exists()

    # Cleanup
    Path(result).unlink()


@patch("src.services.extractor.epub.read_epub")
def test_extract_epub_failure(mock_read_epub: MagicMock) -> None:
    """Test EPUB extraction failure."""
    mock_book = MagicMock()
    mock_book.get_metadata.return_value = None
    mock_book.get_items.return_value = []
    mock_read_epub.return_value = mock_book

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.epub")

    assert result is None
