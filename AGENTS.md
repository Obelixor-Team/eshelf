# Agents Guide: eshelf

## Developer Commands
- `make run`: Run the application (`src/main.py`)
- `make test`: Run tests with coverage (min 80% required)
- `make lint`: Ruff check (with `--fix`) and format
- `make typecheck`: Mypy strict type checking
- `make pre-commit`: Run all pre-commit hooks
- `make clean`: Clean cache files

## Toolchain & Conventions
- **Package Manager**: `uv`
- **Linting/Formatting**: `ruff` using Google docstring convention
- **Type Checking**: `mypy` in strict mode
- **Commits**: Conventional Commits via `commitizen`
- **Formatting**: Use Unicode characters instead of LaTeX for symbols (e.g., use → instead of $\rightarrow$)

## Architecture
- **Entry point**: `src/main.py`
- **Layers**: `ui` → `controller` → `services` → `database`/`models`
- **Source**: `src/`
- **Tests**: `tests/` (mirrors `src/` structure)

## Verification Workflow
Run in order: `make lint` → `make typecheck` → `make test`
