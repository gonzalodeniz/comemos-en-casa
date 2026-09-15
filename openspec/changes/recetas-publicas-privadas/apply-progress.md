# Apply progress: recipe catalogue foundation

## Completed work

- [x] RED — added three migration-contract tests in `backend/tests/recipes/test_repository.py` for the planned `recipes` UUID primary key and foundation columns, calendar-table independence, and documented catalogue-before-calendar ownership/order.
- [x] Persisted the matching first RED checkbox in `tasks.md` immediately after authentic failing evidence.

## Files changed

- `backend/tests/recipes/test_repository.py`
- `openspec/changes/recetas-publicas-privadas/tasks.md`
- `openspec/changes/recetas-publicas-privadas/apply-progress.md`

## TDD Cycle Evidence

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Foundation migration RED | `backend/tests/recipes/test_repository.py` | Contract/unit | N/A (new file) | Failed: 3 failed, because `0002_recipe_catalogue_foundation.sql` does not exist and migration notes do not yet document it | Not started; user requested stop after RED | Not started | Not started |

## Test command and exact output

```console
$ .venv/bin/pytest -q backend/tests/recipes/test_repository.py
FFF                                                                      [100%]
=================================== FAILURES ===================================
__ test_catalogue_migration_creates_the_recipe_identity_and_foundation_fields __

    def test_catalogue_migration_creates_the_recipe_identity_and_foundation_fields() -> None:
>       sql = MIGRATION.read_text(encoding="utf-8")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

backend/tests/recipes/test_repository.py:17: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/lib/python3.12/pathlib.py:1029: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = PosixPath('/opt/apps/comemos-en-casa/backend/migrations/versions/0002_recipe_catalogue_foundation.sql')
mode = 'r', buffering = -1, encoding = 'utf-8', errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """Open the file pointed by this path and return a file object.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       FileNotFoundError: [Errno 2] No such file or directory: '/opt/apps/comemos-en-casa/backend/migrations/versions/0002_recipe_catalogue_foundation.sql'

/usr/lib/python3.12/pathlib.py:1015: FileNotFoundError
__________ test_catalogue_migration_has_no_calendar_table_dependency ___________

    def test_catalogue_migration_has_no_calendar_table_dependency() -> None:
>       sql = MIGRATION.read_text(encoding="utf-8")
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

backend/tests/recipes/test_repository.py:32: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
/usr/lib/python3.12/pathlib.py:1029: in read_text
    with self.open(mode='r', encoding=encoding, errors=errors) as f:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = PosixPath('/opt/apps/comemos-en-casa/backend/migrations/versions/0002_recipe_catalogue_foundation.sql')
mode = 'r', buffering = -1, encoding = 'utf-8', errors = None, newline = None

    def open(self, mode='r', buffering=-1, encoding=None,
             errors=None, newline=None):
        """Open the file pointed by this path and return a file object.
        """
        if "b" not in mode:
            encoding = io.text_encoding(encoding)
>       return io.open(self, mode, buffering, encoding, errors, newline)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E       FileNotFoundError: [Errno 2] No such file or directory: '/opt/apps/comemos-en-casa/backend/migrations/versions/0002_recipe_catalogue_foundation.sql'

/usr/lib/python3.12/pathlib.py:1015: FileNotFoundError
_ test_migration_notes_record_catalogue_ownership_before_calendar_integration __

    def test_migration_notes_record_catalogue_ownership_before_calendar_integration() -> None:
        migration_notes = MIGRATION_NOTES.read_text(encoding="utf-8").lower()

>       assert "0002_recipe_catalogue_foundation.sql" in migration_notes
E       AssertionError: assert '0002_recipe_catalogue_foundation.sql' in '# meal-calendar postgresql migrations\n\nfiles in `versions/` are ordered, expand-only sql migrations. apply each ver...ck service readiness with:\n\n```bash\ndocker compose exec -t postgres pg_isready -u comemos -d comemos_en_casa\n```\n'

backend/tests/recipes/test_repository.py:42: AssertionError
=========================== short test summary info ============================
FAILED backend/tests/recipes/test_repository.py::test_catalogue_migration_creates_the_recipe_identity_and_foundation_fields
FAILED backend/tests/recipes/test_repository.py::test_catalogue_migration_has_no_calendar_table_dependency
FAILED backend/tests/recipes/test_repository.py::test_migration_notes_record_catalogue_ownership_before_calendar_integration
3 failed in 0.06s

Command exited with code 1
```

