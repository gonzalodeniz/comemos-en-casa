```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:32523b2f8cb68d654eda17e4df095ee77bf746be16a09071618bb4470c9b490c
verdict: fail
blockers: 7
critical_findings: 7
requirements: 0/13
scenarios: 0/29
test_command: "PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_api_contract.py"
test_exit_code: 1
test_output_hash: sha256:ef7822e8fc347fd7b2572050872159f79e607220c328d6ca9966b1ff976c9ea1
build_command: "not run: repository-only Task 5 verification; no build requested"
build_exit_code: 125
build_output_hash: sha256:efb2797f9ab64305ed9e38ee2449b49dca40ec2c0f1ff3862b9f3844ca63fc53
```

# Verification: repetir-comidas-calendario — Task 5 repository GREEN

## Verdict

**FAIL for whole-change completeness; PASS for the assigned Task 5 repository slice.** The repository implementation meets its bounded persistence and combined-read contract. The API subset is still RED solely for the explicitly unimplemented Task 6 HTTP contract. Seven implementation tasks remain unchecked, so the change is not ready for archive.

The authoritative native status is `ready`, with `nextRecommended: apply`; optional verification does not alter that recommendation. The structured action context is `repo-local`, workspace `/opt/apps/comemos-en-casa`, with that workspace as the allowed edit root.

## Scope, ownership, and commit evidence

- Inspected finalized proposal, specification, design, tasks, current apply progress, existing verify report, Task 5 commit, repository implementation, and the four recurrence-related test files.
- Task 5 commit is `d6c9fb31c95baebaf4eef0768648dc41c3924ae8` (`feat(meal-calendar): persist recurrence rules and combine weekly reads`), directly after Task 4 RED commit `abd4489`.
- `git diff --check abd4489..d6c9fb3` passed. The committed Task 5 diff contains only `backend/src/comemos_en_casa/meal_calendar/repository.py`, `tasks.md`, and `apply-progress.md` (166 insertions, 12 deletions).
- No API, frontend, migration, or test files appear in the Task 5 commit, so no API/frontend scope drift occurred.
- `git log d6c9fb3..HEAD` was empty before this artifact update; this verification created no repository commit. The only pre-existing worktree modification was the canonical `verify-report.md`.

## Task 5 acceptance evidence

- Shared recurrence lookup, candidate listing, insert, update, and delete all use `CALENDAR_KEY = "shared"`; candidate listing additionally limits rows to `initial_date <= week_end`.
- `list_week` reads ordinary assignments through the preserved `LEFT JOIN recipes`, expands eligible recurrence rules with `occurrence_in_week`, and combines entries only in memory.
- Virtual occurrence IDs are deterministically derived as `series:{series_id}:{occurrence_date}`. No Task 5 query writes generated dates to `meal_assignments`; rule writes target only `meal_recurrence_rules`.
- Combined ordering is date ascending, lunch before dinner, normalized visible text, then stable ID. The repository tests cover ordinary/recipe coexistence, two same-text series, repeated reads, and unavailable legacy recipes.
- The API deliberately has not yet added response discrimination or series routes. Therefore this verification confirms repository metadata (`entry_type`, `series_id`, `occurrence_date`, `initial_date`, `recurrence_weeks`) but does not claim that the public API exposes it until Task 6.

## Commands and results

| Scope | Exact command | Result |
|---|---|---|
| Focused repository | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_calendar_repository.py` | PASS — `5 passed in 0.09s` |
| Recurrence/domain regression | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_recurrence_migration.py backend/tests/meal_calendar/test_time_text.py` | PASS — `17 passed in 0.36s` |
| API contract subset | `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend/src .venv/bin/pytest -q backend/tests/meal_calendar/test_api_contract.py` | Expected Task 6 RED — exit `1`; `3 passed, 7 failed, 2 warnings in 1.24s` |

No build or full suite was run: the user requested focused Task 5 verification, and build/frontend work belongs to later unchecked tasks. The envelope test-output digest is from the final API-subset execution. No source or test files were edited.

