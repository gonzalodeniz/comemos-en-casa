# Categorize recipes with global labels

## Goal
Allow recipes to be categorized with global labels so users can discover recipes by one or more labels.

## Tasks
- [x] Define global label domain, normalization, colors, and lifecycle.
- [x] Define recipe create/edit payloads and the public label autocomplete API.
- [x] Define public catalog filtering with repeated `label` parameters and AND semantics.
- [x] Define removal of draft/published lifecycle and the unified Recetas catalog.
- [x] Define and implement frontend/backend regression coverage.
- [ ] **Pending after this user story:** remove the former “Mis recetas” area, including its endpoints, components, tests, and links for favorites and collections.

**Evidence:** `cc8f5de` (label contracts), `2ad5a2e` (backend/API and public lifecycle), `92531aa` (frontend workflow), `5f71d47` (migration coverage); `make test` passed (132 tests, frontend typecheck/build) and frontend tests passed (17 tests).

## Confirmed behavior
- Labels are global and may be created implicitly while creating or editing a recipe.
- Labels normalize to lowercase, preserve accents, trim/collapse whitespace, allow internal spaces and special characters, and have a 25-character maximum.
- Empty label values are ignored; duplicate normalized labels are deduplicated.
- A recipe may have zero to ten labels; excess labels are ignored after deduplication.
- Labels expose `id`, `name`, and `color`; unused labels are deleted transactionally.
- Anonymous users may create, edit, delete recipes, and manage images for now; deletion confirmation belongs to the frontend.
- Catalog filters use repeated `label` query parameters with AND semantics; absent or empty labels return all recipes.
- Draft/published state is removed; the catalog is a single public “Recetas” area.

## Non-goals
- No label administration area independent from recipe forms.
- No OR filtering mode or combination with text/ingredient/author filters.
- No label history or retained identifiers after deletion.
