# Apply progress: repetir-comidas-calendario

## Slice boundary

- Delivery path: slice 1 of 4, stacked-to-main chain, backend persistence/domain foundations only.
- Review workload: the full change forecast is high risk at 900–1,300 lines; this assigned slice is limited to migration, domain validation, pure expansion, focused backend tests, and migration documentation.
- No repository, API, frontend, or occurrence-materialization work was implemented.

## Structured status consumed

- Change: `repetir-comidas-calendario`
- Native state: `ready`; recommended action consumed: `apply`.
- Artifact store: `openspec`; proposal, spec, design, and tasks were read before editing.
- Action context: `repo-local`, workspace `/opt/apps/comemos-en-casa`, allowed edit root `/opt/apps/comemos-en-casa`.
- Warning: the native status listed no apply-progress locator; this file is the first cumulative progress artifact.
- Delivery decision: the parent prompt resolved the workload gate as slice 1 of 4 with stacked-to-main, so no size exception was used.

## Completed implementation tasks

- [x] Task 1: added RED tests for migration shape, shared rule constraints, absent generated-date storage, recurrence validation, inclusive weekly expansion, interval boundaries, month/year crossings, and future anchors.
- [x] Task 2: added migration `0007`, migration documentation, `RECURRENCE_INTERVALS`, `RecurrenceRuleDraft`, and validated `RecurrenceRule` domain values. Recurrence remains free-text-only and shared-calendar-only.
- [x] Task 3: added pure civil-date `occurrence_in_week` expansion with inclusive Monday–Sunday boundaries and `7 * interval_weeks` arithmetic.

Persisted task checkboxes for tasks 1–3 were updated to `[x]` in `openspec/changes/repetir-comidas-calendario/tasks.md`.

## Files changed

- `backend/migrations/versions/0007_meal_calendar_recurrence.sql`
- `backend/migrations/README.md`
- `backend/src/comemos_en_casa/meal_calendar/schemas.py`
- `backend/src/comemos_en_casa/meal_calendar/service.py`
- `backend/tests/meal_calendar/test_recurrence_migration.py`
- `backend/tests/meal_calendar/test_time_text.py`
- `openspec/changes/repetir-comidas-calendario/tasks.md`
- `openspec/changes/repetir-comidas-calendario/apply-progress.md`

## Verification evidence

- Safety net before modifying existing Python files: `15 passed` from `backend/tests/meal_calendar/test_time_text.py` and `backend/tests/meal_calendar/test_schema_migration.py`.
- RED: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_recurrence_migration.py backend/tests/meal_calendar/test_time_text.py` failed during collection because the new `occurrence_in_week` production symbol was absent; no production code had been added before this RED run.
- GREEN: focused recurrence and time-text tests passed with `17 passed`.
- GREEN plus migration/schema regression: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_schema_migration.py backend/tests/meal_calendar/test_recurrence_migration.py backend/tests/meal_calendar/test_time_text.py` passed with `22 passed`.
- The migration integration test exercised PostgreSQL checks, shared FK, coexistence, index presence, and absence of a generated-date table.
- Configured harness: `make test` ran backend and stopped after `107 passed, 1 failed`; the only failure was the pre-existing allowlist test `backend/tests/test_alembic_foundation.py::test_historical_sql_migrations_are_not_rewritten_as_alembic_revisions`, which still expects only versions `0001`–`0006`. That file is outside the explicitly allowed edit surfaces, so it was not changed.

## TDD Cycle Evidence

| Task | Test files | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1. RED contract | `test_recurrence_migration.py`, `test_time_text.py` | Unit plus PostgreSQL migration integration | 15 passed | Written and failed on absent production behavior | N/A | Added boundary, invalid-value, and migration constraint cases | N/A |
| 2. GREEN migration/domain | `test_recurrence_migration.py`, `test_time_text.py` | Unit plus PostgreSQL migration integration | 15 passed | Existing RED evidence | 17 focused tests passed | Added `RecurrenceRule`, recipe rejection, and all intervals 1–4 | Explicit constructor fields replaced `__dict__` expansion; 22 regression tests passed |
| 3. GREEN expansion | `test_time_text.py` | Pure unit | 15 passed | Written for absent `occurrence_in_week` | 17 focused tests passed | Covered inclusive boundaries, empty adjacent week, future anchor, month/year crossing, and intervals 1–4 | 22 migration/domain/time tests passed |

- Total tests added: 8 recurrence-focused tests, including one PostgreSQL integration test.
- Total focused tests passing at final focused run: 22.
- Pure functions created: `occurrence_in_week`.
- Approval tests: none; this slice adds behavior rather than refactoring existing behavior.

