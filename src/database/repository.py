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

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def _init_db(self) -> None:
        """Create the categories and books tables if they don't exist."""
        with self._get_connection() as conn:
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
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (category_id) REFERENCES categories (id)
                    ON DELETE SET NULL
                )
                """
            )
            # Migration: Add created_at to books table if it doesn't exist
            cursor = conn.execute("PRAGMA table_info(books)")
            columns = [column[1] for column in cursor.fetchall()]
            if "created_at" not in columns:
                conn.execute("ALTER TABLE books ADD COLUMN created_at DATETIME")

            conn.commit()

    def add_book(self, book: Book) -> None:
        """Add or update a book in the database."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO books (
                    path, title, author, cover_path, category_id, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(path) DO UPDATE SET
                    title = excluded.title,
                    author = excluded.author,
                    cover_path = excluded.cover_path,
                    category_id = COALESCE(excluded.category_id, books.category_id)
                """,
                (
                    book.path,
                    book.title,
                    book.author,
                    book.cover_path,
                    book.category_id,
                    book.created_at,
                ),
            )
            conn.commit()

    def get_all_books(self) -> List[Book]:
        """Retrieve all books from the database."""
        with self._get_connection() as conn:
            query = (
                "SELECT path, title, author, cover_path, category_id, created_at "
                "FROM books"
            )
            cursor = conn.execute(query)
            return [
                Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                    created_at=row[5],
                )
                for row in cursor.fetchall()
            ]

    def get_book_by_path(self, path: str) -> Optional[Book]:
        """Find a book by its file path."""
        with self._get_connection() as conn:
            query = (
                "SELECT path, title, author, cover_path, category_id, created_at "
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
                    created_at=row[5],
                )
            return None

    def remove_book(self, path: str) -> None:
        """Remove a book from the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM books WHERE path = ?", (path,))
            conn.commit()

    def update_book_category(self, path: str, category_id: Optional[int]) -> None:
        """Update the category of a book."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE books SET category_id = ? WHERE path = ?",
                (category_id, path),
            )
            conn.commit()

    def update_book_metadata(self, path: str, title: str, author: str) -> None:
        """Update the title and author of a book."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE books SET title = ?, author = ? WHERE path = ?",
                (title, author, path),
            )
            conn.commit()

    def create_category(self, name: str) -> int:
        """Create a new category and return its ID."""
        with self._get_connection() as conn:
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
        with self._get_connection() as conn:
            conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
            conn.commit()

    def get_all_categories(self) -> List[Category]:
        """Retrieve all categories from the database."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT id, name FROM categories ORDER BY name")
            return [Category(id=row[0], name=row[1]) for row in cursor.fetchall()]

    def get_books_by_category(self, category_id: Optional[int]) -> List[Book]:
        """Retrieve books belonging to a specific category."""
        with self._get_connection() as conn:
            if category_id is None:
                query = (
                    "SELECT path, title, author, cover_path, category_id, created_at "
                    "FROM books WHERE category_id IS NULL"
                )
                cursor = conn.execute(query)
            else:
                query = (
                    "SELECT path, title, author, cover_path, category_id, created_at "
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
                    created_at=row[5],
                )
                for row in cursor.fetchall()
            ]

    def clear(self) -> None:
        """Remove all books from the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM books")
            conn.commit()
