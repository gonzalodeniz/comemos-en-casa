# Proposal: recipe catalogue foundation

**Change:** `recetas-publicas-privadas`  
**Product source:** approved GitHub issue #5, “Feature: Gestión y organización de recetas”
**Status:** proposal  
**Basis:** `openspec/changes/recetas-publicas-privadas/exploration.md`

## Intent

Establish the smallest independent recipe-catalogue foundation that owns the canonical PostgreSQL `recipes(id)` contract required by meal-calendar integration. This slice provides stable recipe identity and the minimum public recipe data boundary needed for catalogue reads, while deliberately leaving the complete public recipe product for later changes. The product has no private recipes or private-recipe visibility model.

## Problem

The meal calendar can store a nullable recipe identifier, but the repository has no catalogue-owned `recipes` table or recipe model. Adding a foreign key or implementing current-title, image, search, and detail reads without that owner would force the calendar change to invent recipe storage and make future work for issue #5 harder to evolve.

This foundation is needed now because calendar PR1 is merged and calendar PR2 is blocked until a catalogue owner defines `recipes(id)`. The foundation must unblock that integration without expanding into the full recipe-management experience.

## Goals

1. Make the recipe catalogue the single owner of a stable UUID `recipes(id)` identity in PostgreSQL.
2. Define the minimum public recipe data contract needed for calendar search, detail, current title, and current image reads.
3. Keep recipe presentation data in the catalogue so consumers read current values instead of snapshotting them.
4. Establish validation and normalization rules for the foundation fields at a Python domain/schema boundary.
5. Preserve an additive path to the complete public recipe experience approved in issue #5, including authenticated management, collections, and favorites.
6. Document migration order and ownership so calendar integration can add its foreign key without coupling catalogue creation to calendar delivery.

## Scope

### Included in this foundation

- An expand-only, versioned PostgreSQL migration that creates the canonical `recipes` relation with:
  - a stable UUID primary key named `id`;
  - the minimum fields required to represent a public recipe for title search and detail reads;
  - catalogue-owned current title and image data used by calendar reads.
- A small Python domain/schema boundary that validates and normalizes only those foundation fields.
- A database access dependency and repository/catalogue adapter only if the design phase first establishes a compatible application boundary; the proposal does not introduce a framework merely to expose the table.
- Focused verification of migration shape, UUID identity, foundation-field validation, public title/image/detail reads where an adapter exists, and deletion semantics required by the calendar tombstone contract.
- Documentation that identifies the catalogue as owner of `recipes` and defines migration ordering for downstream consumers.

The specification and design may choose exact column names, nullability, normalization limits, and storage representation for image and detail content. Those choices must remain limited to the stated public-read use cases and must not silently introduce full recipe management.

### Affected areas

- `backend/migrations/versions/` for the catalogue-owned creation of `recipes`.
- `backend/migrations/README.md` or equivalent migration documentation for ownership and ordering.
- A bounded backend recipe domain/schema module and its focused pytest coverage.
- A repository/catalogue adapter and PostgreSQL dependency only if justified by the design.
- Future calendar integration that consumes `recipes(id)`; the existing `calendario-de-comidas` change is not modified by this proposal.

## Non-goals

- Full recipe create, edit, delete, draft, publishing, moderation, or administration workflows.
- Recipe frontend screens, catalogue browsing UI, editor UI, upload flows, or complete recipe-detail UX.
- Collections, favorites, family libraries, sharing workflows, shopping-list integration, nutrition, ingredients, portions, steps, tags, or other rich recipe features beyond the minimum foundation contract.
- Recipe-private visibility, household sharing, or any private-recipe authorization model.
- Authentication or Gmail login; issue #6 owns that capability.
- Calendar endpoints, calendar repositories, calendar UI, or changes to the existing `calendario-de-comidas` OpenSpec artifacts.
- Adding the calendar foreign key in the catalogue migration or otherwise making this migration depend on calendar tables.
- Selecting a web framework or building an API solely for this slice.

## Constraints

### Product constraints

- The first slice supports only the public catalogue foundation. It must not claim that the complete recipe-management product is delivered.
- Public recipe records must have stable identities suitable for references from other product areas.
- Title and image remain catalogue-owned current values. Calendar assignments must not duplicate them as snapshots.
- The data model must remain additively extensible for later ownership, household, visibility, collections, and richer recipe content.
- The slice must remain independently reviewable within the 400 changed-line budget; if later design forecasts otherwise, delivery must pause under `ask-on-risk` rather than silently broaden or chain the work.

### Technical constraints

- PostgreSQL is the persistence system and Python is the backend language.
- Migrations are versioned, lexical-order, expand-only changes; this slice must not require a destructive downgrade.
- `recipes.id` is the canonical UUID primary key contract.
- The catalogue must not depend on `meal_assignments` or any calendar migration to exist.
- Recipe deletion must be compatible with the calendar's tombstone behavior: after integration, deleting a recipe must allow `meal_assignments.recipe_id` to become `NULL` through `ON DELETE SET NULL` rather than deleting the assignment.
- No database driver, framework, or repository abstraction may be selected without design-phase justification based on an established application boundary.
- Future implementation uses proportionate verification with the repository's pytest runner when applicable; this proposal itself adds no source code.

