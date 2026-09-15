# Meal-calendar PostgreSQL migrations

Files in `versions/` are ordered, expand-only SQL migrations. Apply each version once in lexical order. `0001_meal_calendar_foundation.sql` creates the shared-calendar foundation and deliberately has no destructive downgrade.

The recipe catalogue owns `0002_recipe_catalogue_foundation.sql`, which creates the canonical `recipes(id)` relation and its public foundation fields. Apply `0002_recipe_catalogue_foundation.sql` before calendar integration; it is independently applicable and does not depend on calendar tables.

The calendar owns a later migration that adds `meal_assignments.recipe_id REFERENCES recipes(id) ON DELETE SET NULL` after `0002_recipe_catalogue_foundation.sql` exists. That calendar migration must not recreate or redefine `recipes`; future recipe-schema expansions remain catalogue-owned.

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
