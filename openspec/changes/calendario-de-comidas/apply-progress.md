# Apply progress: calendario-de-comidas

## PR boundary and status

- **Work unit:** PR 1 — foundation, temporal rules, and PostgreSQL schema only.
- **Delivery path:** feature-branch chain slice on `feature/calendario-de-comidas-pr1-foundation-schema`; no PR 2 API work was started and no commit was created.
- **Structured status consumed:** `applyState=ready`, artifact store `openspec`, strict TDD enabled, workspace `/opt/apps/comemos-en-casa`, allowed root `/opt/apps/comemos-en-casa`, and no action-context warnings.
- **Current status:** PR 1 is complete: the five implementation-owned PR 1 checkboxes are persisted as checked in `tasks.md`.

## Prior blocked attempt merged

The earlier attempt wrote the PR 1 domain, migration, and focused tests but could not execute `pytest` (exit 127). This resumption did not duplicate those artifacts. It first executed the configured virtual-environment runner, added one missing assignment-shape regression, and added an isolated PostgreSQL execution test so the previously blocked evidence is now executable.

## Baseline and verification evidence

| Stage | Exact command | Observed result |
|---|---|---|
| Baseline before this resumption's edits | `.venv/bin/pytest -q` | `14 passed in 0.02s` (exit 0) |
| RED | `.venv/bin/pytest -q backend/tests/meal_calendar/test_time_text.py::test_assignment_draft_rejects_a_recipe_value_that_is_not_a_uuid` | `1 failed in 0.03s` (exit 1): `AssignmentDraft.create()` accepted a string instead of a UUID. |
| GREEN | `.venv/bin/pytest -q backend/tests/meal_calendar/test_time_text.py` | `10 passed in 0.03s` (exit 0). |
| Final explicit time-zone regression | `.venv/bin/pytest -q backend/tests/meal_calendar/test_time_text.py` | `10 passed in 0.02s` (exit 0), with Canary tests passing `timezone=CANARY_TIMEZONE` explicitly. |
| TRIANGULATE, first execution | `.venv/bin/pytest -q backend/tests/meal_calendar/test_schema_migration.py` | `4 passed, 1 failed in 0.23s` (exit 1): the new PostgreSQL oracle incorrectly counted the required `calendar_key` foreign key as a recipe foreign key. |
| TRIANGULATE, corrected oracle | `.venv/bin/pytest -q backend/tests/meal_calendar/test_schema_migration.py` | `5 passed in 0.18s` (exit 0). |
| Foundation regression | `.venv/bin/pytest -q backend/tests/meal_calendar` | `15 passed in 0.20s` (exit 0). |
| REFACTOR/full configured suite | `.venv/bin/pytest -q` | `16 passed in 0.16s` (exit 0). |
| Diff whitespace check | `git diff --check` | Exit 0; no output. |

## PostgreSQL migration evidence

The healthy `postgres` Compose service was used by the integration test, which runs the exact contents of `backend/migrations/versions/0001_meal_calendar_foundation.sql` through `docker compose exec -T postgres psql --set ON_ERROR_STOP=1 -U comemos -d comemos_en_casa` in a transaction-local schema and rolls it back.

A separate foreground migration check used:

```sh
docker compose exec -T postgres psql --set ON_ERROR_STOP=1 -U comemos -d comemos_en_casa <<'SQL'
# BEGIN; CREATE SCHEMA meal_calendar_manual_check; SET LOCAL search_path;
# exact 0001 foundation DDL; two same-cell free-text INSERTs; contract SELECTs; ROLLBACK;
SQL
```

Observed result: all three tables and all three secondary indexes were created; two same-date/same-slot free-text rows inserted successfully; `duplicate_cell_rows` was `2`; `deferred_recipe_fks` was `0`; and `ROLLBACK` removed the validation schema. The test also exercises rejected non-`shared` singleton keys and a free-text row that improperly supplies `recipe_id`.

`recipes(id)` still has no concrete migration target in this repository. Therefore `0001` intentionally keeps `recipe_id` nullable, has no invented recipes FK, and the migration README retains the required future `REFERENCES recipes(id) ON DELETE SET NULL` direction. A real `ON DELETE SET NULL` preservation test is deferred with that catalogue-owned migration; the current test verifies the deferred tombstone-FK contract rather than claiming an unavailable FK was applied.

## TDD Cycle Evidence

