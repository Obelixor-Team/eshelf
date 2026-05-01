"""Service for extracting book covers from PDF and EPUB files."""

import hashlib
import io
import logging
from pathlib import Path
from typing import Optional

import ebooklib
from ebooklib import epub
from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)


class CoverExtractor:
    """Extracts thumbnails from digital book formats."""

    THUMBNAIL_SIZE = (200, 300)

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
            cover_image.thumbnail(self.THUMBNAIL_SIZE)
            output_path = self._get_output_path(path)
            cover_image.save(output_path, "PNG")
            return str(output_path)
        except Exception as e:
            logger.warning(f"Could not extract PDF cover from {path}: {e}")
            return None

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
            with Image.open(io.BytesIO(cover_item.get_content())) as img:
                img.thumbnail(self.THUMBNAIL_SIZE)
                img.save(output_path, "PNG")

            return str(output_path)
        except Exception as e:
            logger.warning(f"Could not extract EPUB cover from {path}: {e}")
            return None

    def _get_output_path(self, path: Path) -> Path:
        """Generate a unique output path for the cover image based on file content."""
        # Use file size and modification time for quick comparison
        stat = path.stat()
        file_size = stat.st_size
        mtime = stat.st_mtime

        # Create a hash based on file size, mtime, and first/last 64KB of content
        hash_input = f"{file_size}:{mtime}:"
        try:
            with open(path, "rb") as f:
                # Read first 64KB
                hash_input += f.read(65536).hex()
                # Read last 64KB (if file is large enough)
                f.seek(max(0, file_size - 65536))
                hash_input += f.read(65536).hex()
        except (OSError, IOError):
            # Fallback to path-based hash if we can't read the file
            file_hash = hashlib.sha256(str(path.absolute()).encode()).hexdigest()
            return self.cache_dir / f"{file_hash}.png"

        file_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        return self.cache_dir / f"{file_hash}.png"
