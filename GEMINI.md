# eshelf — Project Instructions

`eshelf` is a dedicated Linux shelf application for managing and organizing digital books (EPUB, PDF). It is built with Python 3.11 using the Libadwaita (GTK4) framework to provide a modern, native Linux experience.

## Architecture

The project follows a layered architecture to ensure separation of concerns and maintainability:

- **UI Layer (`src/ui/`)**: Libadwaita components for the main window, book grid, sidebar, and widgets.
- **Controller Layer (`src/controller/`)**: Orchestrates interactions between the UI and the underlying services.
- **Service Layer (`src/services/`)**: Business logic for book scanning, metadata extraction (EPUB/PDF), and sorting.
- **Data Layer (`src/database/`, `src/models/`)**: Persistent storage using SQLite (with WAL mode) and Pydantic-like data models for books and categories.

## Core Technology Stack

- **Language**: Python 3.11+
- **UI Framework**: PyGObject (GTK 4.0 + Libadwaita 1.0)
- **Dependency Management**: `uv`
- **Linting & Formatting**: `ruff` (following Google docstring convention)
- **Type Checking**: `mypy` (strict mode)
- **Testing**: `pytest` with `pytest-cov`
- **Database**: SQLite (managed via `BookRepository`)

## Development Commands

Always use the `Makefile` to ensure commands run in the correct environment (`.venv`):

- `make run`: Launch the application.
- `make test`: Run the test suite with coverage reports (target >80% coverage).
- `make lint`: Run `ruff` check (with `--fix`) and format.
- `make typecheck`: Run `mypy` strict type checking.
- `make pre-commit`: Manually run all pre-commit hooks.
- `make clean`: Remove cache files and build artifacts.

## Development Conventions

- **Types**: Use strict type hinting everywhere. `mypy` must pass without errors.
- **Styling**: Adhere to `ruff` formatting. Line length is set to 88.
- **Documentation**: Use Google-style docstrings for all public modules, classes, and functions.
- **Concurrency**: Perform heavy operations (like folder imports or library scans) in background threads to keep the UI responsive. Use `GLib.idle_add` for UI updates from background threads.
- **Git**: Follow Conventional Commits. Use `uv run cz bump` for versioning, changelog generation, and automated tagging. Never manually update the version or create tags.
- **GitNexus**: This project is indexed for AI-assisted engineering.
    - Run `npx gitnexus analyze` if the index becomes stale.
    - Use `npx gitnexus serve` to explore the codebase knowledge graph at `localhost:4747`.

## File Structure Highlights

- `src/main.py`: Application entry point and initialization.
- `src/config.py`: Configuration management and persistence (JSON).
- `src/database/repository.py`: Primary interface for database operations.
- `src/ui/main_window.py`: Orchestrates the primary UI layout and state.
- `tests/`: Mirror of `src/` for unit and integration testing.
