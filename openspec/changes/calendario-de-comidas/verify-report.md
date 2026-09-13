```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:7a1509fbbfb9e0f2c422f6fcdd6b170b24b66d836e5b6cc3e3083012e77f0dfa
verdict: fail
blockers: 20
critical_findings: 20
requirements: 1/30
scenarios: 1/39
test_command: .venv/bin/pytest -q
test_exit_code: 0
test_output_hash: sha256:dba147114f275ae0f2e9c99e2ca6e034b73a99d3a3f72cbac85fef6cb2d486e1
build_command: docker compose exec -T postgres pg_isready -U comemos -d comemos_en_casa
build_exit_code: 0
build_output_hash: sha256:6e168fc3b5a0662104b5e5da92e87b870e8b7c65fec827d267115b5123d18614
```

# PR1 Verification Report — calendario-de-comidas

## Status

**PR1 SLICE PASS WITH AN EXPLICIT GOVERNANCE EXCEPTION; WHOLE CHANGE FAIL / NOT ARCHIVE-READY.**

This formal verification is limited to **PR1 — foundation, temporal rules, and PostgreSQL schema** on `feature/calendario-de-comidas-pr1-foundation-schema`. Current behavior, focused migration execution, design coherence, and the five PR1 task checkboxes pass. The maintainer disposition in `apply-progress.md` admits the irrecoverable historical-RED gap for PR1 only without fabricating evidence.

The machine envelope remains `fail` because 20 implementation tasks for PR2–PR5 are unchecked. Under the task-checkbox contract each is a CRITICAL whole-change completeness and archive blocker, even though none is a defect in the approved PR1 slice. This is not a clean whole-change pass and the change is not ready to archive.

## Scope, status, and artifacts

- Branch: `feature/calendario-de-comidas-pr1-foundation-schema`.
- HEAD: `3552bb22a67d41392c6d67737973accda6401208`.
- Structured status: verify `ready`; artifact store `openspec`; `strict_tdd: true`.
- Action context: `repo-local`; workspace and allowed edit root `/opt/apps/comemos-en-casa`; no action-context warnings.
- Read completely: `proposal.md`, all five specs, `design.md`, `tasks.md`, `apply-progress.md` including the new maintainer disposition, `openspec/config.yaml`, the prior verify report, global strict-TDD verification guidance, every PR1 source/test/migration file, pytest configuration, dependencies, `.gitignore`, and Compose configuration.
- Evidence revision: SHA-256 over a 29-entry manifest of the retrieved artifacts, PR1 code/tests/migration, relevant configuration, strict-TDD guidance, exact command outputs, and current branch/HEAD/status/diff evidence. The prior/current report is excluded.
- The worktree is not clean. Verification applies to the exact current worktree, not HEAD alone.
- Verification changed no source, test, task, apply-progress, configuration, or migration file. The report is the only repository artifact authorized for update.

## Maintainer governance disposition and strict-TDD admission

The newly recorded disposition is explicit and internally consistent:

1. It accepts a **PR1-only exception** for the irrecoverable historical RED-evidence gap affecting the original temporal/text/schema behaviors.
2. It does not represent the missing RED run as authentic evidence. This report likewise makes no fabricated RED claim.
3. It leaves `strict_tdd: true` active. PR2 and every later PR still require authentic RED before implementation, then GREEN, TRIANGULATE, and REFACTOR evidence.
4. It is not a `size:exception`; the review-budget overage remains a warning.
5. It does not authorize PR2 and does not alter later task checkboxes.

Repository history still shows the original PR1 test paths and production implementation introduced together in commit `3552bb22a67d41392c6d67737973accda6401208`, with no retained pre-implementation failure output. The UUID runtime-guard regression remains the only authentic RED recorded: `.venv/bin/pytest -q backend/tests/meal_calendar/test_time_text.py::test_assignment_draft_rejects_a_recipe_value_that_is_not_a_uuid` failed because a string recipe identifier was accepted. The PostgreSQL oracle failure remains correctly excluded because it was a test-query defect after the migration existed.

**PR1 strict-TDD admission: PASS BY EXPLICIT, NARROW GOVERNANCE EXCEPTION.** The evidence gap remains documented as a warning; it is not repaired, relabeled, or generalized.

## Spec and scenario coverage

