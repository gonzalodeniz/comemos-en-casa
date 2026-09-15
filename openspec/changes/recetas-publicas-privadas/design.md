# Technical design: public recipe catalogue foundation

**Change:** `recetas-publicas-privadas`  
**Status:** ready for task planning  
**Basis:** `exploration.md`, `proposal.md`, and `specs/recipe-catalogue-foundation/spec.md`  
**Delivery constraint:** one reviewable implementation of at most 400 changed lines; `ask-on-risk` applies if task planning forecasts more

## 1. Decision summary

Add a catalogue-owned `0002_recipe_catalogue_foundation.sql` migration, a standard-library Python recipe schema boundary, and a small synchronous Psycopg 3 repository. The table stores a stable UUID plus current `title`, `image_url`, and `detail`. An internal `title_search_key` is written atomically with the title and indexed with PostgreSQL `pg_trgm` for accent-insensitive, case-insensitive substring search.

No web framework, ORM, migration framework, authentication model, visibility flag, or calendar implementation is introduced. All rows in this slice belong to the public catalogue. The product has no private recipes; a later authenticated-management change may add author or ownership data for editing permissions, but it must not add private visibility.

The catalogue migration does not inspect or alter `meal_assignments`. After this change is merged, calendar PR2 must take the next migration number and add its own `REFERENCES recipes(id) ON DELETE SET NULL` constraint. Existing calendar source, tests, and OpenSpec artifacts remain untouched.

## 2. Architecture and dependency choices

```text
Future catalogue or calendar service
              |
              v
RecipeCatalogueRepository (synchronous SQL, no HTTP concerns)
              |
              v
Psycopg 3 connection supplied by the caller
              |
              v
PostgreSQL 16: recipes + normalized-search index

Recipe schema boundary
  - creates/restores stable UUID identities
  - normalizes and validates foundation fields
  - derives title_search_key
  - exposes Recipe and RecipeListItem values
```

### Chosen components

| Component | Decision and reason |
| --- | --- |
| Python boundary | Frozen dataclasses and small functions under `comemos_en_casa.recipes.schemas`. This follows the existing backend style and needs no validation framework for three fields. |
| PostgreSQL driver | `psycopg[binary]` 3.x as a runtime dependency. Psycopg is the direct PostgreSQL driver, maps UUIDs natively, supports parameterized SQL, and is sufficient for four bounded repository operations. The binary extra avoids introducing system build prerequisites before an application image exists. Deployment may later move to the C implementation without changing repository contracts. |
| Repository | One concrete synchronous `RecipeCatalogueRepository` receiving an already-open Psycopg connection. The caller owns connection lifetime, commit/rollback, retries, and pooling. This keeps transaction policy out of a foundation with no application service yet. |
| Search index | An application-derived `title_search_key` plus a GIN trigram index supplied by the trusted PostgreSQL `pg_trgm` extension. It gives indexed literal substring matching while preserving Python's Unicode `casefold` behavior. |
| Migrations | Continue lexical, expand-only SQL files. Alembic is not added because the repository already has a versioned SQL convention and this change needs no dynamic migration API. |

### Explicitly rejected for this slice

- **FastAPI, Django, or another web framework:** there is no approved HTTP application boundary in this change. Adding one would create routing, lifecycle, and deployment decisions unrelated to the catalogue contract.
- **SQLAlchemy or another ORM:** four explicit SQL operations do not justify a mapping/session layer. A direct repository makes selected columns and transaction ownership visible.
- **Pydantic:** the existing domain uses dataclasses and standard-library validation. Pydantic would duplicate framework-independent rules and add a dependency solely for three fields.
- **PostgreSQL `unaccent` as the canonical normalizer:** PostgreSQL 16 lowercasing does not provide Python-equivalent Unicode case folding, and expression indexing requires function-volatility workarounds. Deriving one key in Python is smaller and has deterministic cross-environment behavior.
- **A `visibility` boolean:** private recipe visibility is not part of the product. Existing rows are public by definition, and future management metadata must not reinterpret this foundation as private authorization.

## 3. PostgreSQL design

`backend/migrations/versions/0002_recipe_catalogue_foundation.sql` will create:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE recipes (
    id uuid PRIMARY KEY,
    title text NOT NULL,
    image_url text NOT NULL,
    detail text NOT NULL,
    title_search_key text NOT NULL,
    CHECK (char_length(title) BETWEEN 1 AND 200),
    CHECK (title = btrim(title)),
    CHECK (char_length(image_url) BETWEEN 1 AND 2048),
    CHECK (image_url = btrim(image_url)),
    CHECK (image_url ~* '^https?://'),
    CHECK (char_length(detail) BETWEEN 1 AND 10000),
    CHECK (detail = btrim(detail)),
    CHECK (position(E'\r' in detail) = 0),
    CHECK (char_length(title_search_key) > 0)
);

