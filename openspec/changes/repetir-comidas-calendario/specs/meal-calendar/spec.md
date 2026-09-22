# Meal Calendar Recurrence Specification

## Purpose

Define the acceptance contract for indefinite recurrence of free-text meals in the shared calendar. The calendar stores one recurrence rule per series and expands its occurrences only when a weekly calendar range is read, while preserving existing ordinary and recipe assignments.

## Requirements

### Requirement: Persist one shared recurrence rule per series

The system MUST persist exactly one recurrence rule for each recurring meal series in the shared calendar (`calendar_key = "shared"`) and MUST NOT persist generated occurrences as independent assignments. A rule MUST contain a stable series identity, its first occurrence date, its meal slot, normalized free text, and an interval of 1, 2, 3, or 4 weeks. A rule MUST have no end date and MUST represent recurrence as `Cada semana`, `Cada 2 semanas`, `Cada 3 semanas`, or `Cada 4 semanas`; `No repetir` MUST represent an ordinary assignment rather than a recurrence rule.

#### Scenario: Create an indefinite weekly series

- GIVEN the shared calendar has no series with the requested series identity
- WHEN a valid free-text meal is created for `2026-09-16`, slot `lunch`, with frequency `Cada semana`
- THEN the system persists one rule with first occurrence `2026-09-16`, interval `1`, and no end date
- AND the system does not create an independent persisted assignment for any later occurrence

#### Scenario: Reject a recurrence interval outside the supported options

- GIVEN a create or update request contains an interval other than `No repetir`, `1`, `2`, `3`, or `4` weeks
- WHEN the request is validated
- THEN the system rejects it as a validation error
- AND the existing calendar data remains unchanged

### Requirement: Keep recurrence free-text-only

The system MUST allow recurrence only for meals whose type is `free_text`, using the same free-text normalization and validity rules as ordinary free-text assignments. A recurrence request MUST NOT create, select, associate, or modify a recipe. Recipe assignment flows MUST remain separate from recurrence flows.

#### Scenario: Create a recurring free-text meal

- GIVEN a valid free-text value and a valid lunch or dinner slot
- WHEN the meal is created with any supported recurring frequency
- THEN the persisted rule and every expanded occurrence have type `free_text`
- AND the response exposes the normalized meal text

#### Scenario: Reject recurrence on a recipe assignment without changing the recipe flow

- GIVEN an existing or requested meal has type `recipe`
- WHEN a request attempts to attach a recurrence rule to it
- THEN the system rejects the recurrence request as a validation error
- AND it does not create a rule, change the recipe assignment, or add recipe-selection behavior

### Requirement: Derive a stable weekday and interval from the first occurrence

The first occurrence date MUST be included in the series and MUST establish the series weekday. For interval `n`, an occurrence MUST be scheduled exactly when its local calendar date is the current initial occurrence date plus `7 × n × k` days for an integer `k >= 0`. Occurrences MUST therefore retain the current initial-date weekday and MUST NOT drift because of month boundaries, daylight-saving transitions, or the number of days in a month. A confirmed initial-date edit MUST replace the anchor used for all subsequent expansion, including historical and future reads.

#### Scenario: Preserve the weekday across a month boundary

- GIVEN a series starts on Wednesday `2026-09-30` with interval `2`
- WHEN the calendar is read for the week beginning Monday `2026-10-12`
- THEN the series includes Wednesday `2026-10-14`
- AND it does not include Tuesday `2026-10-13` or Thursday `2026-10-15`

#### Scenario: Apply every-four-weeks spacing

- GIVEN a series starts on Monday `2026-01-05` with interval `4`
- WHEN dates are evaluated after creation
- THEN occurrences are `2026-01-05`, `2026-02-02`, `2026-03-02`, and so on
- AND dates on the same weekday at one, two, or three weeks after an occurrence are absent from this series

### Requirement: Expand only the requested inclusive calendar week

