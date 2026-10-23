# Repository Guidelines

## Project Structure & Module Organization

This repository is a small full-stack foundation, not yet a user-facing meal-planning application. `backend/` contains the FastAPI service (`app/`), Alembic migrations (`migrations/`), and pytest tests (`tests/`). `frontend/` contains the React/TypeScript Vite app and its Vitest tests under `src/`. `docs/` holds architecture, product, and planning material; `odd/tasks/` contains the architecture task ledger. Docker Compose configuration is at the repository root. Keep changes within the relevant service and update documentation when behavior or setup changes.

## Build, Test, and Development Commands

Use Docker Compose from the root for the integrated local environment:

- `docker compose up -d --build --wait` builds and starts PostgreSQL, API, and frontend.
- `docker compose exec backend python -m alembic upgrade head` applies database migrations.
- `cd backend && python -m pytest -q` runs API tests; use `cd frontend && npm test` for frontend tests.
- `cd frontend && npm run build` type-checks and produces the production Vite bundle.
- `cd backend && uvicorn app.main:app --reload` and `cd frontend && npm run dev` start each service independently.

Run database integration tests only against a fresh, isolated Compose project/database; set `RUN_DB_INTEGRATION=1` as documented in the root README. Do not run them against data you need to preserve.

## Coding Style & Naming Conventions

Follow the existing Python, TypeScript, and React patterns. Use clear descriptive names; React components use PascalCase, Python modules and functions use snake_case, and tests use `test_*.py` or `*.test.tsx`. Keep configuration and secrets out of source control; use environment variables for local database credentials. There is no repository-wide formatter or linter command currently documented, so avoid introducing one without updating project guidance.

## Testing Guidelines

Add or update focused tests alongside the code they cover. Backend tests use pytest; frontend tests use Vitest. Run the relevant suite and frontend production build before submitting. Integration tests require PostgreSQL and must verify migration behavior on an isolated database.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style prefixes such as `docs:`, `fix:`, and `test:`. Use a concise imperative subject (for example, `fix: bind local development ports to loopback`). Pull requests should explain the change and rationale, link related issues or planning documents, list validation commands and outcomes, and include screenshots for visible UI changes. Call out migration or configuration impacts explicitly.
