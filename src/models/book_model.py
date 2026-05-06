"""A custom GListModel for lazy loading books.

This class is not thread-safe and should only be accessed from the main thread.
"""

from typing import Optional

from gi.repository import Gio, GObject  # noqa: E402

from src.database.repository import BookRepository
from src.models.book import Book, BookObject


class BookListModel(GObject.Object, Gio.ListModel):  # type: ignore
    """A lazy-loading ListModel for books."""

    def __init__(
        self,
        repository: Optional[BookRepository] = None,
        category_id: Optional[int] = None,
        all_books: bool = False,
        search_query: Optional[str] = None,
    ) -> None:
        """Initialize the model."""
        super().__init__()
        self.repository = repository
        self.category_id = category_id
        self.all_books = all_books
        self.search_query = search_query
        self._n_items = self._get_count()
        self._cache: dict[int, BookObject] = {}

    def _get_count(self) -> int:
        """Get the total number of books."""
        if not self.repository:
            return 0
        return self.repository.get_book_count(
            self.category_id, all_books=self.all_books, search_query=self.search_query
        )

    def do_get_item_type(self) -> GObject.GType:
        """Return the GType of the items in the list."""
        return BookObject.__gtype__

    def do_get_n_items(self) -> int:
        """Return the total number of items."""
        return self._n_items

    def do_get_item(self, position: int) -> Optional[BookObject]:
        """Return the item at the given position."""
        if position >= self._n_items:
            return None

        if position not in self._cache:
            # Fetch a chunk of books from the repository
            if self.repository:
                chunk_size = 50
                # Calculate the start of the chunk (aligned to chunk_size)
                chunk_offset = (position // chunk_size) * chunk_size
                books = self.repository.get_books_by_category_paginated(
                    self.category_id,
                    all_books=self.all_books,
                    limit=chunk_size,
                    offset=chunk_offset,
                    search_query=self.search_query,
                )
                if isinstance(books, Book):
                    books = [books]
                for i, book in enumerate(books):
                    self._cache[chunk_offset + i] = BookObject(book)

        return self._cache.get(position)

    def invalidate_cache(self) -> None:
        """Clear the cache and notify listeners of changes."""
        old_n_items = self._n_items
        self._n_items = self._get_count()
        self._cache.clear()
        self.items_changed(0, old_n_items, self._n_items)