A weekly read MUST expand candidate rules against the existing Monday-to-Sunday calendar week. The returned range MUST be inclusive of both `weekStart` and `weekEnd`, and the expansion MUST include an occurrence exactly on either boundary when the recurrence formula matches it. Rules whose first occurrence is after `weekEnd` or whose next matching occurrence is after `weekEnd` MUST contribute no occurrence to that response. Generated occurrences MUST be limited to the requested seven-day range.

#### Scenario: Include the initial date at the start boundary

- GIVEN a weekly read requests Monday `2026-09-14` through Sunday `2026-09-20`
- AND a weekly series has first occurrence Monday `2026-09-14`
- WHEN the week is read
- THEN the response includes the occurrence on `2026-09-14`

#### Scenario: Include the final date at the end boundary and exclude the next week

- GIVEN a weekly read requests Monday `2026-09-14` through Sunday `2026-09-20`
- AND a weekly series has first occurrence Sunday `2026-09-20` with interval `1`
- WHEN the week is read
- THEN the response includes the occurrence on `2026-09-20`
- AND it excludes the next occurrence on `2026-09-27`

#### Scenario: Do not leak a later occurrence into an adjacent week

- GIVEN a series starts Wednesday `2026-09-16` with interval `2`
- WHEN the week `2026-09-21` through `2026-09-27` is read
- THEN the response contains no occurrence from that series
- AND when the week `2026-09-28` through `2026-10-04` is read, it contains the occurrence on Wednesday `2026-09-30`

### Requirement: Expose stable occurrence and series identity

Every recurring occurrence in a weekly response MUST be distinguishable from a persisted ordinary assignment and MUST expose a stable series identity that is the same for every occurrence of that series. The occurrence identity MUST be stable across repeated reads and MUST be sufficient to address the series-level edit and delete operations without addressing a nonexistent persisted occurrence. The occurrence identity is the tuple `(series identity, occurrence date)`; if the response also exposes a single `id`, that `id` MUST remain deterministic for that tuple and MUST NOT be presented as an ordinary assignment row identity. Ordinary assignments MUST retain their existing assignment identity.

#### Scenario: Identify two occurrences from one series

- GIVEN a weekly series has identity `S` and occurrences on `2026-09-16` and `2026-09-23`
- WHEN both dates are returned in separate weekly reads
- THEN both responses expose series identity `S`
- AND their occurrence identities are respectively `(S, 2026-09-16)` and `(S, 2026-09-23)`
- AND a client can use either occurrence to target the same series mutation

#### Scenario: Preserve identity across repeated reads

- GIVEN the same unchanged series is read twice for the same week
- WHEN both responses are compared
- THEN the recurring occurrence has the same series and occurrence identity in both responses
- AND the read does not create a new persisted identity

### Requirement: Create, update, and delete series atomically at series scope

Creating a recurring meal MUST create one series rule and return its stable series identity. Updating a recurring meal from any occurrence MUST update the single rule and therefore affect all past and future reads of the series; it MUST NOT update only the displayed occurrence. Deleting a recurring meal from any occurrence MUST remove the rule and therefore remove all past and future generated occurrences. No individual occurrence edit or delete operation MAY be offered or accepted.

#### Scenario: Edit interval and text from a displayed occurrence

- GIVEN a series starts Wednesday `2026-09-16` with interval `1` and text `Sopa`
- WHEN a client edits the occurrence shown on `2026-09-30` to interval `2` and text `Crema de verduras`
- THEN the system updates the one series rule identified by the response identity
- AND subsequent reads show `Crema de verduras` only on dates matching the updated interval and weekday
- AND no occurrence-only override is persisted

#### Scenario: Delete a series from a later occurrence

- GIVEN a recurring series has already produced occurrences in past and future calendar weeks
- WHEN the client deletes the series using the identity of one returned occurrence
- THEN the series rule is deleted
- AND reads for both past and future weeks return none of that series
- AND ordinary assignments in those weeks remain unchanged

#### Scenario: Reject an occurrence-only mutation

- GIVEN a client submits a mutation that identifies only an occurrence date without a valid series identity
- WHEN the mutation is processed
- THEN the system rejects it as an invalid target
- AND it does not create an exception, override, or independent occurrence assignment

