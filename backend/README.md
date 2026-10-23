# Backend

Minimal FastAPI service for the architecture foundation. No user or meal features are included.

## Start locally

From this directory, create and activate a virtual environment, install dependencies, then run:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

The health endpoint is available at <http://127.0.0.1:8000/health> and returns `{"status":"ok"}`. `/ready` checks the PostgreSQL connection and returns HTTP 503 when it cannot connect. For local development outside Compose, set `DATABASE_URL` to your own PostgreSQL URL before starting the server. Compose supplies separate `DB_HOST`, `DB_USER`, `DB_PASSWORD` and `DB_NAME` variables so passwords with URL-reserved characters work unchanged. Never commit a real database password.

## Compose configuration example

From the repository root, choose a local password (the value below is a placeholder, not a secret):

```sh
export POSTGRES_PASSWORD='<choose-your-own-local-password>'
docker compose up -d --build --wait
```

The frontend and API are available at `http://localhost:5173` and `http://localhost:8000`; do not commit your password. Compose passes the password separately rather than embedding it in a database URL.

## Migrations

With `DATABASE_URL` or Compose's `DB_*` variables pointing to an available PostgreSQL database, run from this directory:

```sh
alembic upgrade head
alembic current
```

From the repository root with Compose running, use `docker compose exec backend alembic upgrade head` (the container already has the DB variables). The initial revision records the schema version without creating business tables.

## Smoke test

With the environment activated and dependencies installed, run from this directory:

```sh
python -m pytest -q
```
