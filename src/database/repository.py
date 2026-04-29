"""Repository for managing book metadata in a SQLite database."""

import sqlite3
from typing import List, Optional

from src.models.book import Book
from src.models.category import Category


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
        """Create the categories and books tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS books (
                    path TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    cover_path TEXT,
                    category_id INTEGER,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                    ON DELETE SET NULL
                )
                """
            )
            try:
                conn.execute(
                    "ALTER TABLE books ADD COLUMN category_id INTEGER "
                    "REFERENCES categories (id) ON DELETE SET NULL"
                )
            except sqlite3.OperationalError:
                pass
            conn.commit()

    def add_book(self, book: Book) -> None:
        """Add or update a book in the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                """
                INSERT OR REPLACE INTO books 
                (path, title, author, cover_path, category_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (book.path, book.title, book.author, book.cover_path, book.category_id),
            )
            conn.commit()

    def get_all_books(self) -> List[Book]:
        """Retrieve all books from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            query = "SELECT path, title, author, cover_path, category_id FROM books"
            cursor = conn.execute(query)
            return [
                Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                )
                for row in cursor.fetchall()
            ]

    def get_book_by_path(self, path: str) -> Optional[Book]:
        """Find a book by its file path."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            query = (
                "SELECT path, title, author, cover_path, category_id "
                "FROM books WHERE path = ?"
            )
            cursor = conn.execute(query, (path,))
            row = cursor.fetchone()
            if row:
                return Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                )
            return None

    def remove_book(self, path: str) -> None:
        """Remove a book from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM books WHERE path = ?", (path,))
            conn.commit()

    def update_book_category(self, path: str, category_id: Optional[int]) -> None:
        """Update the category of a book."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute(
                "UPDATE books SET category_id = ? WHERE path = ?",
                (category_id, path),
            )
            conn.commit()

    def create_category(self, name: str) -> int:
        """Create a new category and return its ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.execute(
                "INSERT INTO categories (name) VALUES (?)",
                (name,),
            )
            conn.commit()
            last_id = cursor.lastrowid
            if last_id is None:
                raise RuntimeError("Failed to create category: no ID returned")
            return last_id

    def delete_category(self, category_id: int) -> None:
        """Delete a category."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()

    def get_all_categories(self) -> List[Category]:
        """Retrieve all categories from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            cursor = conn.execute("SELECT id, name FROM categories ORDER BY name")
            return [Category(id=row[0], name=row[1]) for row in cursor.fetchall()]

    def get_books_by_category(self, category_id: Optional[int]) -> List[Book]:
        """Retrieve books belonging to a specific category."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            if category_id is None:
                query = (
                    "SELECT path, title, author, cover_path, category_id "
                    "FROM books WHERE category_id IS NULL"
                )
                cursor = conn.execute(query)
            else:
                query = (
                    "SELECT path, title, author, cover_path, category_id "
                    "FROM books WHERE category_id = ?"
                )
                cursor = conn.execute(query, (category_id,))
            return [
                Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                )
                for row in cursor.fetchall()
            ]

    def clear(self) -> None:
        """Remove all books from the database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("DELETE FROM books")
            conn.commit()
