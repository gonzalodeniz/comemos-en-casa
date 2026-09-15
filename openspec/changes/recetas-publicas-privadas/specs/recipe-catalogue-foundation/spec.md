# Recipe Catalogue Foundation Specification

## Purpose

Define the catalogue-owned PostgreSQL identity and minimum public recipe data contract that meal-calendar consumers can reference without owning recipe storage.

## Requirements

### Requirement: Canonical Recipe Identity

The catalogue MUST own exactly one canonical PostgreSQL relation named `recipes`. Its `id` column MUST be the relation's UUID primary key and the only supported recipe-reference identity. The catalogue migration MUST create this relation without requiring any calendar relation to exist.

#### Scenario: Applying the catalogue migration to an empty database

- GIVEN an empty supported PostgreSQL database with no calendar tables
- WHEN the catalogue migrations are applied in lexical version order
- THEN a `recipes` relation exists with `id` as a UUID primary key and no calendar relation was required

### Requirement: Minimum Public Recipe Foundation Fields

Each recipe record MUST provide the public foundation data `title`, `image URL`, and `detail` in addition to its `id`. `title` MUST support catalogue title search; `image URL` MUST represent the recipe's current cover image; and `detail` MUST provide the text returned by an identity-based public detail read. These fields MUST be catalogue-owned and MAY be extended only additively by later catalogue changes.

#### Scenario: Representing a public recipe for calendar consumers

- GIVEN valid foundation values for a recipe title, image URL, and detail
- WHEN the recipe is stored in the catalogue
- THEN its UUID identity, title, image URL, and detail are available as the public foundation contract

### Requirement: Foundation Field Normalization and Validation

The foundation domain/schema boundary MUST normalize Unicode text to NFC before validation. It MUST trim leading and trailing whitespace from `title`, `image URL`, and `detail`; it MUST also collapse runs of internal whitespace in `title` to one space and normalize CRLF and CR line endings in `detail` to LF. A normalized title MUST contain from 1 through 200 Unicode code points, and a normalized detail MUST contain from 1 through 10,000 Unicode code points. An image URL MUST contain from 1 through 2,048 characters and be an absolute `http` or `https` URL. The boundary MUST reject input that fails these constraints and MUST expose only normalized accepted values.

#### Scenario: Normalizing valid foundation input

- GIVEN a title with surrounding and repeated whitespace, a whitespace-padded HTTPS image URL, and detail with CRLF line endings
- WHEN the values are submitted to the foundation boundary
- THEN the accepted title is NFC-normalized, trimmed, and space-collapsed, the image URL is trimmed, and the detail is NFC-normalized with LF line endings and no surrounding whitespace

#### Scenario: Rejecting invalid foundation input

- GIVEN a blank normalized title, a non-HTTP(S) or relative image URL, or a detail outside its allowed length
- WHEN the values are submitted to the foundation boundary
- THEN the recipe is rejected and no invalid foundation value is accepted

### Requirement: Current Public Catalogue Reads

The public catalogue read contract MUST support title search and identity-based detail reads. Title search MUST match normalized titles without case or accent distinctions. A detail read for an existing recipe MUST return exactly its current UUID identity, title, image URL, and detail foundation values. Consumers MUST read current title and image values from the catalogue and MUST NOT treat presentation snapshots stored in `meal_assignments` as part of this contract.

#### Scenario: Searching a title without case or accents

- GIVEN the catalogue contains a recipe currently titled `Tortilla Española`
- WHEN a consumer searches for `tortilla espanola`
- THEN that recipe is included in the public title-search results

#### Scenario: Reading current recipe presentation and detail

- GIVEN a recipe's title and image URL have changed after it was first referenced by a calendar assignment
- WHEN a consumer performs an identity-based public detail read
- THEN the result contains the recipe's current title, current image URL, and current detail from the catalogue rather than historical assignment snapshots

### Requirement: Stable Recipe Identifiers

A recipe's `id` MUST be assigned as a UUID when the recipe is created and MUST remain unchanged by ordinary updates to its foundation fields. All public title-search results and identity-based detail reads for that recipe MUST use the same `id`.

#### Scenario: Updating a recipe without changing its identity

- GIVEN a stored recipe with UUID `id`
- WHEN its valid title, image URL, or detail is updated
- THEN subsequent public reads return the same `id` with the updated current values

### Requirement: Migration Ownership and Ordering

The catalogue change MUST own the expand-only, versioned migration that creates `recipes` and its foundation fields, and its migration documentation MUST name the catalogue as that owner. The migration MUST be independently applicable before calendar integration and MUST NOT create, alter, or reference `meal_assignments`. A later calendar-owned migration MAY add the `meal_assignments.recipe_id` foreign key only after `recipes(id)` exists; it MUST NOT recreate or redefine `recipes`.

#### Scenario: Applying catalogue before calendar integration

- GIVEN the catalogue migration has not yet been applied
- WHEN an operator follows the documented migration order
- THEN the catalogue migration is applied before any calendar migration that references `recipes(id)`

#### Scenario: Catalogue migration remains calendar-independent

- GIVEN a database with no `meal_assignments` relation
- WHEN the catalogue migration is applied
- THEN it succeeds without creating, altering, or referencing `meal_assignments`

### Requirement: Calendar Tombstone Deletion Compatibility

The catalogue schema MUST permit a recipe to be deleted without defining a calendar foreign key itself. Once the calendar owner adds `meal_assignments.recipe_id REFERENCES recipes(id) ON DELETE SET NULL`, deleting a referenced recipe MUST preserve the meal assignment and set only its `recipe_id` to `NULL`; the catalogue foundation MUST NOT require cascading deletion of the assignment or restrict the recipe deletion.

#### Scenario: Deleting a recipe referenced by a later calendar foreign key

- GIVEN the catalogue's `recipes(id)` exists and the calendar owner has added `meal_assignments.recipe_id REFERENCES recipes(id) ON DELETE SET NULL`
- WHEN a referenced recipe is deleted
- THEN the recipe is removed, the meal assignment remains, and that assignment's `recipe_id` is `NULL`

### Requirement: Foundation Scope Boundaries

This foundation SHALL provide only the public recipe identity and read-data contract defined here. It SHALL NOT implement or claim authenticated recipe management, authorization, users, households, ownership, roles, permissions, collections, favorites, rich recipe content, publishing workflows, or any recipe frontend or full recipe-detail UI. The product SHALL NOT define or implement private recipe visibility. It SHALL NOT add calendar endpoints, calendar repositories, calendar UI, or the calendar-owned foreign-key migration.

#### Scenario: Evaluating the delivered foundation scope

- GIVEN only this foundation change is applied
- WHEN a consumer evaluates its supported capabilities
- THEN it can rely on stable public recipe identity and current title, image URL, and detail reads, but cannot rely on authenticated management or a full recipe-management or recipe-UI capability; private recipe visibility is not supported
