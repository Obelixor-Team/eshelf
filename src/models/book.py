"""Book model for storing book metadata."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Book:
    """Represents a book in the library.

    Attributes:
        path (str): Path to the book file.
        title (str): Title of the book.
        author (str): Author of the book.
        cover_path (Optional[str]): Path to the extracted cover image.
    """

    path: str
    title: str
    author: str
    cover_path: Optional[str] = None
