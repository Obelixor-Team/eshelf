"""Tests for the BookListModel class."""

from unittest.mock import MagicMock

from src.database.repository import BookRepository
from src.models.book import Book
from src.models.book_model import BookListModel


def test_book_model_cache_stale_data():
    """Verify that BookListModel returns stale data if cache is not cleared."""
    mock_repo = MagicMock(spec=BookRepository)
    model = BookListModel(repository=mock_repo)

    book1 = Book(path="/tmp/book1.epub", title="Original Title", author="Author")

    mock_repo.get_book_count.return_value = 1
    # First call to get_item(0) will fetch from repo
    mock_repo.get_books_by_category_paginated.return_value = book1

    # Initialize model
    model._n_items = 1

    item1 = model.do_get_item(0)
    assert item1.title == "Original Title"
    assert 0 in model._cache

    # Update book in repo
    updated_book1 = Book(path="/tmp/book1.epub", title="Updated Title", author="Author")
    mock_repo.get_books_by_category_paginated.return_value = updated_book1

    # Second call to get_item(0) should come from cache
    item2 = model.do_get_item(0)
    assert item2.title == "Original Title"  # Still old title because of cache
    assert item2 == item1


def test_book_model_invalidate_cache():
    """Verify that invalidate_cache clears the cache and updates data."""
    mock_repo = MagicMock(spec=BookRepository)
    model = BookListModel(repository=mock_repo)

    book1 = Book(path="/tmp/book1.epub", title="Original Title", author="Author")
    mock_repo.get_book_count.return_value = 1
    mock_repo.get_books_by_category_paginated.return_value = book1
    model._n_items = 1

    model.do_get_item(0)

    # Update book in repo
    updated_book1 = Book(path="/tmp/book1.epub", title="Updated Title", author="Author")
    mock_repo.get_books_by_category_paginated.return_value = updated_book1

    model.invalidate_cache()

    item_updated = model.do_get_item(0)
    assert item_updated.title == "Updated Title"


def test_book_model_cache_emits_signal():
    """Verify that BookListModel emits items-changed signal on invalidation."""
    mock_repo = MagicMock(spec=BookRepository)
    model = BookListModel(repository=mock_repo)

    mock_repo.get_book_count.return_value = 5
    model._n_items = 5

    signal_received = []

    def on_items_changed(m, position, removed, added):
        signal_received.append((position, removed, added))

    model.connect("items-changed", on_items_changed)

    mock_repo.get_book_count.return_value = 3
    model.invalidate_cache()

    assert len(signal_received) == 1
    assert signal_received[0] == (0, 5, 3)
