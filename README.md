# eshelf

`eshelf` is a dedicated, modern Linux shelf application for managing and organizing digital books (EPUB, PDF). It is built with Python 3.11, leveraging the power of Libadwaita (GTK4) to provide a native and intuitive experience on the GNOME desktop.

## Key Features

- **Virtual Scrolling & Lazy Loading**: Efficiently handle thousands of books with minimal memory overhead and instant UI responsiveness using GTK4 `GridView`.
- **Keyword-based Search**: Flexible, order-independent searching across book titles and authors, integrated with lazy-loading for optimal performance.
- **PDF Content Search**: Search inside the contents of PDF books for keywords, with progress tracking and contextual snippets.
- **Library Organization**: Organize your books into custom categories with sidebar navigation.
- **Drag-and-Drop**: Supports bulk actions; move multiple books between categories instantly.
- **Modern UI**: Built with Libadwaita for a sleek, responsive design that follows GNOME standards.
- **Customizable**: Toggle between Light, Dark, or System appearance modes.
- **Easy Imports**: Recursive folder imports with background processing.
- **Performance**: High-performance library scanning with multi-threaded metadata extraction and database-level pagination.
- **Maintenance**: Automated cache pruning ensures orphaned thumbnails are cleaned up when books are removed.

## Recent Improvements (since v0.8.3)

- **Gtk.GridView Integration**: Migrated from a standard FlowBox to a virtualized GridView for significant performance improvements in large libraries.
- **Lazy Loading Model**: Implemented a custom `GListModel` that fetches book data from the database on-demand, dramatically reducing initial load times and memory usage.
- **Search Optimization**: Re-engineered search functionality to work seamlessly with the virtualized grid, ensuring fast filtering across any library size.
- **PDF Content Search**: Added ability to search inside PDF book contents for keywords with progress tracking and contextual snippets.
- **Architecture Refactor**: Cleaned up the `MainWindow` structure and improved shutdown procedures for better stability.


## Getting Started

### Prerequisites

- Python 3.11+
- `uv` (Package manager)
- GTK 4 and Libadwaita development libraries

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Obelixor-Team/eshelf.git
   cd eshelf
   ```

2. Sync dependencies:
   ```bash
   uv sync
   ```

3. Run the application:
   ```bash
   make run
   ```

## Development

We use a standard set of commands to keep the codebase clean:

- `make lint`: Run `ruff` to lint and format code.
- `make typecheck`: Run `mypy` strict type checking.
- `make test`: Run the test suite with coverage reporting.
- `make build-appimage`: Build a portable AppImage.

## Architecture

`eshelf` uses a layered architecture (`UI` -> `Controller` -> `Service` -> `Database`) to maintain a clean separation of concerns. The project is fully indexed for AI-assisted development via [GitNexus](https://gitnexus.vercel.app/).

## License

This project is licensed under the MIT License.
