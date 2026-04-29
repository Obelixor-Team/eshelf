"""Service for extracting book covers from PDF and EPUB files."""

import hashlib
import logging
from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub
from pdf2image import convert_from_path

from src.services.exceptions import ExtractionError

logger = logging.getLogger(__name__)


class CoverExtractor:
    """Extracts thumbnails from digital book formats."""

    def __init__(self, cache_dir: str):
        """Initialize the extractor.

        Args:
            cache_dir (str): Directory where extracted covers are stored.
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def extract(self, file_path: str) -> Optional[str]:
        """Extract a cover image from a file and save it to the cache.

        Args:
            file_path (str): Path to the book file.

        Returns:
            Optional[str]: Path to the saved cover image, or None if extraction failed.
        """
        path = Path(file_path)
        ext = path.suffix.lower()

        if ext == ".pdf":
            return self._extract_pdf(path)
        elif ext == ".epub":
            return self._extract_epub(path)

        return None

    def _extract_pdf(self, path: Path) -> Optional[str]:
        """Extract the first page of a PDF as a cover image."""
        try:
            # Convert only the first page to an image
            images = convert_from_path(path, first_page=1, last_page=1)
            if not images:
                return None

            cover_image = images[0]
            output_path = self._get_output_path(path)
            cover_image.save(output_path, "PNG")
            return str(output_path)
        except (OSError, RuntimeError) as e:
            raise ExtractionError(f"Error extracting PDF cover from {path}") from e

    def _extract_epub(self, path: Path) -> Optional[str]:
        """Extract the cover image from an EPUB file."""
        try:
            book = epub.read_epub(path)
            # EPUBs usually define the cover in the metadata
            cover_id_meta = book.get_metadata("OPF", "cover")
            cover_item = None
            if cover_id_meta:
                cover_item = book.get_item_with_id(cover_id_meta[0][0])

            if not cover_item:
                # Fallback: search for common cover image names
                for item in book.get_items():
                    if (
                        item.get_type() == ebooklib.ITEM_IMAGE
                        and "cover" in item.get_name().lower()
                    ):
                        cover_item = item
                        break

            if not cover_item:
                return None

            output_path = self._get_output_path(path)
            with open(output_path, "wb") as f:
                f.write(cover_item.get_content())

            return str(output_path)
        except Exception as e:
            raise ExtractionError(f"Error extracting EPUB cover from {path}") from e

    def _get_output_path(self, path: Path) -> Path:
        """Generate a unique output path for the cover image based on the file path."""
        file_hash = hashlib.sha256(str(path.absolute()).encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.png"