## Dependency on issue #6

Issue #6 remains a prerequisite for authenticated recipe management, but not for the public catalogue foundation. This change must not infer users, ownership, or permissions; any later management API must use the authentication contract without introducing private recipe visibility.

## Migration ownership and ordering

Ownership is intentionally split by bounded context:

1. This catalogue change owns the migration that creates `recipes`, including its UUID `id` and foundation fields.
2. The catalogue migration is independent of calendar tables and can be applied before calendar integration.
3. After this foundation is implemented and merged, the calendar PR2 work owns a later migration that alters `meal_assignments.recipe_id` to reference `recipes(id) ON DELETE SET NULL`.
4. That calendar integration migration must run only after the catalogue migration and must not recreate or redefine `recipes`.
5. Future recipe-schema expansions remain catalogue-owned; future changes to calendar references remain calendar-owned.

## Explicit follow-up boundary

A separate follow-up to issue #5 will deliver the complete public recipe product: recipe-management APIs and UI, richer recipe content, collections/favorites, and publication workflows. All recipes remain publicly readable; authentication controls who may manage recipes, not whether a recipe is private.

Until those follow-ups are specified and delivered:

- only the public foundation is considered available;
- no full recipe-management guarantee is made;
- all catalogue records are public by product decision;
- no collections or full recipe UI are included;
- no temporary access-control scheme may be added to this slice;
- calendar integration may rely only on stable identity and the explicitly specified public-read contract.

## Risks and tradeoffs

- **Under-modeling:** A deliberately small schema may require additive migrations when richer recipe behavior is designed. This is accepted to avoid guessing at issue #5's later UI and domain rules.
- **Premature infrastructure:** Adding a driver, framework, or repository before an application boundary exists could create unnecessary architecture. Design must omit those pieces unless they are required for a testable boundary.
- **Authorization leakage:** Modeling recipe-private visibility would create a product capability that is explicitly out of scope. This slice therefore keeps the catalogue public and leaves authenticated management to a later change.
- **Consumer coupling:** Calendar code could couple to table details beyond the supported contract. Specifications and design must keep the consumer boundary limited to stable identity and current public recipe reads.
- **Migration ordering:** Applying the calendar foreign key before `recipes` exists will fail. Ownership and ordering documentation are mandatory.
- **Deletion mismatch:** A restrictive or cascading foreign key would violate the calendar tombstone behavior. The later calendar-owned constraint must use `ON DELETE SET NULL`.

## Acceptance direction

The specification and design phases must turn at least the following outcomes into verifiable scenarios:

1. Applying catalogue migrations to an empty supported PostgreSQL database creates one canonical `recipes` table whose `id` is a UUID primary key.
2. The migration is expand-only, does not require calendar tables, and can be applied before the calendar integration migration.
3. The foundation domain/schema boundary accepts valid minimum public recipe data and rejects or normalizes invalid title, image, and detail values according to explicitly specified rules.
4. A public recipe can be represented with the current title and image/detail data required by calendar search and detail consumers, without storing presentation snapshots in `meal_assignments`.
5. Where the design includes a catalogue adapter, public title search and identity-based detail reads return only the foundation contract and reflect updated title/image values.
6. Recipe identifiers remain stable across ordinary catalogue reads and updates.
7. Migration documentation identifies this change as owner of `recipes` and the calendar integration as owner of the later `meal_assignments.recipe_id` foreign key.
8. The later calendar-owned foreign key can target `recipes(id)` with `ON DELETE SET NULL`, preserving an assignment as a tombstone when its recipe is deleted.
9. No authenticated recipe-management behavior, collections, rich recipe management, or recipe UI is required for this foundation to pass; private recipe visibility is not a product requirement.
10. Focused pytest coverage verifies each implemented foundation behavior without requiring implementation of calendar PR2.

## Success criteria

- Calendar PR2 has a concrete, catalogue-owned `recipes(id)` target and no longer needs to invent recipe storage.
- The catalogue migration can be applied independently and before the calendar integration constraint.
- The supported public-read boundary supplies stable identity and current title/image/detail values needed by calendar consumers.
- No calendar source or existing calendar OpenSpec artifact is changed as part of this foundation.
- No authenticated management, collection, or full recipe-UI behavior is represented as complete; private recipe visibility is explicitly excluded from the product.
- The planned implementation remains within the 400 changed-line review budget or explicitly pauses for a delivery decision under `ask-on-risk`.

## Rollback and recovery

Before downstream foreign keys or production data depend on the catalogue, rollback is performed by reverting the application deployment and, only in a disposable environment, removing the newly created catalogue objects through an explicitly reviewed operator action. The committed migration remains expand-only and does not include a destructive automatic downgrade.

After recipes or calendar references exist, operational rollback must leave the `recipes` table and its data in place while disabling or reverting catalogue application behavior. The later calendar foreign key must not be removed or changed as part of rolling back this feature without a separate migration plan. Forward-fix additive migrations are preferred for schema defects.

## Next phase

Write focused specifications for recipe identity, minimum public recipe fields, catalogue reads, migration ordering, and calendar-compatible deletion semantics. The subsequent design must decide whether a repository adapter and PostgreSQL driver are necessary, document tradeoffs, and forecast implementation size without expanding into the deferred public recipe product.
