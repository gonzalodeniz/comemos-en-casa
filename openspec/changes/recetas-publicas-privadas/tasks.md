# Tasks: recipe catalogue foundation

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | 350–395 |
| 400-line budget risk | Medium; pause if the honest diff exceeds 400 |
| Delivery strategy | ask-on-risk |
| Chained PRs recommended | No, unless implementation exceeds the budget |

## Scope boundary

This change owns the canonical public `recipes(id)` relation and minimum current title/image/detail read contract. It does not implement private access, authentication, full recipe management, collections, favorites, frontend, HTTP routes, or calendar code. Calendar PR2 remains untouched until this foundation is merged; it then owns the later `meal_assignments.recipe_id REFERENCES recipes(id) ON DELETE SET NULL` migration.

## Strict TDD rule

For every work unit, retain exact test names and command output: RED, GREEN, TRIANGULATE, and REFACTOR. Use `.venv/bin/pytest -q` and the existing PostgreSQL Compose service. Do not claim a passing result without executing the configured runner.

## Work units

### Foundation migration and dependency

- [x] RED — add failing migration-contract tests under `backend/tests/recipes/test_repository.py` proving the catalogue migration creates `recipes(id uuid primary key, title, image_url, detail, title_search_key)`, is independent of calendar tables, and documents ownership/order.
- [x] GREEN — add `backend/migrations/versions/0002_recipe_catalogue_foundation.sql`, update migration ownership notes, and add the minimal `psycopg[binary]` runtime dependency without modifying `0001` or calendar artifacts.
- [x] TRIANGULATE — execute `0002` in an isolated PostgreSQL transaction-local schema without calendar tables; assert checks, `pg_trgm` index, expand-only behavior, and migration ordering.
- [x] REFACTOR — keep the SQL contract explicit and bounded; run the migration tests and full existing suite.

### Recipe domain boundary

- [x] RED — add failing tests under `backend/tests/recipes/test_schemas.py` for UUID creation/restoration, NFC and whitespace normalization, title/detail lengths, absolute HTTP(S) image URLs, and accent-insensitive search keys.
- [x] GREEN — implement `backend/src/comemos_en_casa/recipes/__init__.py` and `schemas.py` with frozen recipe/list-item values, normalization, validation, and stable UUID factories.
- [x] TRIANGULATE — cover CRLF/CR detail normalization, Unicode code-point boundaries, wildcard characters, invalid URL hosts/schemes, and unchanged IDs on updates.
- [x] REFACTOR — consolidate validation helpers without changing the specified contract; run the focused schema tests and full suite.

### Catalogue repository

- [x] RED — extend `backend/tests/recipes/test_repository.py` with failing insert, update, identity-detail, current-value, bounded literal title-search, and unknown-ID cases.
- [x] GREEN — add `backend/src/comemos_en_casa/recipes/repository.py` with parameterized Psycopg 3 SQL, caller-owned transactions, current title/image/detail reads, deterministic ordering, and escaped literal search.
- [x] TRIANGULATE — verify updated title/image/detail and search-key consistency, stable UUIDs, limits 1–50, `%`/`_`/`\` literal queries, and the later calendar-owned tombstone FK compatibility in an isolated test-only schema.
- [x] REFACTOR — isolate SQL mapping from schema validation, retain no HTTP/retry/pooling policy, and run repository, schema, migration, and full regression tests.

## Final boundary check

- [x] Confirm no calendar source, calendar migration, calendar OpenSpec artifact, private-access behavior, authentication, full recipe UI, collection/favorite workflow, or HTTP route was introduced.
- [x] Confirm the catalogue migration is independently applicable before calendar integration and that PR2 can add the FK without redefining `recipes`.