The five retrieved specs contain **30 requirements and 39 scenarios**, counted from their actual `### Requirement:` and `#### Scenario:` headings. Exactly **1 requirement and 1 scenario** are complete for the whole change: the Python/pytest implementation-platform requirement and runner scenario. PR1 establishes partial foundation evidence for additional requirements but does not claim API, access, resilience, frontend, or documentation completion.

| PR1 concern | Specification/design trace | Current evidence | Result |
|---|---|---|---|
| Canary week calculation | `calendario-semanal`; design §4 | Aware-instant conversion, Monday derivation, midnight/year-boundary/DST tests | PASS for domain foundation |
| Monday–Sunday dates | `calendario-semanal`; design §4 | Monday validation and seven date results | PASS for domain foundation |
| Free-text safety | `asignaciones-de-comida`; design §§5–6 | NFC, trim, text-only HTML parsing, whitespace rejection, 100/101-code-point tests | PASS for domain/schema foundation |
| Assignment shapes | Assignment and persistence clauses; design §6 | Date/slot/kind/value guards, including runtime UUID validation | PASS for domain/schema foundation |
| Shared singleton and duplicate cells | Guest/persistence clauses; design §6 | Exact `shared` seed, rejected non-shared key, two same-cell rows in PostgreSQL | PASS for schema foundation |
| Recipe tombstone direction | Deleted-recipe clauses; design §6 | Nullable `recipe_id`, no snapshots, deferred catalogue-owned FK documented | PASS for the safe PR1 state; FK execution remains deferred |
| Rate-limit storage foundation | Access-limit clauses; design §§6–7 | Bucket table, checks, key, and cleanup index execute in PostgreSQL | PASS for schema foundation |
| Backend platform | `persistencia-y-resiliencia` platform requirement | Python package and pytest runner execute | COMPLETE: 1 requirement / 1 scenario |

**Envelope coverage:** 1/30 requirements and 1/39 scenarios are complete for the whole change.

## Implementation and design coherence

- `current_week_start` rejects naive datetimes, converts aware instants to the resolved Canary zone, and derives Monday from the local date.
- `week_dates` uses date arithmetic and returns an inclusive Monday–Sunday tuple without timestamp/DST drift.
- `AssignmentDraft` rejects invalid dates, slots, kinds, cross-kind payloads, and recipe identifiers that are not `UUID` instances.
- Free text is parsed as text content, normalized to NFC, trimmed, and validated as 1–100 Python Unicode code points.
- `Europe/Canary` remains the product-facing name; runtime falls back to the valid IANA name `Atlantic/Canary` where necessary. Tests inject the resolved zone explicitly.
- The migration is expand-only, seeds only `shared`, permits UUID-distinct duplicate cells, enforces assignment shapes, and creates the three required secondary indexes plus the rate-limit bucket key.
- The repository has no concrete `recipes(id)` migration target. PR1 therefore correctly defers `REFERENCES recipes(id) ON DELETE SET NULL`; no unavailable deletion-preservation execution is claimed.
- No repository/API/catalogue adapter, access/retry middleware, frontend, login, privacy model, CAPTCHA, destructive rollback, or PR2 target was introduced.

## PostgreSQL readiness and migration evidence

**PASS.** `docker compose ps` showed:

```text
NAME                       IMAGE                COMMAND                  SERVICE    CREATED             STATUS                       PORTS
comemos-en-casa-postgres   postgres:16-alpine   "docker-entrypoint.s…"   postgres   About an hour ago   Up About an hour (healthy)   0.0.0.0:5433->5432/tcp, [::]:5433->5432/tcp
```

The exact readiness command `docker compose exec -T postgres pg_isready -U comemos -d comemos_en_casa` exited 0 with:

```text
/var/run/postgresql:5432 - accepting connections
```

The focused migration command `.venv/bin/pytest -q backend/tests/meal_calendar/test_schema_migration.py` exited 0:

```text
.....                                                                    [100%]
5 passed in 0.15s
```

Its PostgreSQL integration test sends the exact bytes of `backend/migrations/versions/0001_meal_calendar_foundation.sql` to:

```text
docker compose exec -T postgres psql --quiet --tuples-only --no-align --set ON_ERROR_STOP=1 -U comemos -d comemos_en_casa
```

