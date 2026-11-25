# INDEX.md

Índice de orientación para agentes. Actualizar las entradas afectadas cuando cambie la estructura; no pretende enumerar cada archivo.

## Raíz

- `AGENTS.md`: normas del repositorio y del entorno de pruebas.
- `README.md`: arranque, configuración y pruebas.
- `COMMANDS.md`: comandos locales y condiciones de ejecución.
- `Makefile`: atajos de desarrollo; `docker-compose.yml`: entorno integrado.
- `scripts/orquestador.sh`: lanzador local de Codex con instrucciones de rol y bloqueo entre sus ejecuciones.
- `scripts/tests/`: pruebas del lanzador con Codex simulado.
- `.codex/agents/`: siete agentes TOML de Codex y sus fuentes Markdown de Claude conservadas.

## Aplicación

- `backend/app/`: API FastAPI, dominio, seguridad y configuración.
- `backend/migrations/`: migraciones Alembic; `backend/tests/`: pruebas pytest.
- `frontend/src/`: aplicación React/TypeScript y pruebas Vitest; `frontend/ui-lib/`: biblioteca de interfaz.
- `deploy/`: configuración de despliegue; `data/`: datos y recursos locales (evitar modificar datos no relacionados).

## Documentación y planificación

- `docs/project/PERFIL.md`: contexto y restricciones del proyecto para agentes.
- `docs/process/FLUJO_DE_TRABAJO.md`: flujo local de historias, tareas, revisión y auditorías.
- `docs/product-vision.md`, `docs/glosario.md`: visión y vocabulario.
- `docs/historias-usuarios/`, `docs/product/`: historias y backlogs.
- `docs/planes/`, `docs/seguimiento/`, `odd/tasks/`: planes, seguimiento nuevo y registros de tareas existentes con sus evidencias.
- `docs/arquitectura.md`: arquitectura inicial; puede contener estado histórico.
- `docs/manual/`: manuales de usuario, administración y desarrollo.
- `docs/interfaces/`: referencias de interfaz y prototipos.