| Work unit | Test files | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| PR 1 foundation/schema | `backend/tests/meal_calendar/test_time_text.py` | Unit | `.venv/bin/pytest -q`: 14 passed | Added and ran `test_assignment_draft_rejects_a_recipe_value_that_is_not_a_uuid`; it failed because a string recipe ID was accepted. | Added the minimum UUID runtime guard; the focused temporal/text suite passed 10 tests. | Existing cases cover Canary midnight, year boundary, DST, Monday-only starts, NFC/trim/text-only HTML sanitization, 1–100 code points, and invalid slot/kind/value combinations. | Reconfirmed constants and validation helpers remain consolidated in the domain boundary; no behavior-changing refactor was needed; full suite passed. |
| PR 1 foundation/schema | `backend/tests/meal_calendar/test_schema_migration.py` | PostgreSQL integration plus SQL-contract unit | `.venv/bin/pytest -q`: 14 passed | The earlier blocked-at-runner schema tests were retained rather than duplicated; this resumption added the executable PostgreSQL migration contract. | The existing expand-only migration applied unchanged in an isolated transaction. | Added executable singleton and invalid-shape checks, duplicate-cell inserts, index/rate-bucket checks, and a recipe-FK-specific catalogue query; `5 passed`. | Kept the migration contract unchanged; repeated the focused foundation and full suites successfully. |

## Completed persisted tasks

- [x] Baseline — configured-runner baseline executed and passed.
- [x] RED — focused temporal/text/schema tests now have executable RED evidence.
- [x] GREEN — the pure foundation boundary and expand-only migration are validated.
- [x] TRIANGULATE — boundary, invalid-shape, duplicate-cell, index/rate-bucket, and deferred-FK contracts are exercised.
- [x] REFACTOR — consolidated domain boundary was retained and regression-tested.

## Files changed or validated

### Existing PR 1 files validated

- `backend/src/comemos_en_casa/meal_calendar/settings.py`
- `backend/src/comemos_en_casa/meal_calendar/service.py`
- `backend/src/comemos_en_casa/meal_calendar/schemas.py`
- `backend/migrations/versions/0001_meal_calendar_foundation.sql`
- `backend/migrations/README.md`
- `backend/tests/meal_calendar/test_time_text.py`
- `backend/tests/meal_calendar/test_schema_migration.py`

### Changes made during this resumption

- `backend/src/comemos_en_casa/meal_calendar/schemas.py`: reject a recipe assignment whose `recipe_id` is not a `UUID`.
- `backend/tests/meal_calendar/test_time_text.py`: add the executable invalid-UUID assignment-shape RED regression.
- `backend/tests/meal_calendar/test_schema_migration.py`: execute the exact migration through the healthy Compose PostgreSQL service inside a rolled-back isolated schema, including singleton, invalid-shape, duplicate-cell, index, rate-bucket, and deferred-FK checks.
- `openspec/changes/calendario-de-comidas/tasks.md`: checked only the five completed PR 1 rows.
- `openspec/changes/calendario-de-comidas/apply-progress.md`: merged this execution evidence.

## Limitations and deviations

- The product-facing `Europe/Canary` setting resolves through the existing `Atlantic/Canary` fallback only if the platform's IANA data does not provide `Europe/Canary`; temporal tests explicitly inject `CANARY_TIMEZONE` for Canary midnight, year-boundary, and DST behavior.
- The recipe catalogue and its `recipes(id)` migration remain absent. No fake recipe table, foreign key, destructive rollback, API route, repository, catalogue adapter, frontend, login, privacy model, or CAPTCHA was introduced.
- The manually applied migration was deliberately rolled back. It is validation evidence, not a persistent environment deployment.
- Pre-existing worktree changes outside the allowed edit surfaces (`.gitignore`, `pyproject.toml`, `requirements-dev.txt`, and untracked `docker-compose.yml`) were not modified during this resumption.

## Workload / PR boundary

This is the assigned `feature-branch-chain` PR 1 slice only. The resumption changed 103 backend lines relative to branch head (97 additions and 6 deletions across the UUID guard and focused tests), plus OpenSpec task/progress bookkeeping; it did not begin PR 2. The underlying PR 1 foundation commit already contains the broader foundation/schema work and remains the intended PR boundary.

## Remaining unchecked implementation tasks

