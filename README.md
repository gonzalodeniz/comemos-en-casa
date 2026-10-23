# Comemos en casa — base local

Esta rama prepara React/TypeScript, FastAPI y PostgreSQL. La gestión de usuarios, las etiquetas y la planificación todavía no están implementadas; consultá el [plan aprobado](docs/planes/arquitectura-base.md).

## Arranque local

Requisitos: Docker con Compose. Elegí una contraseña propia para la base local; no la guardes en Git. Configuración de ejemplo (el texto entre `< >` es un marcador, no una contraseña):

```sh
export POSTGRES_PASSWORD='<elegí-una-contraseña-local>'
docker compose up -d --build --wait
docker compose exec backend python -m alembic upgrade head
```

React: <http://localhost:5173>. API: <http://localhost:8000/health> (proceso vivo) y <http://localhost:8000/ready> (conexión a PostgreSQL; HTTP 503 cuando no está disponible). Compose conserva PostgreSQL en el volumen `postgres_data`. La migración inicial solo registra `0001_baseline`; aún no crea tablas de negocio. Opcionalmente, `POSTGRES_USER` y `POSTGRES_DB` modifican usuario y nombre de base.

## Pruebas

Para probar la integración, usá un **proyecto Compose aislado** sobre una base nueva; no ejecutes estas comprobaciones contra datos que quieras conservar. Si ya tenés otra instancia ocupando los puertos 8000 o 5173, detenela primero o usá otra máquina. Desde la raíz:

```sh
PROJECT="cec-foundation-test-$$"
docker compose -p "$PROJECT" up -d --build --wait
docker compose -p "$PROJECT" exec -T backend python -m alembic upgrade head
docker compose -p "$PROJECT" exec -T -e RUN_DB_INTEGRATION=1 backend python -m pytest -q
docker compose -p "$PROJECT" stop
docker compose -p "$PROJECT" up -d --wait
docker compose -p "$PROJECT" exec -T backend python -m alembic current
docker compose -p "$PROJECT" exec -T -e RUN_DB_INTEGRATION=1 backend python -m pytest -q tests/test_database_integration.py
```

La prueba de integración debe pasar después de migrar y nuevamente tras el reinicio: la versión persiste. Para detener el proyecto de prueba sin borrar sus datos, ejecutá `docker compose -p "$PROJECT" down` (sin `-v`). El nombre del proyecto y el volumen quedan separados del entorno habitual.

Si ya instalaste dependencias locales, las pruebas aisladas de la API se ejecutan con `cd backend && python -m pytest -q` y las del frontend con `cd frontend && npm test && npm run build`. La prueba de integración se omite en la suite local salvo que establezcas `RUN_DB_INTEGRATION=1` con una base aislada. Consultá también [backend/README.md](backend/README.md) y [frontend/README.md](frontend/README.md).
