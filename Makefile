.PHONY: lint test

lint:
	cd backend && uv run ruff check .
	cd backend && uv run lint-imports
	cd backend && uv run pyright app scripts

test:
	cd backend && uv run pytest -q
