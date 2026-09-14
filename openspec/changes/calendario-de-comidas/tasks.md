# Tasks: calendario de comidas

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 2,800–3,800 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 foundation/schema → PR 2 calendar API → PR 3 resilience/access → PR 4 frontend state/UI → PR 5 accessibility/docs/acceptance |
| Delivery strategy | ask-on-risk (preconfigured; no delivery decision is made here) |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

## Planning constraints

- Preserve the external dependency **issue #6**: with guest disabled, return the integration’s `401 authentication_required`; do not add a login UI or an authentication replacement.
- Preserve the approved guest risk: `ENABLE_GUEST_USER=true` deliberately exposes one shared calendar to anonymous and authenticated visitors; do not introduce ownership, isolation, recovery, CAPTCHA, or hidden permission controls.
- Before applying the calendar migration, confirm the discovery target that owns `recipes(id)` and its migration history. The `ON DELETE SET NULL` foreign key cannot be applied before that table exists.
- `proposal.md` and `design.md` still say pytest/strict-TDD or test tooling must be configured. This is documentation drift: `openspec/config.yaml` already configures `strict_tdd: true` and `pytest`; do not duplicate configuration/setup work or claim the stale wording remains true.
- No commits are part of this phase or this task plan’s delivery decision.

## Strict TDD evidence rule

For every work unit, retain the exact test names and command output: **RED** proves the new focused tests fail for the intended missing behavior; **GREEN** proves the smallest implementation passes; **TRIANGULATE** adds boundary, failure, or concurrency examples and passes; **REFACTOR** improves structure with the full relevant suite still passing. Use `pytest` for all backend and PostgreSQL evidence; use the frontend runner introduced with the frontend application only for frontend evidence, without changing `openspec/config.yaml`.

## Work-unit boundaries

| Work unit / PR | Start boundary | Finish boundary | Verification | Rollback boundary |
|---|---|---|---|---|
| PR 1 — foundation and schema | Existing pytest smoke test | Python domain boundary plus an expand-only PostgreSQL migration | Unit and ephemeral-PostgreSQL migration tests | Leave schema/data in place; do not run destructive downgrade |
| PR 2 — calendar API | PR 1 schema and recipe-table prerequisite available | Read/search/assignment HTTP contract and repository behavior | API contract and PostgreSQL integration tests | Remove API routing while retaining compatible schema |
| PR 3 — resilience and access | PR 2 endpoints callable | Guest gate, rate limits, retries, and error mapping | Failure-injection, access, and atomic-limit tests | Set guest false and restart; retain plans and schema |
| PR 4 — frontend calendar | PR 2 contract stable, PR 3 context/error contract stable | Week store, assignment flows, and responsive grid | Focused frontend state/component tests | Remove feature route/client without changing persisted plans |
| PR 5 — accessible delivery | PR 4 interactions present | Accessibility/responsive behavior, OpenAPI, user docs, acceptance coverage | Contract, manual viewport/assistive-tech, and full suite | Withdraw UI/docs together; do not delete calendar data |

## PR 1 — foundation, temporal rules, and PostgreSQL schema

- [x] Baseline — run `pytest` from the repository root before feature changes and retain the passing smoke-test output as the configured-runner baseline; do not alter pytest or OpenSpec setup. <!-- sdd-owner: implementation -->
- [x] RED — add focused failing pytest cases under `backend/tests/meal_calendar/test_time_text.py` and `backend/tests/meal_calendar/test_schema_migration.py` for injected `Europe/Canary` week calculation (midnight, year boundary, DST), Monday-only week starts, NFC/trim/sanitize/1–100-code-point free text, and the required singleton/schema checks. <!-- sdd-owner: implementation -->
- [x] GREEN — create the Python meal-calendar boundary at `backend/src/comemos_en_casa/meal_calendar/{schemas.py,service.py,settings.py}` and the versioned migration under the repository’s chosen migration directory to implement DATE/slot/kind validation, singleton `shared` calendar, assignments, indexes, rate-limit buckets, and the non-destructive recipe tombstone schema; apply only after confirming the concrete `recipes(id)` migration target. <!-- sdd-owner: implementation -->
- [x] TRIANGULATE — extend the same unit and ephemeral-PostgreSQL tests for duplicate assignments, invalid check combinations, Unicode code-point boundaries, normalized HTML-like input, and migration preservation of a recipe assignment after `ON DELETE SET NULL`. <!-- sdd-owner: implementation -->
- [x] REFACTOR — consolidate domain constants and validation helpers inside `backend/src/comemos_en_casa/meal_calendar/` without changing the migration contract, then run `pytest` for the foundation tests and full baseline suite. <!-- sdd-owner: implementation -->

## PR 2 — repository, catalogue adapter, and HTTP calendar contract

- [ ] RED — add failing API and PostgreSQL integration tests in `backend/tests/meal_calendar/test_api_contract.py` and `test_repository.py` covering `/context` (read-only), Monday-validated weekly reads, normalized public recipe search/cursors, recipe detail, ordered mixed assignments, and the documented POST/PATCH/DELETE status/error payloads. <!-- sdd-owner: implementation -->
- [ ] GREEN — implement `backend/src/comemos_en_casa/meal_calendar/{repository.py,api.py,catalog_adapter.py}` and the application route registration discovery target so `/api/v1/meal-calendar` (read-only) serves the specified JSON UTF-8, `Cache-Control: no-store` resources using PostgreSQL as the source of truth. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — extend those tests for duplicate UUID-backed creates, repeat-create same-payload `200`, differing-payload `409 idempotency_conflict`, idempotent repeated delete, `404` after delete, current recipe-title joins, and the unavailable-recipe payload with no copied title/image snapshot. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — isolate HTTP translation from service and SQL concerns at the listed backend boundaries, retain stable error envelopes and ordering tie-breaks, and run `pytest` for API/repository plus all earlier tests. <!-- sdd-owner: implementation -->