### Requirement: Convert an ordinary assignment into a recurrence on explicit edit

When a user edits an ordinary free-text assignment and selects one of the recurring frequencies, the system MUST convert that assignment into exactly one recurrence rule using the edited meal data. The original ordinary assignment MUST be removed as part of the same successful transition, and the conversion MUST NOT leave both an ordinary assignment and a recurring series for the same edit.

#### Scenario: Convert a one-off free-text meal to a weekly series

- GIVEN an ordinary free-text assignment exists on `2026-09-16` lunch with text `Sopa`
- WHEN the user edits that assignment and selects `Cada semana`
- THEN the system creates one recurrence rule whose initial date is `2026-09-16`, slot is `lunch`, interval is `1`, and text is `Sopa`
- AND the original ordinary assignment is removed
- AND the weekly response contains the converted series occurrence rather than two entries for `2026-09-16`

#### Scenario: Do not partially convert an ordinary assignment

- GIVEN an ordinary free-text assignment is being converted to a recurrence
- WHEN validation or persistence of the recurrence fails
- THEN the original ordinary assignment remains unchanged
- AND no partial recurrence rule is visible

### Requirement: Delete a recurrence when editing it to No repetir

When a user edits an existing recurrence and selects `No repetir`, the system MUST require explicit user confirmation before applying the change and MUST warn that the recurrence rule and all of its generated occurrences will be deleted. After confirmation, the system MUST delete the recurrence rule entirely; it MUST NOT retain or create a one-off meal at the initial date or at the edited occurrence date. Without confirmation, the rule MUST remain unchanged.

#### Scenario: Confirmed No repetir deletes the whole recurrence

- GIVEN a recurrence rule has occurrences in past and future weeks
- WHEN the user edits any occurrence, selects `No repetir`, receives the deletion warning, and confirms
- THEN the system deletes the recurrence rule
- AND no one-off assignment is retained at the initial date or occurrence date
- AND past and future weekly reads contain none of that series

#### Scenario: Unconfirmed No repetir leaves the series intact

- GIVEN a recurrence rule is being edited
- WHEN the user selects `No repetir` but declines or does not provide the required confirmation
- THEN the system does not delete the rule
- AND subsequent reads continue to show the existing occurrences

### Requirement: Confirm initial-date changes and preserve the series slot

The initial occurrence date of an existing recurrence MUST be editable. Changing it MUST require explicit user confirmation and a warning that the new date changes the weekday anchor for the entire series, including historical and future reads. After confirmation, the system MUST update the same recurrence rule, use the new date as its first occurrence, preserve the selected 1-, 2-, 3-, or 4-week interval, and remain indefinite. The meal slot MUST NOT be editable on an existing recurrence; a request attempting to change the slot MUST be rejected without changing the rule.

#### Scenario: Move a series to a new weekday anchor

- GIVEN a series starts Wednesday `2026-09-16` in `lunch` with interval `2`
- WHEN the user changes its initial date to Friday `2026-09-18`, receives the anchor-change warning, and confirms
- THEN the same series rule has initial date `2026-09-18`, slot `lunch`, interval `2`, and no end date
- AND its occurrences are recalculated on Fridays every two weeks from `2026-09-18`
- AND no occurrence remains anchored to Wednesday

#### Scenario: Do not apply an unconfirmed initial-date change

- GIVEN a series starts Wednesday `2026-09-16`
- WHEN a requested new initial date is not confirmed
- THEN the rule remains anchored to Wednesday `2026-09-16`
- AND its existing occurrences remain unchanged

#### Scenario: Reject a slot change on an existing series

- GIVEN a series exists in `lunch`
- WHEN an edit attempts to change its slot to `dinner`
- THEN the system rejects the edit as invalid
- AND the series remains in `lunch` with its prior date, interval, and text

### Requirement: Make writes validated and idempotent

