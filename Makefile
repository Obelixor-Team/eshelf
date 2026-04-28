.PHONY: run test lint typecheck clean

# Run the application
run:
	PYTHONPATH=. .venv/bin/python src/main.py

# Run tests with coverage
test:
	.venv/bin/pytest --cov=src

# Run linting and formatting
lint:
	.venv/bin/ruff check . --fix
	.venv/bin/ruff format .

# Run static type checking
typecheck:
	.venv/bin/mypy src

# Clean up cache files
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage
