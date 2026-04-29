.PHONY: help run test lint typecheck clean pre-commit

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

run: ## Run the application
	PYTHONPATH=. .venv/bin/python src/main.py

test: ## Run tests with coverage
	.venv/bin/pytest --cov=src

lint: ## Run linting and formatting
	.venv/bin/ruff check . --fix
	.venv/bin/ruff format .

typecheck: ## Run static type checking
	.venv/bin/mypy src

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

clean: ## Clean up cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage
