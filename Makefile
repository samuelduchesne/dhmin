.PHONY: install dev lint format typecheck check clean

## Install the package
install:
	uv pip install -e .

## Install with dev dependencies and pre-commit hooks
dev:
	uv pip install -e ".[dev,plot]"
	pre-commit install

## Run ruff linter
lint:
	ruff check dhmin/

## Run ruff linter with auto-fix
fix:
	ruff check --fix dhmin/

## Run ruff formatter
format:
	ruff format dhmin/

## Run pyright type checker
typecheck:
	pyright dhmin/

## Run all checks (lint + typecheck)
check: lint typecheck

## Remove build artifacts and caches
clean:
	rm -rf build/ dist/ *.egg-info .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