## Deviations from design

- No material deviations. `RecurrenceRule` exposes its persisted UUID as `id` and a `series_id` property for the later API layer; no API or repository wiring was added in this slice.
- The expansion function validates that the supplied range is exactly the inclusive Monday–Sunday week, preserving the existing `week_dates` contract.

## Historical remaining implementation tasks at end of slice 1

- [ ] Extender primero las pruebas de `backend/tests/meal_calendar/test_calendar_repository.py` y `backend/tests/meal_calendar/test_api_contract.py` para exigir listado de reglas candidatas compartidas, expansión combinada, orden por fecha/franja/texto/identidad, identidad estable `(seriesId, occurrenceDate)`, creación idempotente, conflicto `409`, conversión ordinaria atómica, `PATCH /series/{series_id}`, `DELETE /series/{series_id}?confirmed=true` y rechazos no mutantes. Incluir coexistencia de varias series/ordinarias en la misma celda, slot inmutable, `No repetir` destructivo confirmado y compatibilidad con receta heredada. Ejecutar ambos archivos y registrar los fallos esperados. <!-- sdd-owner: implementation -->
- [ ] Extender `backend/src/comemos_en_casa/meal_calendar/repository.py` con `find_rule_by_id`, inserción idempotente, actualización, borrado y listado de candidatas `calendar_key = "shared"`; modificar `list_week` para combinar asignaciones existentes (incluido `LEFT JOIN recipes`) con ocurrencias virtuales, derivar el identificador estable y aplicar un único orden determinista. Verificar con `backend/tests/meal_calendar/test_calendar_repository.py` y los tests de compatibilidad de `backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->
- [ ] Extender `backend/src/comemos_en_casa/meal_calendar/api.py` para aceptar `recurrenceWeeks: 0|1|2|3|4` con ausencia equivalente a `0`, devolver `entryType` discriminado y añadir `PATCH /series/{series_id}` y `DELETE /series/{series_id}?confirmed=true`; ejecutar creación/actualización/borrado y conversión de asignación libre dentro de transacciones, con UUID reutilizable, conflicto de idempotencia, `422` para receta/intervalo/fecha/franja/texto inválidos, confirmación obligatoria de reanclaje y borrado confirmado idempotente. No ofrecer rutas por `occurrenceDate`. Verificar con `pytest backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->
- [ ] Ejecutar y ajustar únicamente las pruebas backend necesarias en `backend/tests/meal_calendar/test_time_text.py`, `test_calendar_repository.py`, `test_api_contract.py` y `test_recurrence_migration.py` para triangular errores de límites de semana, retries, fallos simulados de inserción, reanclaje no confirmado, borrado repetido, coexistencia, calendario compartido y recetas históricas; verificar con `pytest` y después `make test-backend`. <!-- sdd-owner: implementation -->
- [ ] Ampliar `frontend/src/App.test.tsx` con pruebas fallidas para la unión `entryType`, frecuencias `0..4`, payload con UUID estable de creación, conversión mediante `assignmentId`, apertura de ocurrencia con `initialDate`, franja deshabilitada, confirmación de reanclaje, confirmación destructiva de `No repetir`, `deleteSeries` en vez de `deleteAssignment`, refetch posterior, coexistencia y receta heredada sin controles recurrentes. Añadir casos de reducer solo si la cobertura de la interfaz no permite observar el estado; ejecutar `cd frontend && npm test`. <!-- sdd-owner: implementation -->
- [ ] Implementar en `frontend/src/types.ts` `RecurrenceWeeks`, la unión `CalendarAssignment`/`RecurringCalendarOccurrence` y payloads de serie; en `frontend/src/api.ts` conservar contratos ordinarios y añadir `updateSeries`/`deleteSeries(seriesId, confirmed)`; en `frontend/src/calendarReducer.ts` modelar editor discriminado, `seriesId`, `occurrenceDate`, `initialDate`, intervalo, UUID retenido desde apertura y refresco posterior a mutación. Verificar con los tests RED y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->
- [ ] Modificar `frontend/src/App.tsx` y los estilos mínimos de `frontend/src/styles.css` para altas de texto libre con selector `No repetir`/`Cada semana`/`Cada 2–4 semanas`, conversión explícita de asignación, edición de serie sobre `initialDate`, slot visible deshabilitado, advertencia confirmada de reanclaje, borrado confirmado de serie y etiqueta accesible de frecuencia; mantener las tarjetas de receta heredadas legibles y sin controles de recurrencia. Verificar con `cd frontend && npm test` y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->
- [ ] Ejecutar la suite de `frontend/src/App.test.tsx` junto con `cd frontend && npm run build`, y ajustar casos deterministas para relectura de semana tras crear, convertir, editar o borrar, identidad estable en reintento, series en una misma celda, confirmaciones canceladas y presentación de recetas disponibles/no disponibles. No modificar el layout semanal fuera de los estilos estrictamente necesarios. <!-- sdd-owner: implementation -->
- [ ] Revisar los archivos modificados del backend y frontend para eliminar duplicación entre asignaciones y ocurrencias, mantener nombres `camelCase`/`PascalCase` y PEP 8, conservar consultas parametrizadas, mensajes de confirmación específicos y documentación de rollback; ejecutar `make test`, `cd frontend && npm run typecheck` y `cd frontend && npm run build`, y documentar la evidencia antes de solicitar revisión. <!-- sdd-owner: implementation -->

