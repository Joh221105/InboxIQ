.PHONY: install dev test lint typecheck format migrations

install:
	cd frontend && npm install
	cd backend && pip install -r requirements.txt

dev:
	cd frontend && npx concurrently \
		"npm run dev" \
		"sh -c 'cd ../backend && uvicorn app.main:app --reload --host 127.0.0.1 --port 8000'"

test:
	cd backend && python -m pytest tests/ -v
	cd frontend && npm test

lint:
	cd backend && ruff check app/ tests/
	cd frontend && npm run lint

typecheck:
	cd backend && mypy app/
	cd frontend && npx tsc --noEmit

format:
	cd backend && ruff format app/ tests/

migrations:
	cd backend && python scripts/print_migrations.py