### Expected Task 6 RED failures

The seven API-subset failures are all missing Task 6 behavior, not Task 5 repository failures:

1. Week responses do not yet emit `entryType: "assignment"`.
2. Recurring create rejects `recurrenceWeeks` before series persistence/idempotency can run.
3. Ordinary-to-series conversion rejects `recurrenceWeeks` before an atomic transition can run.
4. `PATCH /series/{series_id}` is absent, returning `404` instead of its confirmation/validation contract.
5. `DELETE /series/{series_id}` is absent, returning `404` instead of confirmation and idempotent deletion behavior.
6. The `No repetir` series PATCH validation path is absent with that same missing route.
7. Legacy recipe/free-text read responses lack the new `entryType` discriminator.

The migration regression passes and verifies two coexisting shared rules, SQL checks and index presence, plus zero `meal_recurrence_occurrences` tables. This corroborates the virtual-occurrence-only persistence model.

## Spec coverage

The finalized specification contains **13 requirements and 29 scenarios**. At whole-change level, **0/13 requirements and 0/29 scenarios are complete**, because Task 6 API wiring and all subsequent backend/frontend work are intentionally outstanding. Task 5 provides bounded evidence toward shared persistence, virtual weekly expansion, coexistence, deterministic ordering, legacy recipe readability, and shared-calendar filtering; it cannot independently complete API-facing requirements.

## Strict TDD compliance

Strict TDD is active in `openspec/config.yaml`. The project-local override is absent; the global strict-TDD verification guidance was applied.

| Check | Result | Details |
|---|---|---|
| TDD Cycle Evidence reported | PASS | `apply-progress.md` contains Task 1–5 evidence tables, including Task 5 RED, GREEN, TRIANGULATE, and REFACTOR columns. |
| Reported test files exist | PASS | `test_time_text.py`, `test_recurrence_migration.py`, `test_calendar_repository.py`, and `test_api_contract.py` all exist. |
| Task 5 GREEN remains true | PASS | The focused repository run is `5 passed`. |
| Recurrence/domain regressions remain green | PASS | Migration and time/domain run is `17 passed`. |
| Task 4/6 API RED distinguished | PASS | The API subset has 3 passing legacy checks and 7 failures attributable to the documented, unchecked Task 6 scope. |
| Assertion quality | PASS | No tautologies, ghost loops, type-only-only assertions, smoke-only assertions, CSS implementation-detail assertions, or assertions lacking production execution were found in the four related test files. |

### Test layer distribution

| Layer | Tests | Files | Tool |
|---|---:|---:|---|
| Unit/repository-domain | 19 | 2 | pytest |
| PostgreSQL migration integration | 3 | 1 | pytest plus Docker Compose/psql |
| FastAPI contract integration | 10 | 1 | pytest plus FastAPI TestClient |
| E2E | 0 | 0 | not configured |
| Total | 32 | 4 | |

Coverage analysis was skipped because no coverage command is configured. No lint command is configured; frontend type checking is not applicable to the Task 5 Python-only committed scope.

## Review workload and PR boundary

`tasks.md` forecasts a high-risk 900–1,300 line whole change and recommends chained review. The current committed boundary is limited to Task 5 repository code plus required OpenSpec progress/task evidence, at 178 changed lines, and fits the requested stacked slice. No `size:exception` is needed for this commit. The cumulative progress labels it "Slice 3" because the earlier Task 4 RED and migration-allowlist correction were recorded separately; the user-requested Task 5 boundary itself remains repository-only.

## Task completion and archive blockers

Tasks 1–5 are checked. The following exact unchecked implementation markers remain. Each is a critical completeness issue and archive blocker; this partial slice is not ready for archive.

