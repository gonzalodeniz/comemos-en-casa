# Backend

FastAPI service with atomic first-account bootstrap, private account creation, login/logout, revocable sessions, profile/password routes and password-reset email adapter. T4/T6/T7 are implemented in the working branch but their full regression verification remains pending; meal features are out of scope.

## Start locally

From this directory, create and activate a virtual environment, install dependencies, then run:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --no-proxy-headers
```

The health endpoint is available at <http://127.0.0.1:8000/health> and returns `{"status":"ok"}`. `/ready` checks the PostgreSQL connection and returns HTTP 503 when it cannot connect. For local development outside Compose, set `DATABASE_URL` to your own PostgreSQL URL and `AUTH_RATE_LIMIT_HMAC_KEY` to a stable random 32-byte hexadecimal key before starting the server. Compose supplies separate `DB_HOST`, `DB_USER`, `DB_PASSWORD` and `DB_NAME` variables so passwords with URL-reserved characters work unchanged. Set `CORS_ALLOWED_ORIGINS` to a comma-separated allowlist when the UI origin differs from the local defaults. Never commit credentials or the HMAC key.

## Compose configuration example

From the repository root, choose a local password (the value below is a placeholder, not a secret):

```sh
export POSTGRES_PASSWORD='<choose-your-own-local-password>'
export AUTH_RATE_LIMIT_HMAC_KEY="$(openssl rand -hex 32)"
export APP_PUBLIC_URL='http://localhost:5173'
docker compose up -d --build --wait
```

The frontend and API are available at `http://localhost:5173` and `http://localhost:8000`; do not commit your password or HMAC key. Compose passes the password separately rather than embedding it in a database URL.

## Migrations

With `DATABASE_URL` or Compose's `DB_*` variables pointing to an available PostgreSQL database, run from this directory:

```sh
alembic upgrade head
alembic current
```

From the repository root with Compose running, use `docker compose exec backend alembic upgrade head` (the container already has the DB variables). `0001_baseline` records the initial schema version; `0002_user_auth` creates user, session, reset-token and login-attempt bucket tables; `0003_login_attempt_events` persists timestamps for rolling-window enforcement; `0004_password_reset_rate_scopes` separates recovery request counters.

## Authentication API

The versioned API supports initial registration, login/logout/session, and authenticated user listing, creation, profile changes, activation/deactivation, deletion, and password changes under `/api/v1`. Password recovery uses `POST /api/v1/password-resets` and `/confirm`; responses are generic, the token is stored as a digest, and SMTP is configured only through environment variables. `APP_PUBLIC_URL` is required for reset links. Initial registration closes atomically after the first account and does not log that account in. Writes require an explicitly allowed `Origin`; authenticated writes also require the CSRF cookie value in `X-CSRF-Token`. Login and password-reset limits are shared in PostgreSQL and use HMAC digests with a stable `AUTH_RATE_LIMIT_HMAC_KEY` across instances.

## Smoke test

With the environment activated and dependencies installed, run from this directory:

```sh
python -m pytest -q
```
