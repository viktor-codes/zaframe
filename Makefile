.PHONY: lint test

lint:
	cd backend && uv run ruff check .
	cd backend && uv run lint-imports

test:
	cd backend && uv run pytest -q