- [ ] Extender `backend/src/comemos_en_casa/meal_calendar/api.py` para aceptar `recurrenceWeeks: 0|1|2|3|4` con ausencia equivalente a `0`, devolver `entryType` discriminado y añadir `PATCH /series/{series_id}` y `DELETE /series/{series_id}?confirmed=true`; ejecutar creación/actualización/borrado y conversión de asignación libre dentro de transacciones, con UUID reutilizable, conflicto de idempotencia, `422` para receta/intervalo/fecha/franja/texto inválidos, confirmación obligatoria de reanclaje y borrado confirmado idempotente. No ofrecer rutas por `occurrenceDate`. Verificar con `pytest backend/tests/meal_calendar/test_api_contract.py`. <!-- sdd-owner: implementation -->
- [ ] Ejecutar y ajustar únicamente las pruebas backend necesarias en `backend/tests/meal_calendar/test_time_text.py`, `test_calendar_repository.py`, `test_api_contract.py` y `test_recurrence_migration.py` para triangular errores de límites de semana, retries, fallos simulados de inserción, reanclaje no confirmado, borrado repetido, coexistencia, calendario compartido y recetas históricas; verificar con `pytest` y después `make test-backend`. <!-- sdd-owner: implementation -->
- [ ] Ampliar `frontend/src/App.test.tsx` con pruebas fallidas para la unión `entryType`, frecuencias `0..4`, payload con UUID estable de creación, conversión mediante `assignmentId`, apertura de ocurrencia con `initialDate`, franja deshabilitada, confirmación de reanclaje, confirmación destructiva de `No repetir`, `deleteSeries` en vez de `deleteAssignment`, refetch posterior, coexistencia y receta heredada sin controles recurrentes. Añadir casos de reducer solo si la cobertura de la interfaz no permite observar el estado; ejecutar `cd frontend && npm test`. <!-- sdd-owner: implementation -->
- [ ] Implementar en `frontend/src/types.ts` `RecurrenceWeeks`, la unión `CalendarAssignment`/`RecurringCalendarOccurrence` y payloads de serie; en `frontend/src/api.ts` conservar contratos ordinarios y añadir `updateSeries`/`deleteSeries(seriesId, confirmed)`; en `frontend/src/calendarReducer.ts` modelar editor discriminado, `seriesId`, `occurrenceDate`, `initialDate`, intervalo, UUID retenido desde apertura y refresco posterior a mutación. Verificar con los tests RED y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->
- [ ] Modificar `frontend/src/App.tsx` y los estilos mínimos de `frontend/src/styles.css` para altas de texto libre con selector `No repetir`/`Cada semana`/`Cada 2–4 semanas`, conversión explícita de asignación, edición de serie sobre `initialDate`, slot visible deshabilitado, advertencia confirmada de reanclaje, borrado confirmado de serie y etiqueta accesible de frecuencia; mantener las tarjetas de receta heredadas legibles y sin controles recurrentes. Verificar con `cd frontend && npm test` y `cd frontend && npm run typecheck`. <!-- sdd-owner: implementation -->
- [ ] Ejecutar la suite de `frontend/src/App.test.tsx` junto con `cd frontend && npm run build`, y ajustar casos deterministas para relectura de semana tras crear, convertir, editar o borrar, identidad estable en reintento, series en una misma celda, confirmaciones canceladas y presentación de recetas disponibles/no disponibles. No modificar el layout semanal fuera de los estilos estrictamente necesarios. <!-- sdd-owner: implementation -->
- [ ] Revisar los archivos modificados del backend y frontend para eliminar duplicación entre asignaciones y ocurrencias, mantener nombres `camelCase`/`PascalCase` y PEP 8, conservar consultas parametrizadas, mensajes de confirmación específicos y documentación de rollback; ejecutar `make test`, `cd frontend && npm run typecheck` y `cd frontend && npm run build`, y documentar la evidencia antes de solicitar revisión. <!-- sdd-owner: implementation -->

## Blockers

1. Task 6 API recurrence create/convert/series-route implementation is unchecked and its contract tests remain intentionally RED.
2. Backend triangulation is unchecked.
3. Frontend RED, types/client/reducer, editor, frontend triangulation, and refactor tasks are unchecked.
