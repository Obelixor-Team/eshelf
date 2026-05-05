"""Repository for managing book metadata in a SQLite database."""

import sqlite3
import threading
import time
from datetime import datetime
from typing import Callable, Iterator, List, Optional, ParamSpec, TypeVar, cast

from src.models.book import Book
from src.models.category import Category

# Type variables for generic retry decorator
P = ParamSpec("P")
T = TypeVar("T")


def retry_on_locked(
    max_retries: int = 3, delay: float = 0.1
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to retry database operations on locked database errors.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds

    Returns:
        Decorated function that retries on SQLite locked errors
    """

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: Optional[Exception] = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        last_exception = e
                        if attempt < max_retries - 1:  # Don't sleep on last attempt
                            time.sleep(delay * (2**attempt))  # Exponential backoff
                    else:
                        raise  # Re-raise if it's not a lock error
            # If we exhausted retries, raise the last exception
            if last_exception:
                raise last_exception
            # This should never happen, but just in case
            raise RuntimeError("Unexpected state in retry logic")

        return wrapper

    return decorator


class BookRepository:
    """Handles persistence of book metadata using SQLite."""

    def __init__(self, db_path: str):
        """Initialize the repository.

        Args:
            db_path (str): Path to the SQLite database file.
        """
        self.db_path = db_path
        self._local = threading.local()
        self._all_connections: set[sqlite3.Connection] = set()
        self._lock = threading.Lock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled."""
        if not hasattr(self._local, "conn"):
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA foreign_keys = ON")
            self._local.conn = conn
            with self._lock:
                self._all_connections.add(conn)
        return cast(sqlite3.Connection, self._local.conn)

    def _init_db(self) -> None:
        """Create the categories and books tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute("PRAGMA journal_mode=WAL")
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

    @retry_on_locked()
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

    def get_all_books(
        self, limit: Optional[int] = None, offset: int = 0
    ) -> Iterator[Book]:
        """Retrieve books from the database with optional pagination."""
        conn = self._get_connection()
        query = (
            "SELECT path, title, author, cover_path, category_id, created_at FROM books"
        )
        if limit is not None:
            query += " LIMIT ? OFFSET ?"
            cursor = conn.execute(query, (limit, offset))
        else:
            cursor = conn.execute(query)

        for row in cursor:
            yield Book(
                path=row[0],
                title=row[1],
                author=row[2],
                cover_path=row[3],
                category_id=row[4],
                created_at=datetime.fromisoformat(row[5]) if row[5] else None,
            )

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
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                )
            return None

    @retry_on_locked()
    def remove_book(self, path: str) -> None:
        """Remove a book from the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM books WHERE path = ?", (path,))
            conn.commit()

    @retry_on_locked()
    def update_book_category(self, path: str, category_id: Optional[int]) -> None:
        """Update the category of a book."""
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE books SET category_id = ? WHERE path = ?",
                (category_id, path),
            )
            conn.commit()

    @retry_on_locked()
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

    def get_books_by_category(self, category_id: Optional[int] = None) -> List[Book]:
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
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                )
                for row in cursor.fetchall()
            ]

    def get_book_count(self, category_id: Optional[int] = None) -> int:
        """Get the total number of books."""
        with self._get_connection() as conn:
            if category_id is None:
                query = "SELECT COUNT(*) FROM books"
                cursor = conn.execute(query)
            else:
                query = "SELECT COUNT(*) FROM books WHERE category_id = ?"
                cursor = conn.execute(query, (category_id,))
            return cast(int, cursor.fetchone()[0])

    def get_books_by_category_paginated(
        self, category_id: Optional[int] = None, limit: int = 1, offset: int = 0
    ) -> Optional[Book]:
        """Retrieve a single book from the database with offset."""
        with self._get_connection() as conn:
            if category_id is None:
                query = (
                    "SELECT path, title, author, cover_path, category_id, created_at "
                    "FROM books LIMIT ? OFFSET ?"
                )
                cursor = conn.execute(query, (limit, offset))
            else:
                query = (
                    "SELECT path, title, author, cover_path, category_id, created_at "
                    "FROM books WHERE category_id = ? LIMIT ? OFFSET ?"
                )
                cursor = conn.execute(query, (category_id, limit, offset))
            row = cursor.fetchone()
            if row:
                return Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                )
            return None

    def search_books(self, query: str) -> List[Book]:
        """Search for books by title or author using a keyword-based search."""
        words = query.split()
        if not words:
            return list(self.get_all_books())

        with self._get_connection() as conn:
            clauses = []
            params = []
            for word in words:
                clauses.append("(LOWER(title) LIKE ? OR LOWER(author) LIKE ?)")
                search_pattern = f"%{word.lower()}%"
                params.extend([search_pattern, search_pattern])

            where_clause = " AND ".join(clauses)
            query_str = (
                "SELECT path, title, author, cover_path, category_id, created_at "
                "FROM books "
                f"WHERE {where_clause}"
            )
            cursor = conn.execute(query_str, params)
            return [
                Book(
                    path=row[0],
                    title=row[1],
                    author=row[2],
                    cover_path=row[3],
                    category_id=row[4],
                    created_at=datetime.fromisoformat(row[5]) if row[5] else None,
                )
                for row in cursor.fetchall()
            ]

    @retry_on_locked()
    def clear(self) -> None:
        """Remove all books and categories from the database."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM books")
            conn.execute("DELETE FROM categories")
            conn.commit()
            conn.execute("VACUUM")

    def close(self) -> None:
        """Close all database connections."""
        with self._lock:
            for conn in self._all_connections:
                try:
                    conn.close()
                except sqlite3.Error:
                    pass
            self._all_connections.clear()
        if hasattr(self._local, "conn"):
            del self._local.conn
