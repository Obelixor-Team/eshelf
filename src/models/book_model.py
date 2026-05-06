"""A custom GListModel for lazy loading books."""

from typing import Optional

from gi.repository import Gio, GObject  # noqa: E402

from src.database.repository import BookRepository
from src.models.book import BookObject


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
            # Fetch the book from the repository
            if self.repository:
                book = self.repository.get_books_by_category_paginated(
                    self.category_id,
                    all_books=self.all_books,
                    limit=1,
                    offset=position,
                    search_query=self.search_query,
                )
                if book:
                    self._cache[position] = BookObject(book)

        return self._cache.get(position)