## PR 3 — retries, idempotency/concurrency, guest access, and rate limiting

- [ ] RED — add failing tests in `backend/tests/meal_calendar/test_resilience_access.py` for startup-only `ENABLE_GUEST_USER` parsing, absent/false guest access requiring issue #6, exact guest context/banner flag, three 250/500/1000 ms retries after the first attempt, `503` failure mapping, trusted-proxy IP handling, and 60-read/30-write minute limits. <!-- sdd-owner: implementation -->
- [ ] GREEN — implement `backend/src/comemos_en_casa/meal_calendar/{rate_limit.py,settings.py,repository.py,api.py}` so access and atomic PostgreSQL buckets execute once per request before every feature route, guest mode uses only `calendar_key='shared'`, transient repository failures retry in fresh transactions, and API errors expose exact `429`/`503` messages, `Retry-After`, and limit headers. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — add failure-injection and concurrent-connection cases proving four total database attempts, internal retries do not consume extra quota, manual retry is a new request, limit increments cannot exceed either threshold, concurrent distinct UUID creates coexist, last confirmed PATCH wins, and a late PATCH cannot resurrect a deleted assignment. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — centralize retryable-driver classification, operation descriptors, access/rate middleware hooks, and error mapping without weakening fail-closed limiting or the issue #6 boundary; run `pytest` across all backend tests. <!-- sdd-owner: implementation -->

## PR 4 — frontend week state and calendar interactions

- [ ] RED — add focused frontend tests beside `frontend/src/features/meal-calendar/` for bootstrapping `/context` (read-only), Canary `Hoy`, tokenized week navigation with stale data/skeleton/inert editing, global and cell-preselected add flows, and mixed alphabetical cards; retain the frontend test command/output selected by the application scaffold. <!-- sdd-owner: implementation -->
- [ ] GREEN — implement `frontend/src/features/meal-calendar/{api-client.*,store.*,MealCalendar.*,WeekGrid.*,AssignmentEditor.*,RecipePicker.*}` and its route/shell discovery target to consume the stable API contract, show the guest banner before initial week loading, and render the Monday–Sunday Comida/Cena grid with recipe and free-text creation/edit/delete paths. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — add state tests for blur plus explicit `Guardar` including the focused field, disabled clean save, one in-flight request per revision, a changed-during-save follow-up, per-operation `Guardando`/two-second `Guardado`, queued navigation during saving, unsaved-change confirmation, and isolated stale-response handling. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — keep ephemeral drafts, request tokens, timers, modal/search/scroll state, and failed-operation descriptors in the feature store rather than the backend or a local calendar cache; rerun the focused frontend suite and `pytest`. <!-- sdd-owner: implementation -->

## PR 5 — failure UX, accessibility, responsive delivery, OpenAPI, and acceptance

- [ ] RED — add frontend/component and API contract tests for a retained failed draft or stale week under a loading overlay, exact database and rate-limit toasts with isolated `Reintentar`, cancellation of a pending manual retry on navigation, unavailable-recipe cards, modal context restoration, keyboard/touch tooltip behavior, and required accessible names/live feedback/focus return. <!-- sdd-owner: implementation -->
- [ ] GREEN — complete `frontend/src/features/meal-calendar/{Feedback.*,RecipeDetailModal.*,FreeTextTooltip.*,MealCalendar.*}` and styles so failed operations preserve only their own form, the modal is read-only, free text renders through text primitives, the weekly grid scrolls horizontally on mobile with sticky headers/slot column and vertically overflowing cells, and all specified banner, toast, focus, and live-region behavior is present. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — exercise desktop and mobile-touch viewports, dense cells, loading and read-failure states, `Escape`/focus restoration, tooltip hover/focus/tap, `aria-busy`/inert stale content, and guest-on versus guest-off behavior; add or update contract tests for exact response bodies, headers, and no out-of-scope controls. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — remove duplicated feedback, breakpoint, and accessibility helpers while preserving logical DOM order and 44×44 CSS-px touch targets; rerun the frontend suite and `pytest`. <!-- sdd-owner: implementation -->
- [ ] GREEN — create `docs/calendario-de-comidas/uso.md`, `docs/calendario-de-comidas/interfaz.md`, and `docs/interfaces/calendario-de-comidas.openapi.yaml` with the approved routes, schemas, error/limit headers, exact banner/toast strings, guest risk/disable-and-restart guidance, state/UI/accessibility/responsive behavior, and explicit exclusions. <!-- sdd-owner: implementation -->
- [ ] TRIANGULATE — validate the OpenAPI file against the implemented API contract and inspect the two documents against all five specifications, including #6 dependency wording and the approved shared-guest risk, correcting documentation drift rather than reintroducing stale test-setup claims. <!-- sdd-owner: implementation -->
- [ ] REFACTOR — make terminology, endpoint examples, and Spanish feedback consistent across the three documentation targets without expanding product scope; rerun the documentation/contract validation and `pytest`. <!-- sdd-owner: implementation -->
- [ ] Final verification — run the full `pytest` suite, applicable frontend suite, migration test against isolated PostgreSQL, API/OpenAPI contract checks, and manual keyboard plus mobile/desktop responsive acceptance; record RED/GREEN/TRIANGULATE/REFACTOR evidence by work unit and confirm no login implementation, privacy model, CAPTCHA, destructive migration rollback, or commits were introduced. <!-- sdd-owner: implementation -->
