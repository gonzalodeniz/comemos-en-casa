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

The health endpoint is available at <http://127.0.0.1:8000/health> and returns `{"status":"ok"}`. `/ready` checks the PostgreSQL connection and returns HTTP 503 when it cannot connect. For local development outside Compose, set `DATABASE_URL` to your own PostgreSQL URL before starting the server; Compose provides it to the container automatically. Never commit a real database password.

## Migrations

With `DATABASE_URL` pointing to an available PostgreSQL database, run from this directory:

```sh
alembic upgrade head
alembic current
```

The initial revision records the schema version without creating business tables.

## Smoke test

With the environment activated and dependencies installed, run from this directory:

```sh
python -m pytest -q
```
