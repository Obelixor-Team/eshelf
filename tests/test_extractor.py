"""Tests for the CoverExtractor service."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from src.services.extractor import CoverExtractor


def test_extract_unsupported_format() -> None:
    """Test that unsupported formats return None."""
    extractor = CoverExtractor("/tmp/eshelf_cache")
    assert extractor.extract("book.txt") is None


@patch("src.services.extractor.convert_from_path")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.mkdir")
@patch("pathlib.Path.stat")
def test_extract_pdf_success(
    mock_path_stat: MagicMock,
    mock_mkdir: MagicMock,
    mock_exists: MagicMock,
    mock_convert: MagicMock,
) -> None:
    """Test successful PDF cover extraction."""
    # Mock pdf2image.convert_from_path to return a mock image
    mock_image = MagicMock()
    mock_convert.return_value = [mock_image]

    # Mock Path.exists to return False so mkdir is called
    mock_exists.return_value = False
    # Mock Path.stat to return dummy values
    mock_path_stat.return_value.st_size = 1024
    mock_path_stat.return_value.st_mtime = 1234567890
    # Mock Path.st_mode for is_dir check (not directly used but stat is called)
    mock_path_stat.return_value.st_mode = 0o100644  # regular file

    extractor = CoverExtractor("/tmp/eshelf_cache")
    result = extractor.extract("test.pdf")

    assert result is not None
    assert result.endswith(".png")  # Should be a hash-based path
    mock_image.save.assert_called_once()

    @patch("src.services.extractor.Image")
    @patch("src.services.extractor.epub.read_epub")
    @patch("pathlib.Path.stat")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.mkdir")
    def test_extract_epub_success(
        mock_mkdir: MagicMock,
        mock_exists: MagicMock,
        mock_path_stat: MagicMock,
        mock_read_epub: MagicMock,
        mock_image: MagicMock,
    ) -> None:
        """Test successful EPUB cover extraction."""
        # Mock EPUB book and items
        mock_book = MagicMock()
        mock_item = MagicMock()
        mock_item.get_type.return_value = 9  # ITEM_IMAGE is 9 in ebooklib
        mock_item.get_name.return_value = "cover.jpg"
        mock_item.get_content.return_value = b"fake_image_data"

        # Mock metadata properly: list of tuples for get_metadata
        mock_book.get_metadata.return_value = [("cover_id", "cover_id")]
        mock_book.get_item_with_id.return_value = mock_item
        mock_read_epub.return_value = mock_book

        # Mock Path.exists to return False so mkdir is called
        mock_exists.return_value = False
        # Mock Path.stat to return dummy values
        mock_path_stat.return_value.st_size = 1024
        mock_path_stat.return_value.st_mtime = 1234567890
        # Mock Path.st_mode for is_dir check (not directly used but stat is called)
        mock_path_stat.return_value.st_mode = 0o100644  # regular file

        extractor = CoverExtractor("/tmp/eshelf_cache")
        result = extractor.extract("test.epub")

        assert result is not None
        mock_image.open.assert_called_once()

    assert result.endswith(".png")  # Should be a hash-based path

    # Cleanup
    if Path(result).exists():
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