## Slice 2 — Task 4 RED progress

- [x] Task 4 RED: extended `backend/tests/meal_calendar/test_calendar_repository.py` and `backend/tests/meal_calendar/test_api_contract.py` with shared candidate filtering, combined virtual expansion, deterministic date/slot/text/identity ordering, stable occurrence identity, series-create idempotency/conflict, atomic ordinary-to-series conversion, series PATCH confirmation and immutable slot, confirmed DELETE idempotency, destructive `No repetir` semantics, non-mutating invalid requests, same-cell coexistence, and legacy recipe compatibility. The persisted checkbox in `tasks.md` is checked.
- No production code, migration, frontend file, or unrelated test was changed in this slice.
- Focused RED command: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_calendar_repository.py backend/tests/meal_calendar/test_api_contract.py` — expected RED: `10 failed, 5 passed, 2 warnings`. Failures are behavior gaps in the absent repository/API recurrence contracts and the newly required `entryType`, not syntax or collection errors.
- Files changed in this slice: `backend/tests/meal_calendar/test_calendar_repository.py`, `backend/tests/meal_calendar/test_api_contract.py`, `openspec/changes/repetir-comidas-calendario/tasks.md`, `openspec/changes/repetir-comidas-calendario/apply-progress.md`, and the pending `openspec/changes/repetir-comidas-calendario/verify-report.md` artifact.
- Delivery boundary: slice 2 start, stacked-to-main chain, Task 4 RED only. The workload gate was resolved by the parent prompt; no size exception approval was inferred for this slice.
- Authored boundary size: 412 insertions and 3 deletions in the commit, including the mandatory pending verification artifact. This is 12 authored lines above the 400-line review budget; the tests and required artifact are cohesive and were not compressed, so record a `size:exception` recommendation if the budget counts OpenSpec artifact bytes.

## TDD Cycle Evidence — Task 4 RED

| Task | Test files | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 4. RED repository/API contracts | `test_calendar_repository.py`, `test_api_contract.py` | Unit plus FastAPI contract | Existing focused suite before slice not rerun | 10 failed, 5 passed, 2 warnings; expected failures expose absent repository/API behavior | N/A by instruction; production code intentionally unchanged | N/A; this is the start of the chained backend slice | N/A |

## Current remaining implementation tasks

- [ ] Extender `backend/src/comemos_en_casa/meal_calendar/repository.py` con `find_rule_by_id`, inserción idempotente, actualización, borrado y listado de candidatas `calendar_key = "shared"`; modificar `list_week` para combinar asignaciones existentes (incluido `LEFT JOIN recipes`) con ocurrencias virtuales, derivar el identificador estable y aplicar un único orden determinista. Verificar con `backend/tests/meal_calendar/test_calendar_repository.py` y los tests de compatibilidad de `backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->
- [ ] Extender `backend/src/comemos_en_casa/meal_calendar/api.py` para aceptar `recurrenceWeeks: 0|1|2|3|4` con ausencia equivalente a `0`, devolver `entryType` discriminado y añadir `PATCH /series/{series_id}` y `DELETE /series/{series_id}?confirmed=true`; ejecutar creación/actualización/borrado y conversión de asignación libre dentro de transacciones, con UUID reutilizable, conflicto de idempotencia, `422` para receta/intervalo/fecha/franja/texto inválidos, confirmación obligatoria de reanclaje y borrado confirmado idempotente. No ofrecer rutas por `occurrenceDate`. Verificar con `pytest backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->
- [ ] Ejecutar y ajustar únicamente las pruebas backend necesarias en `backend/tests/meal_calendar/test_time_text.py`, `test_calendar_repository.py`, `test_api_contract.py` y `test_recurrence_migration.py` para triangular errores de límites de semana, retries, fallos simulados de inserción, reanclaje no confirmado, borrado repetido, coexistencia, calendario compartido y recetas históricas; verificar con `pytest` y después `make test-backend`. <!-- sdd-owner: implementation -->
- [ ] Ampliar `frontend/src/App.test.tsx` con pruebas fallidas para la unión `entryType`, frecuencias `0..4`, payload con UUID estable de creación, conversión mediante `assignmentId`, apertura de ocurrencia con `initialDate`, franja deshabilitada, confirmación de reanclaje, confirmación destructiva de `No repetir`, `deleteSeries` en vez de `deleteAssignment`, refetch posterior, coexistencia y receta heredada sin controles recurrentes. Añadir casos de reducer solo si la cobertura de la interfaz no permite observar el estado; ejecutar `cd frontend && npm test`. <!-- sdd-owner: implementation -->
- [ ] Implementar en `frontend/src/types.ts` `RecurrenceWeeks`, la unión `CalendarAssignment`/`RecurringCalendarOccurrence` y payloads de serie; en `frontend/src/api.ts` conservar contratos ordinarios y añadir `updateSeries`/`deleteSeries(seriesId, confirmed)`; en `frontend/src/calendarReducer.ts` modelar editor discriminado, `seriesId`, `occurrenceDate`, `initialDate`, intervalo, UUID retenido desde apertura y refresco posterior a mutación. Verificar con los tests RED y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->
- [ ] Modificar `frontend/src/App.tsx` y los estilos mínimos de `frontend/src/styles.css` para altas de texto libre con selector `No repetir`/`Cada semana`/`Cada 2–4 semanas`, conversión explícita de asignación, edición de serie sobre `initialDate`, slot visible deshabilitado, advertencia confirmada de reanclaje, borrado confirmado de serie y etiqueta accesible de frecuencia; mantener las tarjetas de receta heredadas legibles y sin controles de recurrencia. Verificar con `cd frontend && npm test` y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->
- [ ] Ejecutar la suite de `frontend/src/App.test.tsx` junto con `cd frontend && npm run build`, y ajustar casos deterministas para relectura de semana tras crear, convertir, editar o borrar, identidad estable en reintento, series en una misma celda, confirmaciones canceladas y presentación de recetas disponibles/no disponibles. No modificar el layout semanal fuera de los estilos estrictamente necesarios. <!-- sdd-owner: implementation -->
- [ ] Revisar los archivos modificados del backend y frontend para eliminar duplicación entre asignaciones y ocurrencias, mantener nombres `camelCase`/`PascalCase` y PEP 8, conservar consultas parametrizadas, mensajes de confirmación específicos y documentación de rollback; ejecutar `make test`, `cd frontend && npm run typecheck` y `cd frontend && npm run build`, y documentar la evidencia antes de solicitar revisión. <!-- sdd-owner: implementation -->

## Work-unit commit and budget

- Work-unit commit: final Conventional Commit hash is reported in the phase envelope.
- Authored changed lines: 472, including the mandatory cumulative apply-progress record. The slice is cohesive and was not compressed by deleting tests, documentation, comments, or blank lines; recommend recording a `size:exception` for this slice if the 400-line review budget applies to planning artifacts as well as source changes.

## Next step

Return `sdd-verify` for parent review of this bounded slice. The next apply slice should begin with repository/API RED work; do not implement it in this commit.

## Approved correction: migration foundation allowlist

- Scope: corrected only `backend/tests/test_alembic_foundation.py` so the historical SQL migration allowlist includes intentional `0007_meal_calendar_recurrence.sql`; the test still asserts that the SQL migrations are not rewritten as Alembic revisions.
- No application code, migration SQL, unrelated tests, or task checkboxes were changed.
- TDD evidence: RED focused foundation run failed with `1 failed, 2 passed` because 0007 was absent from the expectation; GREEN rerun passed with `3 passed`; TRIANGULATE `make test` passed with `108 passed, 2 warnings`, frontend typecheck passed, and frontend build passed.
- Files changed in this correction: `backend/tests/test_alembic_foundation.py`, `openspec/changes/repetir-comidas-calendario/apply-progress.md`.
- Structured status consumed: native `ready`, recommended action `apply`, OpenSpec artifact store, repo-local action context with workspace-root edit authority; no action-context warning or blocker.
- Delivery boundary: small correction to the already-approved slice, kept within the user-provided allowlist; no new implementation task was completed, so persisted implementation task checkboxes remain unchanged.
- The exact unchecked implementation task lines above remain the remaining work; the next implementation slice is still repository/API RED work.