## Verification evidence

The focused RED command failed as intended: the catalogue migration is absent, and the existing migration notes do not name the planned `0002` ownership/order. No production code, migration, dependency, calendar artifact, or later schema/repository behavior was added.

## Design deviations

None. This work unit adds only the planned RED contract tests.

## Remaining tasks

- [ ] GREEN — add `backend/migrations/versions/0002_recipe_catalogue_foundation.sql`, update migration ownership notes, and add the minimal `psycopg[binary]` runtime dependency without modifying `0001` or calendar artifacts.
- [ ] TRIANGULATE — execute `0002` in an isolated PostgreSQL transaction-local schema without calendar tables; assert checks, `pg_trgm` index, expand-only behavior, and migration ordering.
- [ ] REFACTOR — keep the SQL contract explicit and bounded; run the migration tests and full existing suite.
- [ ] RED — add failing tests under `backend/tests/recipes/test_schemas.py` for UUID creation/restoration, NFC and whitespace normalization, title/detail lengths, absolute HTTP(S) image URLs, and accent-insensitive search keys.
- [ ] GREEN — implement `backend/src/comemos_en_casa/recipes/__init__.py` and `schemas.py` with frozen recipe/list-item values, normalization, validation, and stable UUID factories.
- [ ] TRIANGULATE — cover CRLF/CR detail normalization, Unicode code-point boundaries, wildcard characters, invalid URL hosts/schemes, and unchanged IDs on updates.
- [ ] REFACTOR — consolidate validation helpers without changing the specified contract; run the focused schema tests and full suite.
- [ ] RED — extend `backend/tests/recipes/test_repository.py` with failing insert, update, identity-detail, current-value, bounded literal title-search, and unknown-ID cases.
- [ ] GREEN — add `backend/src/comemos_en_casa/recipes/repository.py` with parameterized Psycopg 3 SQL, caller-owned transactions, current title/image/detail reads, deterministic ordering, and escaped literal search.
- [ ] TRIANGULATE — verify updated title/image/detail and search-key consistency, stable UUIDs, limits 1–50, `%`/`_`/`\` literal queries, and the later calendar-owned tombstone FK compatibility in an isolated test-only schema.
- [ ] REFACTOR — isolate SQL mapping from schema validation, retain no HTTP/retry/pooling policy, and run repository, schema, migration, and full regression tests.
- [ ] Confirm no calendar source, calendar migration, calendar OpenSpec artifact, private-access behavior, authentication, full recipe UI, collection/favorite workflow, or HTTP route was introduced.
- [ ] Confirm the catalogue migration is independently applicable before calendar integration and that PR2 can add the FK without redefining `recipes`.

## Workload and PR boundary

This is the isolated `recipe catalogue RED migration tests` work unit. It adds 46 lines to a new test file and stays below the 400-line review budget. No commit was created.

## Structured status consumed

- `changeName`: `recetas-publicas-privadas`
- `artifactStore`: `openspec`
- `applyState`: `ready`
- `actionContext`: `repo-local` at `/opt/apps/comemos-en-casa`
- `allowedEditRoots`: `/opt/apps/comemos-en-casa`
- Action-context warnings: none.

## Native attempt receipt

- Acquired `recipe catalogue RED migration tests` with request ID `c58ef8df-0c42-4945-a58-2f7b5190747f`.
- Settled the authentic RED evidence as `passed`; native settlement returned `blocked` with reason `maintainer_decision` for the attempt or changed-line budget.
- Native status after settlement reports revision `sha256:d4ada9be46102c848b4dea0736222df1feb4b5fc760ca38f3d4eadb061a2e847`, cumulative changed lines `135` against the declared `100` limit, `decision_required: true`, and `next_action: reset`.
- No further runtime work was started after the blocked settlement. A maintainer must reset the objective before any later native attempt.

## RED closure

- [x] Re-ran the existing focused RED contract suite without changing source, migration, dependency, calendar, or test files.
- The persisted first RED task remains visibly checked in `tasks.md`; no later work unit was started.

### Closure verification

```console
$ .venv/bin/pytest -q backend/tests/recipes/test_repository.py
FFF
3 failed in 0.05s
```

The failures are authentic and expected for RED: the first two tests raise `FileNotFoundError` because `0002_recipe_catalogue_foundation.sql` is absent, and the ownership/order test fails because `backend/migrations/README.md` does not yet name that migration. This confirms the test contract is not a false pass or unrelated infrastructure failure.

### Native attempt closure

- Work unit: `recipe catalogue RED migration tests closure`
- Budget: one attempt, 250 changed lines
- Evidence revision: `sha256:40c8a68e86ed99b3f19f8c6fe9a77640417cb67ad7aeec874ad38ba460c2299a`
- Native settlement: `complete` (`passed` outcome)
- No commit was created and no further work units were acquired.

### TDD Cycle Evidence

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Foundation migration RED closure | `backend/tests/recipes/test_repository.py` | Contract/unit | N/A (existing RED evidence) | Confirmed: 3 expected failures | Not started; closure-only scope | Not started | Not started |

### Closure status

- `changeName`: `recetas-publicas-privadas`
- `artifactStore`: `openspec`
- `applyState`: `ready` when consumed
- `actionContext`: `repo-local` at `/opt/apps/comemos-en-casa`
- `allowedEditRoots`: `/opt/apps/comemos-en-casa`
- Action-context warnings: none.

## GREEN work unit: recipe catalogue migration and dependency

- [x] GREEN — added the independent, catalogue-owned `0002_recipe_catalogue_foundation.sql` migration with the required `recipes` columns, defense-in-depth checks, `pg_trgm` extension, and trigram index.
- [x] Updated `backend/migrations/README.md` to state that catalogue-owned `0002` applies before the later calendar-owned `meal_assignments.recipe_id REFERENCES recipes(id) ON DELETE SET NULL` migration.
- [x] Added the `psycopg[binary]` runtime requirement in `requirements.txt` and included it from `requirements-dev.txt`.
- [x] Updated the persisted GREEN checkbox in `tasks.md` immediately after focused tests passed.

### Files changed in this work unit

- `backend/migrations/versions/0002_recipe_catalogue_foundation.sql`
- `backend/migrations/README.md`
- `requirements.txt`
- `requirements-dev.txt`
- `openspec/changes/recetas-publicas-privadas/tasks.md`
- `openspec/changes/recetas-publicas-privadas/apply-progress.md`

### TDD Cycle Evidence

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Foundation migration and dependency GREEN | `backend/tests/recipes/test_repository.py` | Contract/unit | N/A — the persisted RED contract intentionally failed before this work unit | Preserved from the completed RED work unit: 3 authentic failures | Passed: 3 focused migration-contract tests | Deferred to the next unchecked TRIANGULATE task; user scoped this run to GREEN only | Deferred to the next unchecked REFACTOR task; no refactor was performed |

### GREEN test command and exact output

```console
$ .venv/bin/pytest -q backend/tests/recipes/test_repository.py
...                                                                      [100%]
3 passed in 0.01s
```

### Verification evidence

The existing RED contract now passes without modifying `0001`, calendar source or tests, recipe schemas, or repository implementation. The migration SQL contains no calendar-table references, and the migration notes document the required ownership/order.

### Design deviations

None.

### Remaining tasks

- [ ] TRIANGULATE — execute `0002` in an isolated PostgreSQL transaction-local schema without calendar tables; assert checks, `pg_trgm` index, expand-only behavior, and migration ordering.
- [ ] REFACTOR — keep the SQL contract explicit and bounded; run the migration tests and full existing suite.
- [ ] RED — add failing tests under `backend/tests/recipes/test_schemas.py` for UUID creation/restoration, NFC and whitespace normalization, title/detail lengths, absolute HTTP(S) image URLs, and accent-insensitive search keys.
- [ ] GREEN — implement `backend/src/comemos_en_casa/recipes/__init__.py` and `schemas.py` with frozen recipe/list-item values, normalization, validation, and stable UUID factories.
- [ ] TRIANGULATE — cover CRLF/CR detail normalization, Unicode code-point boundaries, wildcard characters, invalid URL hosts/schemes, and unchanged IDs on updates.
- [ ] REFACTOR — consolidate validation helpers without changing the specified contract; run the focused schema tests and full suite.
- [ ] RED — extend `backend/tests/recipes/test_repository.py` with failing insert, update, identity-detail, current-value, bounded literal title-search, and unknown-ID cases.
- [ ] GREEN — add `backend/src/comemos_en_casa/recipes/repository.py` with parameterized Psycopg 3 SQL, caller-owned transactions, current title/image/detail reads, deterministic ordering, and escaped literal search.
- [ ] TRIANGULATE — verify updated title/image/detail and search-key consistency, stable UUIDs, limits 1–50, `%`/`_`/`\` literal queries, and the later calendar-owned tombstone FK compatibility in an isolated test-only schema.
- [ ] REFACTOR — isolate SQL mapping from schema validation, retain no HTTP/retry/pooling policy, and run repository, schema, migration, and full regression tests.
- [ ] Confirm no calendar source, calendar migration, calendar OpenSpec artifact, private-access behavior, authentication, full recipe UI, collection/favorite workflow, or HTTP route was introduced.
- [ ] Confirm the catalogue migration is independently applicable before calendar integration and that PR2 can add the FK without redefining `recipes`.

### Workload and PR boundary

This isolated `recipe catalogue GREEN migration dependency` work unit adds 26 lines across migration, dependency, and migration-note files (excluding the required task/progress evidence) and remains below the 400-line review budget. No commit was created.

### Structured status consumed

- `changeName`: `recetas-publicas-privadas`
- `artifactStore`: `openspec`
- `applyState`: `ready`
- `actionContext`: `repo-local` at `/opt/apps/comemos-en-casa`
- `allowedEditRoots`: `/opt/apps/comemos-en-casa`
- Action-context warnings: none.

### Native attempt

- Acquired a fresh attempt for `recipe catalogue GREEN migration dependency` with request ID `961c15f7-468c-4f5a-a484-7f384faaa9fd`, one allowed attempt, and a 250 changed-line bound.

## TRIANGULATE retry preflight

- No TRIANGULATE test, migration, or production file was changed, and the TRIANGULATE checkbox remains unchecked.
- The required fresh native acquire was attempted with request ID `03d0f4e1-70ff-458c-8d9c-cafeec9b525b`, work unit `recipe catalogue TRIANGULATE migration retry`, one attempt, and a 220-line bound.
- Acquire returned no opaque token and did not return `proceed`; therefore PostgreSQL Compose and pytest were not launched, no settlement was possible, and this retry stopped before the strict-TDD safety-net/RED execution.

### Native acquire output

```console
$ gentle-ai sdd-attempt acquire --cwd "/opt/apps/comemos-en-casa" --change "recetas-publicas-privadas" --request-id "03d0f4e1-70ff-458c-8d9c-cafeec9b525b" --work-unit "recipe catalogue TRIANGULATE migration retry" --evidence-goal "prove 0002 independently applies and enforces the PostgreSQL migration contract" --max-attempts 1 --max-changed-lines 220
Error: untracked files require an explicit declaration; run `gentle-ai review status --cwd <repo> --contract gentle-ai.review-integration/v2 --agent <runtime> --next-transition` to obtain the canonical inventory, then rerun `gentle-ai sdd-attempt acquire` with --untracked-scope=exclude --expected-untracked-inventory=sha256:df72205dcd4694a02a8cbf09e67d75398b4085baa7e89fb7bb94e10352bf9a77 or --untracked-scope=select --intended-untracked=<repo-relative-path> --expected-untracked-inventory=sha256:df72205dcd4694a02a8cbf09e67d75398b4085baa7e89fb7bb94e10352bf9a77

