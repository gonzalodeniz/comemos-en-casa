# Exploration: recipe catalogue foundation

**Change:** `recetas-publicas-privadas`
**Product source:** GitHub issue #5, “Feature: Gestión y organización de recetas”
**Status:** exploration complete for a first catalogue foundation slice; full recipe management remains a later delivery.

## Problem and value

The meal-calendar API needs a concrete recipe catalogue owner. The current repository has no `recipes` table, recipe migration, database driver, application framework, repository, or catalogue adapter. Calendar PR1 deliberately leaves `meal_assignments.recipe_id` nullable and defers the recipe foreign key rather than inventing a catalogue schema.

## Current evidence

- `backend/migrations/versions/0001_meal_calendar_foundation.sql` is the only migration. It creates calendar and rate-limit tables, not `recipes`.
- `backend/migrations/README.md` explicitly defers `REFERENCES recipes(id) ON DELETE SET NULL` until the real catalogue table exists.
- The existing backend contains only pure calendar domain code and tests.
- `docker-compose.yml` provides PostgreSQL 16; pytest is configured, but no database driver or web framework is present.
- Issue #5 is approved with GitHub label `status:approved`.

## Proposed first delivery boundary

Implement the smallest independent catalogue foundation that owns the `recipes(id)` contract required by calendar integration:

### Included

- Versioned, expand-only PostgreSQL migration for a stable UUID recipe identifier and the minimum public recipe fields needed by calendar search, detail, and current-title/image reads.
- Python domain/schema boundary for validating and normalizing the foundation fields.
- PostgreSQL access dependency and a repository/catalogue adapter only if the chosen application boundary is established by the design phase.
- Focused tests for migration shape, UUID identity, public title/image reads, and deletion behavior needed by the calendar tombstone contract.
- Documentation of ownership and migration ordering.

### Deferred

- Authenticated recipe management; issue #6 owns access control. Private recipe visibility does not exist.
- Full recipe editor, drafts, collections, favorites, frontend, and shopping-list integration.
- Calendar API or calendar repository implementation; those remain PR2A/PR2B work.
- Inventing a substitute catalogue table solely inside the calendar change.

## Constraints and decisions to resolve

1. Define the minimal recipe schema without contradicting issue #5 or the calendar contract.
2. Confirm the database access technology before adding a repository implementation; the repository currently has no driver or framework.
3. Keep the migration expand-only and provide a real owner for `recipes(id)` before the calendar foreign key is added.
4. Preserve current recipe title/image by joining the catalogue at read time; do not snapshot presentation fields into `meal_assignments`.
5. Keep the first slice within the 400-line review budget; use a chained PR only if the design forecast requires it.

## Recommendation

Proceed through proposal, specification, and design for this foundation slice. After it is implemented and merged, return to the stashed calendar PR2 planning branch, add the compatible `ON DELETE SET NULL` foreign key migration, and implement PR2A against this catalogue source of truth.
