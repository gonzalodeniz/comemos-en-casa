# COMMANDS.md

Comandos locales del proyecto, desde la raíz salvo que se indique otra cosa. Las definiciones proceden del `Makefile`, los archivos de configuración y `README.md`; que un comando exista **no significa** que se haya ejecutado o verificado en esta adaptación.

Verificados en esta adaptación: `make help`, `cd frontend && npm test` (229 pruebas) y `cd frontend && npm run build`. No se han ejecutado pruebas backend ni servicios Compose.

## Consulta

- `make help`: muestra los atajos definidos.

## Agentes locales

Para iniciar una sesión se necesita Codex CLI, `flock` y Python 3.11 o posterior. Pasa la tarea como un único argumento entre comillas. Si omites el rol, se usa `orquestador`.

- `./scripts/orquestador.sh --list`: muestra los roles disponibles.
- `./scripts/orquestador.sh <rol> "<tarea>"`: inicia Codex interactivo con las instrucciones del rol como contexto del agente principal.
- `./scripts/orquestador.sh security-auditor` o `./scripts/orquestador.sh quality-auditor`: sin mensaje, solicita una auditoría completa del repositorio local, sin modificar código, consultar servicios remotos ni delegar. También funciona con `--auto`. Los demás roles requieren una tarea explícita.
- `./scripts/orquestador.sh --auto <rol> "<tarea>"`: ejecuta Codex sin leer la entrada estándar y escribe la salida en `logs/` (puede incluir datos sensibles). Un fallo al guardar el registro devuelve un código distinto de cero. No concede permisos ni autoriza acciones adicionales.

## Pruebas y build

- `python3 -m unittest discover -s scripts/tests -v`: pruebas del lanzador con ejecutables simulados, sin abrir sesiones de Codex.

- `cd frontend && npm test`: pruebas Vitest.
- `cd frontend && npm run build`: comprobación TypeScript y build de Vite.
- `cd backend && ../.venv/bin/python -m pytest -q`: pytest backend. Las pruebas que usan `TestClient` deben ejecutarse fuera del sandbox mediante aprobación; no repetirlas si quedan bloqueadas.
- `make test`, `make test-backend`: incluyen pruebas backend y requieren ejecución fuera del sandbox mediante aprobación.
- `make test-frontend` y `make build-frontend`: atajos de pruebas y build frontend.

Las pruebas de integración PostgreSQL requieren una base y un proyecto Compose nuevos y aislados, y `RUN_DB_INTEGRATION=1`; consultar el procedimiento completo del README. Nunca ejecutarlas contra datos que deban conservarse.

## Entorno local

- `make up`: construye e inicia Compose; requiere configuración previa documentada en el README.
- `make alembic-upgrade`: aplica migraciones al entorno Compose configurado; verificar antes el destino y preservar los datos.
- `make mailhog-up`: inicia captura de correo de desarrollo; no usar datos reales.
- `cd frontend && npm run dev`: Vite con recarga.
- `cd backend && ../.venv/bin/python -m uvicorn app.main:app --reload --no-proxy-headers`: API local sin confiar en cabeceras proxy.

El seguimiento del flujo se realiza en `docs/` y en los registros existentes de `odd/tasks/`, sin GitHub. Para cualquier operación remota, incluidos despliegue y transferencia de archivos, se necesita autorización explícita previa del destino, operación y credencial o sesión. Los comandos de publicación y certificados no forman parte de una validación local rutinaria.
