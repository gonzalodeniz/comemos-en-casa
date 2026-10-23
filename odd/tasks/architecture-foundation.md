# Architecture foundation — execution tasks
Objective: Implement the approved [architecture foundation plan](../../docs/planes/arquitectura-base.md) on `feat/architecture-foundation`; HU-001 and HU-002 remain out of scope.
Delivery: auto-chain, chain_strategy=feature-branch-chain (user-selected); estimated ~400–600 authored lines, split into reviewable work-unit commits. Checks: pytest, frontend checks, isolated PostgreSQL integration, Docker Compose when available.

## Specs

S1. User request (verbatim): «crea una nueva rama para la implementación de la arquitectura; crea un plan para la implementación y espera mi aprobación.» The branch exists; the plan linked above is the approved scope.
S2. User approval and current request (verbatim): «aprobado el plan. genera los ficheros de tareas».
S3. Approved plan, unit 1 (verbatim): «Proyecto React + TypeScript con Vite y API FastAPI con una respuesta de salud básica; comandos de desarrollo y pruebas mínimas de arranque.» Check: frontend/backend start and focused checks pass.
S4. Approved plan, unit 2 (verbatim): «PostgreSQL en Compose con volumen persistente; configuración por variables de entorno sin secretos en el repositorio; API conectada a la base y comprobación de disponibilidad; migraciones versionadas con una revisión inicial sin tablas de negocio.» Check: connection failure is reflected in readiness, baseline revision is recorded, and no business tables are created.
S5. Approved plan, unit 3 (verbatim): «Prueba de integración contra una base aislada para confirmar conexión y versión de migración; verificación de persistencia tras reiniciar servicios sin borrar volúmenes; instrucciones para configurar, arrancar, migrar y ejecutar pruebas.» Check: isolated integration check and documented local restart demonstrate persistence.
S6. Approved plan, boundary (verbatim): «Quedan fuera de esta etapa la implementación de HU-001, HU-002, la carga de etiquetas predeterminadas, el correo, el despliegue remoto y las copias de seguridad.» Check: no feature implementation or unapproved delivery is included.

## Tasks

T1 | S3,S6 | delegated | done | commit: b726d2e — scaffold FastAPI and Vite/React TypeScript with smoke tests; document start commands alongside behavior.
T2 | S4,S6 | delegated | done | commits: e72d4c9, 4f3d747, 9c4bf0c — wire PostgreSQL and Docker Compose, environment example, readiness and versioned baseline migration; prove failure path and migration state.
T3 | S5,S6 | inline | done | commits: 6b8776f, bc9b546 — add isolated integration checks, verify persistence without deleting volumes, complete reproducible startup/test documentation and final checks.

## Log

L1. Original user request (verbatim): «crea una nueva rama para la implementación de la arquitectura; crea un plan para la implementación y espera mi aprobación.»
L2. Later user request (verbatim): «organiza los ficheros de plan y tasks de algún modo coherente».
L3. Approval and task-file request (verbatim): «aprobado el plan. genera los ficheros de tareas».
L4. Evidence: `feat/architecture-foundation` branches from `96e0e7f`. The plan was approved; T1–T3 were not implemented or checked at task-file creation.
L5. User authorized implementation (verbatim): «puedes comenzar la implementación.» T1 routed to a scoped writer by context backstop. Python pytest was initially unavailable; installed in local ignored `.venv`.
L6. T1 evidence: `b726d2e`. Backend pytest 1 passed, frontend Vitest 1 passed and Vite build passed; backend `/health` and frontend dev server answered over HTTP. Independent risk-item-5 verifier reproduced tests/build and endpoint. Native ASSESS high via item 5 escalation, reviewDue false (`under_budget`), so no native review START. Initial frontend build typecheck failure was fixed by using `vitest/config`.
L7. T2 evidence: `e72d4c9`; Docker Compose isolated stack up/healthy, API `/ready` 200, migration `0001_baseline` recorded, only `alembic_version` public table; pytest 3 passed. Independent verifier found reserved-character password URL regression and missing configuration example. RED `test_compose_config.py` KeyError, GREEN 4 pytest passed after separate DB vars and URL.create; isolated Docker stack with `pa@ss` and Alembic upgrade/current passed. `.env.example` writer path safeguard denied; example will be documented in guide, no sensitive file written. Cumulative authored lines exceeded ~400; delivery choice requested before correction commit.
L8. User chose `feature-branch-chain` for reviewable delivery slices. Slice 1: `c22a69b..b726d2e` (T1, ~251 authored lines). Slice 2: `e72d4c9..4f3d747` (T2 + correction, ~305 authored lines). No push or PR authorized.
L9. T2 correction `4f3d747`: reserved-character password passes through Compose as separate variables; Docker stack with `pa@ss` healthy; Alembic upgrade/current passed. Independent risk-item-5 verifier checked both runtime and migration URL round-trip with `pa@ss:%/x`; backend 4 tests, frontend 1 test and build passed. Native ASSESS high by item 5 escalation, reviewDue false (`under_budget`), no review START.
L10. T3 evidence: `6b8776f` and `bc9b546`. Isolated Compose project: integration RED before baseline migration (missing version), GREEN 1 passed after migration, GREEN 1 passed after normal stop/up (no `down -v`). With PostgreSQL stopped, `/health` HTTP 200 and `/ready` HTTP 503; recovery HTTP 200. Local backend 4 passed, 1 integration skipped (no DB env), frontend 1 passed + build. Independent risk-item-5 verifier checked code/test path and relied on parent isolated Docker evidence; no blocker. Docker Compose `start --wait` failed unsupported flag and guide was corrected to `up -d --wait`. Native ASSESS high via item 5 with reviewDue false for test-image commit; docs correction passive.
L11. Delivery boundaries (no publication): slice 1 `b726d2e`; slice 2 `e72d4c9, 4f3d747`; slice 3 `6b8776f, bc9b546, 1873758, 9c4bf0c` plus closing ledger commit. The reviewable branch is local, PR/push/merge not authorized.
L12. Closing check found Compose published ports on every host interface rather than localhost. T2 reopened: RED Compose config test (missing host_ip), GREEN 5 backend passed / 1 integration skipped and frontend test/build passed. Isolated Docker stack showed frontend/backend published only on 127.0.0.1, PostgreSQL unpublished, `/ready` 200; down preserved volume. Security item 2 verifier independently confirmed config and tests; native ASSESS high via item 2, reviewDue false (`under_budget`). Fixed in `9c4bf0c`.
