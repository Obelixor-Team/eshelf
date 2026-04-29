"""Service for extracting metadata from PDF and EPUB files."""

import logging
from pathlib import Path
from typing import Tuple

import fitz  # PyMuPDF
from ebooklib import epub

from src.services.exceptions import ExtractionError

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extracts title and author from digital book formats."""

    def extract(self, file_path: str) -> Tuple[str, str]:
        """Extract metadata from a file.

        Args:
            file_path (str): Path to the book file.

        Returns:
            Tuple[str, str]: A tuple of (title, author).
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            return self._extract_pdf(path)
        elif ext == ".epub":
            return self._extract_epub(path)

        return path.stem, "Unknown Author"

    def _extract_pdf(self, path: Path) -> Tuple[str, str]:
        """Extract metadata from a PDF file."""
        try:
            with fitz.open(path) as doc:
                meta = doc.metadata
                title = meta.get("title")
                author = meta.get("author")

                # Fallback to filename if title is empty
                final_title = title if title and title.strip() else path.stem
                final_author = author if author and author.strip() else "Unknown Author"

                return final_title, final_author
        except Exception as e:
            raise ExtractionError(f"Error extracting PDF metadata from {path}") from e

    def _extract_epub(self, path: Path) -> Tuple[str, str]:
        """Extract metadata from an EPUB file."""
        try:
            book = epub.read_epub(path)

            title = book.get_metadata("DC", "title")
            author = book.get_metadata("DC", "creator")

            final_title = title[0][0] if title else path.stem
            final_author = author[0][0] if author else "Unknown Author"

            return final_title, final_author
        except Exception as e:
            raise ExtractionError(f"Error extracting EPUB metadata from {path}") from e