CREATE INDEX recipes_title_search_idx
    ON recipes USING gin (title_search_key gin_trgm_ops);
```

The Python boundary remains authoritative for NFC, internal whitespace, complete URL parsing, and search-key derivation; SQL checks are defense in depth. `title_search_key` is internal persistence data and is never returned by the public read contract. Supported writes must update `title` and `title_search_key` in the same statement. Direct writes that bypass the repository/domain boundary are unsupported.

There is intentionally no database UUID default. The domain creates the UUID before persistence, so retries retain one identity and tests can inject a deterministic UUID. Ordinary updates never include `id` in the `SET` clause. No timestamps, users, owners, visibility, ingredients, steps, or calendar references are added.

`pg_trgm` is selected instead of an unindexed scan because the read contract is a catalogue search and uses contains matching. It is a PostgreSQL-provided trusted extension available in the supported PostgreSQL image. The migration owns the index but must not remove the extension during rollback because another database object may use it.

## 4. Python domain/schema boundary

Create `backend/src/comemos_en_casa/recipes/schemas.py` with these contracts:

- `RecipeValidationError(ValueError)` for rejected boundary values.
- Frozen `Recipe(id: UUID, title: str, image_url: str, detail: str)`.
- Frozen `RecipeListItem(id: UUID, title: str, image_url: str)` for search results.
- A creation factory that accepts foundation values and an injectable UUID factory defaulting to `uuid4`.
- A restoration/update factory that requires an existing UUID and applies the same field rules.
- `normalize_title_search(value: str) -> str`, shared by stored titles and search queries.

Normalization occurs before length validation:

1. Require a Python string and normalize it to NFC.
2. For `title`, trim surrounding whitespace and collapse every run of Unicode whitespace to one ASCII space. Require 1–200 Unicode code points.
3. For `image_url`, trim surrounding whitespace, require 1–2,048 characters, parse with `urllib.parse.urlsplit`, require a case-insensitive `http` or `https` scheme and a non-empty network location, and reject whitespace within the URL.
4. For `detail`, convert CRLF and lone CR to LF, trim surrounding whitespace, normalize to NFC, and require 1–10,000 Unicode code points.
5. For a title search key, case-fold the normalized text, decompose it with NFKD, remove Unicode combining marks, and normalize the result back to NFC. A search query also trims and collapses whitespace; an empty query is valid and lists catalogue rows.

The boundary does not sanitize HTML because the specification defines text normalization and validation, not rich text or markup acceptance. API-layer escaping/rendering remains a later concern; this foundation treats `detail` as opaque plain text.

## 5. Repository and read contracts

Create `backend/src/comemos_en_casa/recipes/repository.py`. The concrete repository uses parameterized Psycopg SQL and has only these methods:

| Method | Contract |
| --- | --- |
| `insert(recipe)` | Inserts the UUID and normalized fields plus the derived search key; it does not commit. |
| `update_foundation(recipe)` | Updates title, image URL, detail, and search key for `recipe.id`; never updates identity; returns whether a row existed. |
| `find_public_by_id(recipe_id)` | Returns `Recipe` with exactly current `id`, `title`, `image_url`, and `detail`, or `None`. |
| `search_public_by_title(query, limit=50)` | Returns current `RecipeListItem` values ordered by `title_search_key`, then UUID; validates `limit` from 1 through 50. |

Search uses literal contains semantics:

```sql
WHERE title_search_key LIKE '%' || :escaped_normalized_query || '%' ESCAPE '\'
ORDER BY title_search_key, id
LIMIT :limit
```

The repository escapes `\`, `%`, and `_`, so user input is literal rather than a SQL pattern. Values remain bound parameters. An empty normalized query omits the predicate and returns the first ordered page. Cursor pagination and HTTP response shapes are deferred because neither is required by this foundation's specification.

All rows are public by product decision, so the `public` method names state consumer intent rather than applying an authorization predicate. Future authenticated management may restrict writes, but public reads remain public and no private rows may be stored.

No generic repository protocol, unit-of-work abstraction, pool, retry loop, or exception-to-HTTP translation is added. Those policies belong to the future application service. A future calendar repository may use a `LEFT JOIN recipes` for current title/image reads; it must not copy those values into `meal_assignments`.

## 6. Data flow

### Create or update through the internal persistence boundary

1. A future use case supplies raw foundation values.
2. The schema boundary normalizes and validates them and either creates or preserves the UUID.
3. The repository derives the search key from the accepted title.
4. One parameterized statement writes foundation fields and key together within the caller's transaction.
5. Later reads return the same UUID and current catalogue values.

This is a persistence primitive, not a recipe-management API or publishing workflow.

### Search

1. Normalize the query with the same case/accent/whitespace algorithm used for stored keys.
2. Escape SQL wildcard characters.
3. Execute the indexed contains predicate with deterministic ordering and a bounded limit.
4. Return only UUID, current title, and current image URL.

For example, both stored `Tortilla Española` and query `tortilla espanola` produce `tortilla espanola` and match.

### Identity detail read

1. Require a UUID object at the repository boundary.
2. Select by `recipes.id` with a bound parameter.
3. Return exactly UUID, current title, current image URL, and current detail, or `None`.

No cache or snapshot exists, so updates are visible on the next committed read.

## 7. Migration and calendar PR2 ordering

1. Keep merged `0001_meal_calendar_foundation.sql` unchanged.
2. Apply catalogue-owned `0002_recipe_catalogue_foundation.sql`. It must also pass when applied by itself in a schema with no `meal_assignments` relation.
3. Deploy and verify the catalogue boundary/repository.
4. Only after this change is merged, restore/rebase the stashed calendar PR2 planning. Calendar owns the next available migration, expected to be `0003_meal_calendar_recipe_fk.sql` if no other migration lands first.
5. The calendar-owned migration adds `meal_assignments(recipe_id) REFERENCES recipes(id) ON DELETE SET NULL`; it must not recreate or alter catalogue columns.

Before adding that foreign key, calendar PR2 must check for non-null recipe IDs created before referential integrity existed. If any are present, delivery must pause for an explicit calendar-owned data decision: seed matching catalogue rows or convert those references to tombstones (`NULL`) in a reviewed data migration. Silently adding a failing constraint or deleting assignments is not allowed.

After the foreign key exists, deleting a recipe causes PostgreSQL to set only the referencing `recipe_id` to `NULL`; the assignment row remains. Catalogue code neither deletes assignments nor defines the foreign key. The shared `backend/migrations/README.md` may be corrected to record this ownership and ordering, but no file under `meal_calendar/`, no `0001` SQL, and no `calendario-de-comidas` artifact is changed.

## 8. Planned file changes

| Path | Change |
| --- | --- |
| `backend/migrations/versions/0002_recipe_catalogue_foundation.sql` | Create catalogue table, checks, extension, and search index. |
| `backend/migrations/README.md` | Name catalogue ownership and calendar-owned follow-up order. |
| `backend/src/comemos_en_casa/recipes/__init__.py` | Establish the bounded-context package only. |
| `backend/src/comemos_en_casa/recipes/schemas.py` | Foundation values, normalization, validation, and UUID creation/restoration. |
| `backend/src/comemos_en_casa/recipes/repository.py` | Four direct Psycopg operations. |
| `backend/tests/recipes/test_schemas.py` | Unit coverage for field and search normalization. |
| `backend/tests/recipes/test_repository.py` | PostgreSQL migration, reads, updates, search, and deletion compatibility. |
| `requirements.txt` | Add the bounded Psycopg 3 runtime dependency. |
| `requirements-dev.txt` | Include runtime requirements before pytest dependencies. |

No calendar source, calendar tests, calendar migrations, calendar OpenSpec artifact, frontend, or HTTP module is modified.

## 9. Test design

Implementation uses proportionate verification with the existing pytest configuration; strict TDD is not required.

### Unit tests

- Title is NFC-normalized, trimmed, and Unicode-whitespace-collapsed; blank, 201-code-point, and non-string titles fail.
- Detail converts CRLF and CR to LF, trims, preserves internal line breaks, counts Unicode code points, and rejects blank or over-10,000 values.
- Image URL is trimmed and accepts only absolute HTTP(S) values within 2,048 characters; relative, missing-host, unsupported-scheme, whitespace-containing, and non-string values fail.
- Search keys remove accents, use Unicode case folding, and collapse whitespace; `Tortilla Española` and `tortilla espanola` produce the same key.
- Creation generates/injects a UUID; restoration and field updates preserve it.

### PostgreSQL integration tests

Use the existing Docker PostgreSQL service and a transaction-local isolated schema, rolling back after each test group:

- Applying `0002` without calendar tables creates exactly `recipes`, with UUID primary-key identity, required fields, checks, and the trigram index.
- The migration SQL contains no `CREATE`, `ALTER`, or `REFERENCES` operation for `meal_assignments`; migration documentation records catalogue-then-calendar order.
- Insert a valid recipe through the repository, search it without case or accents, and verify the summary contains current UUID/title/image.
- Identity detail returns exactly current foundation values; an unknown UUID returns `None`.
- Update title/image/detail and search key, then verify the UUID is unchanged, old search no longer matches, and new search/detail return current values.
- Queries containing `%`, `_`, or `\` are treated literally.
- Apply `0001`, then `0002`, add the calendar-owned foreign key inside the test only, delete a referenced recipe, and assert the assignment remains with `recipe_id IS NULL`.

The compatibility test exercises the existing calendar migration as an input but does not edit calendar code or its tests.

## 10. Rollout and rollback

### Rollout

1. Install Psycopg in the application/test environment.
2. Verify `0002` and repository integration against PostgreSQL 16 in an isolated schema.
3. Back up production data and apply migrations in lexical order.
4. Deploy repository/domain code. No endpoint, feature flag, or user-visible behavior is activated.
5. Merge this foundation before calendar PR2 is rebased and assigned its later migration number.

There is no dual-write or data backfill because no earlier recipe relation exists.

### Rollback and recovery

- The committed migration has no destructive automatic downgrade.
- If application code must be rolled back, leave `recipes`, its data, and the index in place; the prior application does not depend on them.
- Before any real recipe data or downstream foreign key exists, an operator may remove the new table/index only in a disposable environment or through a separately reviewed production recovery action.
- Do not drop `pg_trgm` during rollback because extension ownership may be shared.
- After calendar PR2 adds its foreign key, never drop `recipes` or rewrite recipe UUIDs as part of an application rollback. Revert behavior while preserving schema/data and use an additive forward-fix migration.
- If a normalization defect is found, deploy corrected Python logic and an additive migration that recomputes `title_search_key` transactionally; do not mutate identity.

## 11. Review workload and delivery gate

The minimal implementation is forecast at **350–395 changed lines**:

| Work unit | Forecast |
| --- | ---: |
| Migration, dependency files, and migration notes | 45–55 |
| Recipe schema/domain boundary | 80–95 |
| Psycopg repository | 55–70 |
| Unit and PostgreSQL integration tests | 170–175 |
| **Total** | **350–395** |

This forecast deliberately excludes HTTP/API scaffolding, generic abstractions, pagination cursors, and calendar edits. Tests are not to be compressed or removed to meet the budget.

No delivery decision is required at design time because the smallest implementation is forecast below 400 lines. Task planning must recalculate against the actual branch diff. If the honest forecast or implementation reaches more than 400 changed lines, `ask-on-risk` requires pausing for a human choice between a chained delivery (schema/domain first, repository reads second; chain strategy then selected explicitly) or an explicitly accepted `size:exception`. Neither choice is inferred here.

## 12. Requirement traceability

| Requirement | Design evidence |
| --- | --- |
| Canonical UUID identity | §§3–5: one `recipes` table, application-created UUID, immutable update identity. |
| Minimum public fields | §§3–5: current title, image URL, and detail in table/domain/read contracts. |
| Normalization and validation | §4 plus unit tests in §9. |
| Case/accent-insensitive title search | §§2, 3, 5, and 6: shared Unicode search key and trigram contains query. |
| Current identity detail | §§5–6: uncached select of exact current foundation values. |
| Stable identifiers | §§3–6 and update integration test. |
| Migration ownership/order | §7 and migration-documentation test. |
| Calendar tombstone deletion | §§7 and 9: later calendar-owned `ON DELETE SET NULL` compatibility test. |
| Public-only foundation | §§1–2 and §5: all rows public, no inferred authorization model. |
| Calendar remains untouched | §§1, 7, and 8: only a read-only compatibility test consumes `0001`. |

## 13. Residual risks

- `title_search_key` can drift only if an operator bypasses the supported Python/repository write boundary. The explicit same-statement write contract and integration tests mitigate this; a database trigger is rejected as duplicated normalization logic.
- Trigram indexes may not accelerate every very short query, but results remain correct. Query-volume tuning is deferred until an HTTP boundary and production catalogue size exist.
- Installing `pg_trgm` requires database permission to create trusted extensions. Deployment must verify this before migration; if unavailable, delivery pauses rather than silently dropping the indexed-search requirement.
- The product does not support private recipe rows. No private data may be inserted under this schema or treated as protected.

**Next step:** create bounded implementation tasks with a fresh changed-line forecast. Do not restore or modify calendar PR2 planning until this catalogue foundation is merged.
