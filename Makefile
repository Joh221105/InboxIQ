.PHONY: install dev test lint typecheck format migrations

install:
	cd backend && python3.11 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
	cd frontend && npm ci

dev:
	cd frontend && npx concurrently -n api,web \
		"cd ../backend && .venv/bin/uvicorn app.main:app --reload --port 8000" \
		"npm run dev"

test:
	cd backend && .venv/bin/pytest -q
	cd frontend && npm test

lint:
	cd backend && .venv/bin/ruff check app tests scripts && .venv/bin/ruff format --check app tests scripts
	cd frontend && npm run lint

typecheck:
	cd backend && .venv/bin/mypy app
	cd frontend && npm run typecheck

format:
	cd backend && .venv/bin/ruff check --fix app tests scripts && .venv/bin/ruff format app tests scripts

migrations:
	@python3 backend/scripts/print_migrations.py
