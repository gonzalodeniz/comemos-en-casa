# Repository Guidelines

## Project Structure & Module Organization

This repository is a small full-stack foundation, not yet a user-facing meal-planning application. `backend/` contains the FastAPI service (`app/`), Alembic migrations (`migrations/`), and pytest tests (`tests/`). `frontend/` contains the React/TypeScript Vite app and its Vitest tests under `src/`. `docs/` holds architecture, product, and planning material; `odd/tasks/` contains the architecture task ledger. Docker Compose configuration is at the repository root. Keep changes within the relevant service and update documentation when behavior or setup changes.

## Build, Test, and Development Commands

Use Docker Compose from the root for the integrated local environment:

- `docker compose up -d --build --wait` builds and starts PostgreSQL, API, and frontend.
- `docker compose exec backend python -m alembic upgrade head` applies database migrations.
- `cd backend && python -m pytest -q` runs API tests; use `cd frontend && npm test` for frontend tests.
- `cd frontend && npm run build` type-checks and produces the production Vite bundle.
- `cd backend && uvicorn app.main:app --reload --no-proxy-headers` and `cd frontend && npm run dev` start each service independently. Keep proxy headers disabled unless trusted-proxy configuration is explicitly introduced.

Run database integration tests only against a fresh, isolated Compose project/database; set `RUN_DB_INTEGRATION=1` as documented in the root README. Do not run them against data you need to preserve.

## Coding Style & Naming Conventions

Follow the existing Python, TypeScript, and React patterns. Use clear descriptive names; React components use PascalCase, Python modules and functions use snake_case, and tests use `test_*.py` or `*.test.tsx`. Keep configuration and secrets out of source control; use environment variables for local database credentials. There is no repository-wide formatter or linter command currently documented, so avoid introducing one without updating project guidance.

Siempre que sea posible, escribe el código en español, incluidos los nombres de variables, funciones, métodos, clases, módulos y archivos. Conserva en su idioma original los nombres exigidos por bibliotecas, protocolos, contratos públicos o convenciones existentes cuando traducirlos pueda romper la compatibilidad o la coherencia.

Add a brief Spanish comment explaining the purpose of every new function, method, class, or other declaration written in a file. For especially important or complex functions and classes, the comment may be more detailed.

## Testing Guidelines

Add or update focused tests alongside the code they cover. Backend tests use pytest; frontend tests use Vitest. Run the relevant suite and frontend production build before submitting. Integration tests require PostgreSQL and must verify migration behavior on an isolated database.

## Commit & Pull Request Guidelines

Recent history uses Conventional Commit-style prefixes such as `docs:`, `fix:`, and `test:`. Use a concise imperative subject (for example, `fix: bind local development ports to loopback`). Pull requests should explain the change and rationale, link related issues or planning documents, list validation commands and outcomes, and include screenshots for visible UI changes. Call out migration or configuration impacts explicitly.

## Python test environment

Run backend pytest commands with the repository virtual environment: `.venv/bin/python -m pytest ...` from the repository root, or `../.venv/bin/python -m pytest ...` from `backend/`.

### Pruebas y sandbox

- No ejecutes `make test`, `make test-backend` ni pruebas backend que utilicen `TestClient` dentro del sandbox. Solicita su ejecución fuera del sandbox mediante el mecanismo de aprobación del entorno.
- Causa verificada: el sandbox bloquea con `EPERM` el envío por el socket local que asyncio utiliza para despertar su bucle desde otro hilo. AnyIO/TestClient queda esperando sin mostrar progreso; no es un fallo demostrado de la aplicación.
- Si la ejecución fuera del sandbox no está autorizada o disponible, informa de la limitación. No repitas ejecuciones bloqueadas, no omitas pruebas ni modifiques asyncio/AnyIO para eludir la restricción.
- Las pruebas frontend (`make test-frontend`) pueden ejecutarse dentro del sandbox.
