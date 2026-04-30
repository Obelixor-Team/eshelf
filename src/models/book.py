"""Book model for storing book metadata."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import gi

gi.require_version("Gtk", "4.0")
from gi.repository import GObject  # noqa: E402


@dataclass
class Book:
    """Represents a book with its metadata."""

    path: str
    title: str
    author: str
    cover_path: Optional[str] = None
    category_id: Optional[int] = None
    created_at: Optional[datetime] = None


class BookObject(GObject.Object):  # type: ignore
    """GObject wrapper for a Book to be used with Gtk.GridView."""

    def __init__(self, book: Book) -> None:
        """Initialize the BookObject."""
        super().__init__()
        self.book = book

    @GObject.Property(type=str)  # type: ignore
    def title(self) -> str:
        """Return the book title."""
        return self.book.title

    @GObject.Property(type=str)  # type: ignore
    def author(self) -> str:
        """Return the book author."""
        return self.book.author

    @GObject.Property(type=str)  # type: ignore
    def cover_path(self) -> Optional[str]:
        """Return the book cover path."""
        return self.book.cover_path
