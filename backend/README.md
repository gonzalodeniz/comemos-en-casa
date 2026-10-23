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

The health endpoint is available at <http://127.0.0.1:8000/health> and returns `{"status":"ok"}`.

## Smoke test

With the environment activated and dependencies installed, run from this directory:

```sh
python -m pytest -q
```
