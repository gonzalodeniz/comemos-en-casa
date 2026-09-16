# Índice del repositorio

Este documento describe la estructura actual del proyecto. Actualízalo cuando cambien las rutas o responsabilidades principales.

## Directorios principales

- `backend/src/comemos_en_casa/`: código fuente del backend Python.
- `backend/tests/`: pruebas del backend, organizadas por funcionalidad:
  - `auth/`: autenticación.
  - `collections/`: colecciones y favoritos.
  - `meal_calendar/`: planificación del calendario.
  - `recipes/`: gestión de recetas.
- `backend/alembic/`: configuración y recursos de Alembic.
- `backend/migrations/`: migraciones de base de datos.
- `frontend/src/`: código fuente del frontend React/TypeScript.
- `frontend/public/`: recursos estáticos públicos del frontend.
- `tests/`: pruebas smoke del repositorio.
- `prototipos/`: imágenes de referencia de la interfaz.
- `scripts/`: scripts auxiliares de configuración y ejecución.

## Ficheros relevantes

- `Makefile`: accesos rápidos para desarrollo, Docker y pruebas.
- `docker-compose.yml`: servicios locales de PostgreSQL, backend y frontend.
- `pyproject.toml`: configuración de Pytest.
- `frontend/package.json`: scripts y dependencias del frontend.
- `.env`: configuración local; contiene información sensible y no debe versionarse.

## Ficheros de instrucciones

- `AGENTS.md`: reglas de comportamiento para contribuyentes y agentes.
- `CLAUDE.md`: copia idéntica de `AGENTS.md` para Claude.
- `COMMANDOS.md`: operativa de instalación, desarrollo y verificación.