inside an isolated transaction-local schema and asserts output `2`, `0`, `3`, `1`: two duplicate-cell assignments, zero prematurely claimed recipe foreign keys, three secondary indexes, and one valid rate-limit bucket count. It also proves rejection of a non-`shared` calendar key and an invalid mixed free-text/recipe shape. The transaction rolls back; the independent query `docker compose exec -T postgres psql --quiet --tuples-only --no-align --set ON_ERROR_STOP=1 -U comemos -d comemos_en_casa -c "SELECT count(*) FROM pg_namespace WHERE nspname = 'meal_calendar_test';"` returned `0`.

No application build command is configured. The envelope `build_command` is the required PostgreSQL readiness gate used by the executable migration test, not an application build claim.

## Test and validation commands

| Exact command | Exit | Exact observed result |
|---|---:|---|
| `.venv/bin/pytest -q` | 0 | `................ [100%]`; `16 passed in 0.17s` |
| `.venv/bin/pytest -q backend/tests/meal_calendar/test_schema_migration.py` | 0 | `..... [100%]`; `5 passed in 0.15s` |
| `docker compose exec -T postgres pg_isready -U comemos -d comemos_en_casa` | 0 | `/var/run/postgresql:5432 - accepting connections` |
| `docker compose ps` | 0 | PostgreSQL 16 service shown `Up ... (healthy)` |
| `docker compose exec -T postgres psql --quiet --tuples-only --no-align --set ON_ERROR_STOP=1 -U comemos -d comemos_en_casa -c "SELECT count(*) FROM pg_namespace WHERE nspname = 'meal_calendar_test';"` | 0 | `0` |
| `git diff --check` | 0 | no output |
| `git log --all --oneline --decorate -- backend/tests/meal_calendar/test_time_text.py backend/tests/meal_calendar/test_schema_migration.py backend/src/comemos_en_casa/meal_calendar backend/migrations/versions/0001_meal_calendar_foundation.sql` | 0 | only introduction commit `3552bb2` |
| `git show --name-status --format=fuller --no-renames 3552bb22a67d41392c6d67737973accda6401208 -- backend/tests/meal_calendar/test_time_text.py backend/tests/meal_calendar/test_schema_migration.py backend/src/comemos_en_casa/meal_calendar backend/migrations/versions/0001_meal_calendar_foundation.sql` | 0 | original tests, domain code, and migration shown as added together |

Exact output hashes:

- Full pytest: `sha256:dba147114f275ae0f2e9c99e2ca6e034b73a99d3a3f72cbac85fef6cb2d486e1`.
- Focused migration pytest: `sha256:bba54d0d911e4f4b3ff7099be56f23a579126dd0cbb36d88eb246b10ef320d5b`.
- PostgreSQL readiness: `sha256:6e168fc3b5a0662104b5e5da92e87b870e8b7c65fec827d267115b5123d18614`.
- Compose status: `sha256:34a21864689efe41c5fc7dd5af5ae465f7ccb426d4915a95f64827718896223d`.

## Strict TDD compliance

| Check | Result | Details |
|---|---|---|
| TDD evidence table present | PASS | `apply-progress.md` contains `## TDD Cycle Evidence` for both PR1 test files. |
| Reported test files exist | PASS | `test_time_text.py` and `test_schema_migration.py` exist and were audited in full. |
| GREEN remains true | PASS | 15/15 PR1 tests and 16/16 full-suite tests pass now. |
| Original RED retained | EXCEPTION | Original temporal/text/schema RED is irrecoverably absent; maintainer admits this for PR1 only and no RED is fabricated. |
| Authentic RED retained | PASS (limited) | The UUID guard has authentic recorded RED; the schema oracle defect is not mislabeled as RED. |
| TRIANGULATE adequate | PASS | Distinct temporal, Monday, Unicode, shape, singleton, duplicate, index, bucket, and real PostgreSQL cases exist. |
| Safety net historically sufficient | WARNING | The retained `14 passed` baseline occurred after the original PR1 implementation existed. |
| REFACTOR/full regression | PASS | Current full configured suite passes. |
| Future strict TDD | REQUIRED | `strict_tdd: true` remains active; the PR1 exception cannot be reused by PR2 or later work. |

**PR1 TDD disposition:** admitted only through the explicit maintainer exception. The historical evidence record remains incomplete and honest.

### Test layer distribution

