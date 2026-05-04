# eshelf

`eshelf` is a dedicated, modern Linux shelf application for managing and organizing digital books (EPUB, PDF). It is built with Python 3.11, leveraging the power of Libadwaita (GTK4) to provide a native and intuitive experience on the GNOME desktop.

## Key Features

- **Keyword-based Search**: Flexible, order-independent searching across book titles and authors.
- **Library Organization**: Organize your books into custom categories with sidebar navigation.
- **Modern UI**: Built with Libadwaita for a sleek, responsive design that follows GNOME standards.
- **Customizable**: Toggle between Light, Dark, or System appearance modes.
- **Easy Imports**: Recursive folder imports with background processing to keep the UI responsive.
- **Performance**: High-performance library scanning with multi-threaded metadata extraction.

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
