.PHONY: lint test e2e e2e-critical booking-lifecycle

lint:
	cd backend && uv run ruff check .
	cd backend && uv run lint-imports
	cd backend && uv run pyright app scripts

test:
	cd backend && uv run pytest -q

e2e:
	cd frontend && npm run test:e2e

e2e-critical:
	cd frontend && npm run test:e2e:critical

booking-lifecycle:
	cd backend && uv run python -m scripts.run_booking_lifecycle
