# Meal-calendar PostgreSQL migrations

Files in `versions/` are ordered, expand-only SQL migrations. Apply each version once in lexical order. `0001_meal_calendar_foundation.sql` creates the shared-calendar foundation and deliberately has no destructive downgrade.

The recipe catalogue owns `0002_recipe_catalogue_foundation.sql`, which creates the canonical `recipes(id)` relation and its public foundation fields. It is independently applicable and must be applied before calendar integration; it does not depend on calendar tables.

The calendar owns `0003_meal_calendar_recipe_fk.sql`. Apply all migrations in lexical order: `0001`, then `0002`, then `0003`. `0003` adds `meal_assignments.recipe_id REFERENCES recipes(id) ON DELETE SET NULL` only after the catalogue relation exists. It must not recreate or redefine `recipes`; future recipe-schema expansions remain catalogue-owned.

`0004_authentication.sql` adds Google OpenID Connect identities and opaque server-side session storage. Apply it after `0003`. It creates independent `users` and `auth_sessions` relations; it does not change recipe visibility or any recipe table. Browser session and OAuth state values are stored only as SHA-256 hashes, while the OIDC nonce is retained only for the short-lived authorization callback validation.

`0005_recipe_management.sql` expands the catalogue after authentication. It adds the explicitly public `draft`/`published` status, allows recipes without an image until a local upload is attached, and adds normalized ordered `recipe_ingredients` and `recipe_preparation_steps` relations. It leaves `meal_assignments.recipe_id` intact, so the existing `ON DELETE SET NULL` behavior remains in force when a recipe is deleted.

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