Command exited with code 1
```

### Required inventory diagnostic output

```console
$ gentle-ai review status --cwd "/opt/apps/comemos-en-casa" --contract gentle-ai.review-integration/v2 --agent "sdd-apply" --next-transition
{
  "schema": "gentle-ai.review-integration.failure/v2",
  "contract": "gentle-ai.review-integration/v2",
  "operation": "review.status",
  "phase": "preflight",
  "code": "immutable_review_transport_unsupported",
  "message": "The active runtime cannot provide immutable receipt-review transport.",
  "mutation_outcome": "not_started",
  "authority_applicability": "not_evaluated",
  "retry_safe": false,
  "replayability": "not_replayable",
  "required_inputs": [],
  "next_action": "stop",
  "cause": "the active runtime is not eligible for immutable receipt review; exit receipt-driven review with `gentle-ai review mode disable --scope clone --cwd <repo>`; supported immutable review runtimes: claude-code, opencode, codex, pi"
}
Error: The active runtime cannot provide immutable receipt-review transport. [immutable_review_transport_unsupported]

Command exited with code 1
```

### TDD Cycle Evidence

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Foundation migration TRIANGULATE retry | `backend/tests/recipes/test_repository.py` | PostgreSQL integration | Not run: native acquire did not proceed | Not started: native acquire preflight blocked | Existing GREEN retained; not reused as an objective | Blocked before test execution | Not started |

### Remaining tasks

- [ ] TRIANGULATE — execute `0002` in an isolated PostgreSQL transaction-local schema without calendar tables; assert checks, `pg_trgm` index, expand-only behavior, and migration ordering.
- [ ] REFACTOR — keep the SQL contract explicit and bounded; run the migration tests and full existing suite.
- [ ] RED — add failing tests under `backend/tests/recipes/test_schemas.py` for UUID creation/restoration, NFC and whitespace normalization, title/detail lengths, absolute HTTP(S) image URLs, and accent-insensitive search keys.
- [ ] GREEN — implement `backend/src/comemos_en_casa/recipes/__init__.py` and `schemas.py` with frozen recipe/list-item values, normalization, validation, and stable UUID factories.
- [ ] TRIANGULATE — cover CRLF/CR detail normalization, Unicode code-point boundaries, wildcard characters, invalid URL hosts/schemes, and unchanged IDs on updates.
- [ ] REFACTOR — consolidate validation helpers without changing the specified contract; run the focused schema tests and full suite.
- [ ] RED — extend `backend/tests/recipes/test_repository.py` with failing insert, update, identity-detail, current-value, bounded literal title-search, and unknown-ID cases.
- [ ] GREEN — add `backend/src/comemos_en_casa/recipes/repository.py` with parameterized Psycopg 3 SQL, caller-owned transactions, current title/image/detail reads, deterministic ordering, and escaped literal search.
- [ ] TRIANGULATE — verify updated title/image/detail and search-key consistency, stable UUIDs, limits 1–50, `%`/`_`/`\` literal queries, and the later calendar-owned tombstone FK compatibility in an isolated test-only schema.
- [ ] REFACTOR — isolate SQL mapping from schema validation, retain no HTTP/retry/pooling policy, and run repository, schema, migration, and full regression tests.
- [ ] Confirm no calendar source, calendar migration, calendar OpenSpec artifact, private-access behavior, authentication, full recipe UI, collection/favorite workflow, or HTTP route was introduced.
- [ ] Confirm the catalogue migration is independently applicable before calendar integration and that PR2 can add the FK without redefining `recipes`.

### Workload and PR boundary

The requested work unit is limited to migration TRIANGULATE. It authored progress evidence only; no test or production lines were changed, and no commit was created. The 400-line review budget is not at risk.

### Structured status consumed

- `changeName`: `recetas-publicas-privadas`
- `artifactStore`: `openspec`
- `applyState`: `ready`
- `actionContext`: `repo-local` at `/opt/apps/comemos-en-casa`
- `allowedEditRoots`: `/opt/apps/comemos-en-casa`
- Action-context warnings: none.

### Blocker

The native attempt cannot acquire while untracked work exists because its required inventory command reports `immutable_review_transport_unsupported` and `next_action: stop`. A runtime eligible for immutable receipt-review transport, or an authorized review-mode/inventory resolution, is required before retrying TRIANGULATE.
- Acquired a fresh attempt for `recipe catalogue GREEN migration dependency` with request ID `961c15f7-468c-4f5a-a484-7f384faaa9fd`, one allowed attempt, and a 250 changed-line bound.
