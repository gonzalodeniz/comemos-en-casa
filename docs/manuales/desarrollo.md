# Manual de desarrollo

## Arranque con Docker Compose

Para levantar PostgreSQL, FastAPI y el frontend juntos:

```bash
docker compose up --build
```

- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- PostgreSQL: `localhost:5433`

En una base nueva, PostgreSQL ejecuta las migraciones SQL históricas desde `backend/migrations/versions/` durante la inicialización del volumen. Si el volumen ya existía, las migraciones no se repiten automáticamente; aplícalas o registra el baseline siguiendo la sección de migraciones.

## Comandos Make

Ejecuta `make` sin argumentos para mostrar todas las opciones. Las más habituales son:

```bash
make up       # levantar la aplicación
make down     # parar los contenedores
make logs     # seguir los logs
make test     # ejecutar backend y frontend
make ps       # consultar el estado
```

## Backend

Requisitos: Python, PostgreSQL y el entorno virtual del proyecto.

```bash
.venv/bin/pip install -r requirements-dev.txt
export DATABASE_URL='postgresql://comemos:comemos_dev_password@localhost:5433/comemos_en_casa'
```

La aplicación FastAPI vive en `backend/src/comemos_en_casa/app.py` y se ejecuta con:

```bash
PYTHONPATH=backend/src .venv/bin/uvicorn comemos_en_casa.app:app --reload
```

Comprobación rápida:

```bash
curl http://localhost:8000/health
```

## Migraciones

Las migraciones históricas están en `backend/migrations/versions/` y se aplican en este orden:

1. `0001_meal_calendar_foundation.sql`
2. `0002_recipe_catalogue_foundation.sql`
3. `0003_meal_calendar_recipe_fk.sql`

Alembic conserva ese historial como baseline. En una base existente, después de comprobar que contiene el esquema correspondiente, registrar el baseline con:

```bash
DATABASE_URL="$DATABASE_URL" PYTHONPATH=backend/src .venv/bin/alembic -c alembic.ini stamp 0000_baseline
```

Las revisiones nuevas de Alembic se añadirán después del baseline. No se deben volver a ejecutar las migraciones históricas sobre una base que ya las aplicó.

## Frontend

El frontend está en `frontend/` y usa React, TypeScript, Vite, React Router, CSS Modules y `useReducer`.

```bash
npm --prefix frontend install
npm --prefix frontend run dev
```

Verificación de producción:

```bash
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

## Pruebas

Backend:

```bash
PYTHONPATH=backend/src .venv/bin/pytest -q
```

Frontend:

```bash
npm --prefix frontend run typecheck
npm --prefix frontend run build
```

## Contrato HTTP actual

La API del calendario usa el prefijo `/api/v1/meal-calendar`:

- `GET /context`
- `GET /weeks/{weekStart}`
- `GET /recipes?q=&cursor=&limit=`
- `GET /recipes/{recipeId}`
- `POST /assignments`
- `PATCH /assignments/{assignmentId}`
- `DELETE /assignments/{assignmentId}`

Las respuestas usan `Cache-Control: no-store`. El acceso invitado está habilitado por defecto mediante `ENABLE_GUEST_USER`; si se desactiva antes de integrar autenticación, las rutas del calendario responden `401 authentication_required`.

## Límites actuales

- Rate limit: 60 lecturas y 30 escrituras por IP y minuto.
- Reintentos de conexión PostgreSQL: una repetición adicional para errores transitorios.
- Las recetas son siempre públicas.
- La autenticación y la gestión completa de recetas aún no están implementadas.
