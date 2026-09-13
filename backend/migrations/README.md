# Meal-calendar PostgreSQL migrations

Files in `versions/` are ordered, expand-only SQL migrations. Apply each version once in lexical order. `0001_meal_calendar_foundation.sql` creates the shared-calendar foundation and deliberately has no destructive downgrade.

The repository has no concrete `recipes(id)` table or recipe migration as of this migration. Therefore `0001` creates nullable `recipe_id` and the recipe tombstone-compatible check, but does **not** add a foreign key to an invented table. A later migration owned by the real recipe catalogue must add `REFERENCES recipes(id) ON DELETE SET NULL` after that concrete table exists.

## Local verification

Start the PostgreSQL service before running the migration integration test:

```bash
docker compose up -d postgres
.venv/bin/pytest -q
```

The configured test paths include both `tests/` and `backend/tests/`. The migration test applies the SQL in an isolated transaction-local schema and rolls it back, so it does not modify the persistent development database. Check service readiness with:

```bash
docker compose exec -T postgres pg_isready -U comemos -d comemos_en_casa
```
