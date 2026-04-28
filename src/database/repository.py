"""Repository for managing book metadata in a SQLite database."""

import sqlite3
from typing import List, Optional

from src.models.book import Book


class BookRepository:
    """Handles persistence of book metadata using SQLite."""

    def __init__(self, db_path: str):
        """Initialize the repository.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        """Create the books table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    cover_path TEXT
                )
                """
            )
            conn.commit()

    def add_book(self, book: Book) -> None:
        """Add or update a book in the database.

        Args:
            book (Book): The book object to persist.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO books (path, title, author, cover_path)
                VALUES (?, ?, ?, ?)
                """,
                (book.path, book.title, book.author, book.cover_path),
            )
            conn.commit()

    def get_all_books(self) -> List[Book]:
        """Retrieve all books from the database.

        Returns:
            List[Book]: A list of all Book objects.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT path, title, author, cover_path FROM books")
            return [
                Book(path=row[0], title=row[1], author=row[2], cover_path=row[3])
                for row in cursor.fetchall()
            ]

    def get_book_by_path(self, path: str) -> Optional[Book]:
        """Find a book by its file path.

        Args:
            path (str): The file path to search for.

        Returns:
            Optional[Book]: The Book object if found, otherwise None.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT path, title, author, cover_path FROM books WHERE path = ?",
                (path,),
            )
            row = cursor.fetchone()
            if row:
                return Book(path=row[0], title=row[1], author=row[2], cover_path=row[3])
            return None

    def remove_book(self, path: str) -> None:
        """Remove a book from the database.

        Args:
            path (str): The file path of the book to remove.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM books WHERE path = ?", (path,))
            conn.commit()

    def clear(self) -> None:
        """Remove all books from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM books")
            conn.commit()