A create request for a recurring series MUST have a stable request or series identity that can be reused for retries. Repeating an identical create MUST return the existing series representation without creating a second rule; reusing that identity with a different payload MUST fail with an idempotency conflict and MUST preserve the original rule. Repeating an update with the same target and payload MUST leave the rule in the same state. Repeating a delete for an already deleted series MUST not recreate data or produce a second deletion effect. Invalid dates, slots, free text, types, intervals, and incompatible recipe fields MUST be rejected before mutation.

#### Scenario: Retry an identical series create

- GIVEN a recurring create request has established series identity `S`
- WHEN the same request is submitted again after an uncertain response
- THEN the system returns the existing series representation for `S`
- AND the shared calendar contains exactly one rule for `S`

#### Scenario: Detect a conflicting retry

- GIVEN series identity `S` already represents a weekly `Sopa` series
- WHEN a create request reuses `S` with a different date, slot, text, or interval
- THEN the system returns an idempotency conflict
- AND the original series remains unchanged

#### Scenario: Retry series deletion

- GIVEN series `S` has been deleted
- WHEN a delete request for `S` is repeated
- THEN the operation remains successful and idempotent
- AND no occurrence or replacement ordinary assignment is created

### Requirement: Preserve coexistence and deterministic ordering

The weekly response MUST combine all ordinary assignments and all applicable recurring occurrences for the shared calendar. The system MUST preserve multiple meals and multiple series in the same date and slot; it MUST NOT replace, deduplicate, reject, warn about, or require confirmation for such coexistence. The combined response MUST be ordered deterministically by date ascending, slot with `lunch` before `dinner`, normalized visible meal text using the calendar's existing text ordering, and a stable identity tie-breaker.

#### Scenario: Keep several rules and an ordinary meal in one slot

- GIVEN `2026-09-16` lunch contains an ordinary free-text assignment `Arroz`, a weekly series `Sopa`, and a two-week series `Fruta`
- WHEN the week containing `2026-09-16` is read
- THEN all three meals are present in the response
- AND none is replaced, hidden, rejected, or marked as a conflict
- AND their relative order is deterministic according to the stated ordering contract

#### Scenario: Keep same-text entries distinct

- GIVEN two different series produce `Sopa` in the same date and slot
- WHEN that date is read
- THEN both occurrences are returned with distinct series identities
- AND the stable identity tie-breaker produces the same order on repeated reads

### Requirement: Preserve existing ordinary and recipe assignment behavior

Existing non-recurring assignments MUST remain readable and writable through their current assignment behavior when the user does not explicitly select a recurrence transition. An explicit edit that selects a recurring frequency MUST follow the ordinary-to-series conversion requirement. Existing recipe assignments MUST continue to be returned as `kind = recipe` with their current recipe presentation, including the existing unavailable-recipe presentation when the referenced recipe is no longer available. Introducing recurrence MUST NOT convert, delete, or materialize recipe assignments, and MUST NOT add recipe creation or linkage to the calendar recurrence flow.

#### Scenario: Read a week containing a legacy recipe assignment and a recurrence

- GIVEN a week contains an existing recipe assignment and a recurring free-text occurrence in the same or another slot
- WHEN the week is read
- THEN both entries are returned
- AND the recipe entry retains `kind = recipe` and its existing recipe reference presentation
- AND the recurring entry has `kind = free_text` and no recipe linkage

#### Scenario: Keep an unavailable legacy recipe legible

- GIVEN an existing recipe assignment references a recipe that is no longer available
- WHEN the calendar is read after recurrence support is enabled
- THEN the assignment remains visible using the existing unavailable-recipe presentation
- AND no recurring rule or new recipe link is created for it

### Requirement: Keep the calendar shared across users

All recurrence reads and series mutations MUST address the existing shared calendar and MUST NOT introduce per-user or per-household ownership, visibility, or conflict semantics. Any user who can access the shared calendar MUST observe the same rule and generated occurrences.

#### Scenario: Observe one series through shared calendar access

- GIVEN one user creates a recurring free-text meal in the shared calendar
- WHEN another authorized user reads the matching week
- THEN the other user sees the same occurrence, series identity, text, date, and slot
- AND the second user does not receive a private copy or a conflict prompt

