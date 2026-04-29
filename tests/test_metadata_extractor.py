"""Tests for the MetadataExtractor service."""

from unittest.mock import MagicMock, patch

from src.services.metadata_extractor import MetadataExtractor


def test_extract_unsupported_format() -> None:
    """Test that unsupported formats return fallback values."""
    extractor = MetadataExtractor()
    title, author = extractor.extract("book.txt")
    assert title == "book"
    assert author == "Unknown Author"


@patch("src.services.metadata_extractor.fitz.open")
def test_extract_pdf_success(mock_open: MagicMock) -> None:
    """Test successful PDF metadata extraction."""
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "PDF Title", "author": "PDF Author"}
    mock_open.return_value.__enter__.return_value = mock_doc

    extractor = MetadataExtractor()
    title, author = extractor.extract("test.pdf")
    assert title == "PDF Title"
    assert author == "PDF Author"


@patch("src.services.metadata_extractor.fitz.open")
def test_extract_pdf_fallback(mock_open: MagicMock) -> None:
    """Test PDF metadata extraction fallback to filename."""
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "", "author": None}
    mock_open.return_value.__enter__.return_value = mock_doc

    extractor = MetadataExtractor()
    title, author = extractor.extract("test_book.pdf")
    assert title == "test_book"
    assert author == "Unknown Author"


@patch("src.services.metadata_extractor.epub.read_epub")
def test_extract_epub_success(mock_read_epub: MagicMock) -> None:
    """Test successful EPUB metadata extraction."""
    mock_book = MagicMock()

    def metadata_side_effect(dc: str, key: str) -> list[list[str]]:
        return [["Value"]] if key in ("title", "creator") else []

    mock_book.get_metadata.side_effect = metadata_side_effect
    mock_read_epub.return_value = mock_book

    extractor = MetadataExtractor()
    title, author = extractor.extract("test.epub")
    assert title == "Value"
    assert author == "Value"


@patch("src.services.metadata_extractor.epub.read_epub")
def test_extract_epub_fallback(mock_read_epub: MagicMock) -> None:
    """Test EPUB metadata extraction fallback."""
    mock_book = MagicMock()
    mock_book.get_metadata.return_value = []
    mock_read_epub.return_value = mock_book

    extractor = MetadataExtractor()
    title, author = extractor.extract("test_book.epub")
    assert title == "test_book"
    assert author == "Unknown Author"


@patch("src.services.metadata_extractor.fitz.open")
def test_extract_pdf_error(mock_open: MagicMock) -> None:
    """Test that PDF extraction errors raise ExtractionError."""
    mock_open.side_effect = Exception("PDF corrupted")

    from src.services.exceptions import ExtractionError

    extractor = MetadataExtractor()
    import pytest

    with pytest.raises(ExtractionError, match="Error extracting PDF metadata"):
        extractor.extract("corrupted.pdf")


@patch("src.services.metadata_extractor.epub.read_epub")
def test_extract_epub_error(mock_read_epub: MagicMock) -> None:
    """Test that EPUB extraction errors raise ExtractionError."""
    mock_read_epub.side_effect = Exception("EPUB corrupted")

    from src.services.exceptions import ExtractionError

    extractor = MetadataExtractor()
    import pytest

    with pytest.raises(ExtractionError, match="Error extracting EPUB metadata"):
        extractor.extract("corrupted.epub")


@patch("src.services.metadata_extractor.fitz.open")
def test_extract_pdf_only_author(mock_open: MagicMock) -> None:
    """Test PDF extraction when only author is present."""
    mock_doc = MagicMock()
    mock_doc.metadata = {"title": "", "author": "Only Author"}
    mock_open.return_value.__enter__.return_value = mock_doc

    extractor = MetadataExtractor()
    title, author = extractor.extract("test_book.pdf")
    assert title == "test_book"
    assert author == "Only Author"


@patch("src.services.metadata_extractor.epub.read_epub")
def test_extract_epub_only_creator(mock_read_epub: MagicMock) -> None:
    """Test EPUB extraction when only creator is present."""
    mock_book = MagicMock()

    def metadata_side_effect(dc: str, key: str) -> list[list[str]]:
        return [["Only Creator"]] if key == "creator" else []

    mock_book.get_metadata.side_effect = metadata_side_effect
    mock_read_epub.return_value = mock_book

    extractor = MetadataExtractor()
    title, author = extractor.extract("test_book.epub")
    assert title == "test_book"
    assert author == "Only Creator"