- [ ] RED — add failing API and PostgreSQL integration tests in `backend/tests/meal_calendar/test_api_contract.py` and `test_repository.py` covering `/context`, Monday-validated weekly reads, normalized public recipe search/cursors, recipe detail, ordered mixed assignments, and the documented POST/PATCH/DELETE status/error payloads. <!-- sdd-owner: implementation -->
- [ ] GREEN — implement `backend/src/comemos_en_casa/meal_calendar/{repository.py,api.py,catalog_adapter.py}` and the application route registration discovery target so `/api/v1/meal-calendar` serves the specified JSON UTF-8, `Cache-Control: no-store` resources using PostgreSQL as the source of truth. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — extend those tests for duplicate UUID-backed creates, repeat-create same-payload `200`, differing-payload `409 idempotency_conflict`, idempotent repeated delete, `404` after delete, current recipe-title joins, and the unavailable-recipe payload with no copied title/image snapshot. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — isolate HTTP translation from service and SQL concerns at the listed backend boundaries, retain stable error envelopes and ordering tie-breaks, and run `pytest` for API/repository plus all earlier tests. <!-- sdd-owner: implementation -->
- [ ] RED — add failing tests in `backend/tests/meal_calendar/test_resilience_access.py` for startup-only `ENABLE_GUEST_USER` parsing, absent/false guest access requiring issue #6, exact guest context/banner flag, three 250/500/1000 ms retries after the first attempt, `503` failure mapping, trusted-proxy IP handling, and 60-read/30-write minute limits. <!-- sdd-owner: implementation -->
- [ ] GREEN — implement `backend/src/comemos_en_casa/meal_calendar/{rate_limit.py,settings.py,repository.py,api.py}` so access and atomic PostgreSQL buckets execute once per request before every feature route, guest mode uses only `calendar_key='shared'`, transient repository failures retry in fresh transactions, and API errors expose exact `429`/`503` messages, `Retry-After`, and limit headers. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — add failure-injection and concurrent-connection cases proving four total database attempts, internal retries do not consume extra quota, manual retry is a new request, limit increments cannot exceed either threshold, concurrent distinct UUID creates coexist, last confirmed PATCH wins, and a late PATCH cannot resurrect a deleted assignment. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — centralize retryable-driver classification, operation descriptors, access/rate middleware hooks, and error mapping without weakening fail-closed limiting or the issue #6 boundary; run `pytest` across all backend tests. <!-- sdd-owner: implementation -->
- [ ] RED — add focused frontend tests beside `frontend/src/features/meal-calendar/` for bootstrapping `/context`, Canary `Hoy`, tokenized week navigation with stale data/skeleton/inert editing, global and cell-preselected add flows, and mixed alphabetical cards; retain the frontend test command/output selected by the application scaffold. <!-- sdd-owner: implementation -->
- [ ] GREEN — implement `frontend/src/features/meal-calendar/{api-client.*,store.*,MealCalendar.*,WeekGrid.*,AssignmentEditor.*,RecipePicker.*}` and its route/shell discovery target to consume the stable API contract, show the guest banner before initial week loading, and render the Monday–Sunday Comida/Cena grid with recipe and free-text creation/edit/delete paths. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — add state tests for blur plus explicit `Guardar` including the focused field, disabled clean save, one in-flight request per revision, a changed-during-save follow-up, per-operation `Guardando`/two-second `Guardado`, queued navigation during saving, unsaved-change confirmation, and isolated stale-response handling. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — keep ephemeral drafts, request tokens, timers, modal/search/scroll state, and failed-operation descriptors in the feature store rather than the backend or a local calendar cache; rerun the focused frontend suite and `pytest`. <!-- sdd-owner: implementation -->
- [ ] RED — add frontend/component and API contract tests for a retained failed draft or stale week under a loading overlay, exact database and rate-limit toasts with isolated `Reintentar`, cancellation of a pending manual retry on navigation, unavailable-recipe cards, modal context restoration, keyboard/touch tooltip behavior, and required accessible names/live feedback/focus return. <!-- sdd-owner: implementation -->
- [ ] GREEN — complete `frontend/src/features/meal-calendar/{Feedback.*,RecipeDetailModal.*,FreeTextTooltip.*,MealCalendar.*}` and styles so failed operations preserve only their own form, the modal is read-only, free text renders through text primitives, the weekly grid scrolls horizontally on mobile with sticky headers/slot column and vertically overflowing cells, and all specified banner, toast, focus, and live-region behavior is present. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — exercise desktop and mobile-touch viewports, dense cells, loading and read-failure states, `Escape`/focus restoration, tooltip hover/focus/tap, `aria-busy`/inert stale content, and guest-on versus guest-off behavior; add or update contract tests for exact response bodies, headers, and no out-of-scope controls. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — remove duplicated feedback, breakpoint, and accessibility helpers while preserving logical DOM order and 44×44 CSS-px touch targets; rerun the frontend suite and `pytest`. <!-- sdd-owner: implementation -->
- [ ] GREEN — create `docs/calendario-de-comidas/uso.md`, `docs/calendario-de-comidas/interfaz.md`, and `docs/interfaces/calendario-de-comidas.openapi.yaml` with the approved routes, schemas, error/limit headers, exact banner/toast strings, guest risk/disable-and-restart guidance, state/UI/accessibility/responsive behavior, and explicit exclusions. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — validate the OpenAPI file against the implemented API contract and inspect the two documents against all five specifications, including #6 dependency wording and the approved shared-guest risk, correcting documentation drift rather than reintroducing stale test-setup claims. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — make terminology, endpoint examples, and Spanish feedback consistent across the three documentation targets without expanding product scope; rerun the documentation/contract validation and `pytest`. <!-- sdd-owner: implementation -->
- [ ] Final verification — run the full `pytest` suite, applicable frontend suite, migration test against isolated PostgreSQL, API/OpenAPI contract checks, and manual keyboard plus mobile/desktop responsive acceptance; record RED/GREEN/TRIANGULATE/REFACTOR evidence by work unit and confirm no login implementation, privacy model, CAPTCHA, destructive migration rollback, or commits were introduced. <!-- sdd-owner: implementation -->

