"""Book model for storing book metadata."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Book:
    """Represents a book in the library.

    Attributes:
        path (str): Path to the book file.
        title (str): Title of the book.
        author (str): Author of the book.
        cover_path (Optional[str]): Path to the extracted cover image.
        category_id (Optional[int]): ID of the category the book belongs to.
        created_at (Optional[datetime]): When the book was added to the library.
    """

    path: str
    title: str
    author: str
    cover_path: Optional[str] = None
    category_id: Optional[int] = None
    created_at: Optional[datetime] = None