| Layer | Tests | Files | Tool |
|---|---:|---:|---|
| Unit / SQL-contract | 14 | 2 | pytest |
| PostgreSQL integration | 1 | 1 | pytest + Docker Compose PostgreSQL |
| E2E | 0 | 0 | not applicable to PR1 |
| **PR1 total** | **15** | **2** | |

The sixteenth full-suite test is the pre-existing pytest runner smoke test and is not counted as PR1 behavioral evidence.

### Assertion quality

**PASS.** The two PR1 test files contain no tautologies, ghost loops, type-only assertions used alone, smoke-only PR1 tests, assertions that omit production/contract execution, implementation-detail CSS assertions, or mock-heavy tests. SQL-text assertions are triangulated by the real PostgreSQL execution test. The pre-existing `tests/pytest_smoke_test.py` contains `assert True`; it was not created or modified by PR1 and is excluded from PR1 behavior evidence.

### Coverage and quality tooling

- Changed-file coverage skipped: no coverage command/tool is configured.
- Linter skipped: no linter is configured.
- Type checker skipped: no type checker is configured.

These omissions are informational and not PR1 failures.

## Review workload and PR boundary

- The assigned feature-branch-chain PR1 boundary is respected. Only foundation domain code, migration/schema tests, and supporting pytest/PostgreSQL scaffolding are present; PR2 files (`repository.py`, `api.py`, `catalog_adapter.py`) and `frontend/` are absent.
- Core PR1 domain/migration/test content is **433 added lines** relative to `main`, already 33 lines above the 400-line budget.
- The full non-OpenSpec candidate is **461 changed lines** relative to `main`: 439 tracked additions, 1 tracked deletion, and 21 untracked `docker-compose.yml` lines. The report and OpenSpec bookkeeping are excluded.
- No `size:exception` exists or is inferred. The 61-line total overage remains a **WARNING** and requires ordinary review/delivery handling.
- The tested candidate is worktree-based: HEAD does not contain all verified corrections/configuration. This is a **WARNING** for candidate identity, not a test failure.
- The governance disposition does not authorize PR2. Verification did not start it.

## Task checkbox verification

All five PR1 implementation-owned rows are checked. The following **20 exact unchecked implementation rows** are approved later-slice scope, not PR1 defects. Nevertheless, each is a CRITICAL whole-change completeness and archive blocker. They prevent a clean whole-change pass and archive; they do not invalidate the admitted PR1 slice.

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

## Findings

### PR1 result

1. **PR1 is admitted by the explicit maintainer disposition.** Current domain behavior and PostgreSQL migration execution pass. The historical RED gap remains honestly documented and is not presented as evidence.

### CRITICAL — whole-change completeness/archive

1–20. **Twenty later implementation tasks remain unchecked.** Their exact lines are listed above. They are outside PR1 and must not be treated as PR1 failures, but they block whole-change completion and archive.

### WARNING

1. **The original PR1 RED sequence is irrecoverable and accepted only for PR1.** Future PRs receive no exception.
2. **Historical safety-net evidence is incomplete.** The retained `14 passed` baseline was captured after the original PR1 implementation existed.
3. **The 400-line review budget is exceeded without `size:exception`.** Core PR1 is 433 added lines; the full non-OpenSpec candidate is 461 changed lines.
4. **The verified candidate is not represented by HEAD alone.** Uncommitted PR1 corrections and supporting configuration remain in the worktree.
5. **The recipe tombstone foreign key is deferred.** This is the correct PR1 behavior because no concrete `recipes(id)` migration exists, but deletion-preservation execution remains future catalogue-owned evidence.

## Exact blockers

1–20. The 20 exact unchecked implementation task lines in **Task checkbox verification** block whole-change completion and archive. There is no remaining PR1 behavior, migration, or strict-TDD-admission blocker after applying the explicit PR1-only governance disposition.

## Next recommendation

**Treat the PR1 verification result as known and admitted, but do not start PR2.** Present the exact verified worktree for the normal PR1 review/delivery decision, preserving the review-budget warning and without inventing `size:exception`. PR2 requires separate authorization after that decision because the maintainer disposition explicitly does not authorize it. Keep `strict_tdd: true`, retain authentic RED before any future implementation, leave all 20 later checkboxes untouched until their assigned slices execute, and do not archive the overall change.