## Formal strict-TDD evidence reconciliation — PR1

This section records the user's request for evidence-only reconciliation and re-verification of PR1 on `feature/calendario-de-comidas-pr1-foundation-schema`. No source, test, task checkbox, configuration, or migration was changed, and no commit was created.

### Historical-evidence determination

- The historical RED for the original temporal/text/schema tests cannot be proven from the retained repository artifacts or reachable/reflog history.
- The search found the original PR1 test paths first introduced together with their implementation in commit `3552bb22a67d41392c6d67737973accda6401208`; no pre-implementation test output was retained, and no historical artifact contained a failure-output marker for those original behaviors.
- The UUID regression remains the only authentic RED: `.venv/bin/pytest -q backend/tests/meal_calendar/test_time_text.py::test_assignment_draft_rejects_a_recipe_value_that_is_not_a_uuid` recorded `1 failed in 0.03s` because a string recipe identifier was accepted.
- The schema oracle failure is excluded as RED evidence because its PostgreSQL query incorrectly counted the required `calendar_key` foreign key as a recipe foreign key after the production migration already existed; it is an oracle defect, not missing behavioral implementation.
- Current green results remain valid, but they do not establish the missing historical RED sequence.
- Strict-TDD admission remains blocked pending an explicit governance disposition; this reconciliation does not resolve or relabel that blocker.

### Requested re-verification

| Exact command | Observed result |
|---|---|
| `.venv/bin/pytest -q` | Exit 0; `16 passed in 0.21s`. |
| `git diff --check` | Exit 0; no output. |

## Maintainer governance disposition — PR1 historical RED evidence exception

The maintainer explicitly accepts a documented **PR1-only exception** for the irrecoverable historical RED-evidence gap identified in the formal reconciliation and verification report.

- This exception does **not** represent the missing original temporal/text/schema RED execution as authentic RED evidence; the evidence remains absent and is recorded honestly as such.
- Current GREEN and PostgreSQL migration evidence remains valid for the exact current worktree, including the passing foundation behavior and executable migration checks.
- `strict_tdd: true` remains in force for all subsequent work. Every future PR must retain authentic RED evidence before production implementation, followed by GREEN, TRIANGULATE, and REFACTOR evidence.
- This is a governance disposition only: it is not a `size:exception`, does not alter task checkboxes, and does not authorize starting PR2 before PR1 verification is rerun.
- No source, test, configuration, migration, or task artifact was changed for this disposition, and no commit was created.

### Disposition verification

| Exact command | Observed result |
|---|---|
| `.venv/bin/pytest -q` | Exit 0; `16 passed in 0.19s`. |
| `git diff --check` | Exit 0; no output. |
