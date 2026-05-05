# Improvement Plan for eshelf

This plan outlines potential architectural and functional improvements for `eshelf`, building on the recent stability fixes.

## 1. Database & Persistence Layer
- **Implement Connection Pooling**: The current `threading.local()` connection approach is adequate but could be more robust. Evaluate using a proper connection pool for better resource management.
- **Full-Text Search (FTS5)**: The current search logic uses `LIKE %word%`, which is slow for large collections. Enabling SQLite's FTS5 extension would significantly improve search performance and relevance.
- **Asynchronous Database Operations**: While serializing writes solved the race condition, long-running database operations (e.g., clearing the library, large bulk imports) still block the main thread. Transitioning to an async database interface (e.g., using `aiosqlite`) would keep the UI fluid during intensive database tasks.

## 2. UI/UX Enhancements
- **Virtual Scrolling for ShelfGrid**: Currently, `ShelfGrid` loads all items into a `ListStore`, which can lead to memory overhead and UI lag with large libraries. Implementing a `Gtk.ListView` with a custom model that loads data on-demand (lazy loading) would improve performance.
- **Graceful Shutdown**: Implement a robust shutdown sequence using `threading.Event` to ensure all background threads (scanner, importer) complete their current work or exit cleanly, and database connections are closed properly before exiting.
- **Enhanced Search UI**: Add real-time search with a debounced input field, and visual feedback for the current search context (e.g., highlighting matches).

## 3. Testing & Quality Assurance
- **End-to-End (E2E) Testing**: Introduce E2E tests using a framework like `dogtail` or simply by automating common user flows via PyGObject to ensure regressions don't slip into the core UI.
- **Integration Test Suite**: Expand the current test coverage to specifically target the integration between the `MainController` and `BookScanner` to ensure that future concurrency changes don't re-introduce race conditions.

## 4. Feature Additions
- **Plugin System**: Introduce a simple plugin architecture for metadata extraction (e.g., support for Amazon/Goodreads/OpenLibrary APIs) so that users can expand support without modifying core services.
- **Import Queue UI**: Add a dedicated "Task Queue" view in the UI where users can track the progress of ongoing imports/scans, cancel them, or view detailed logs.

---
*Status: This is a living list of potential improvements. Please choose a focus area to prioritize for future development.*
