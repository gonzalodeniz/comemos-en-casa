# Fix free-text meal creation in calendar

## Goal
Allow users to add a free-text meal such as `lentejas` from the calendar in browser contexts where `crypto.randomUUID()` is unavailable.

## Tasks
- [x] Add a browser-compatible assignment ID generator with a UUID fallback.
- [x] Add a regression test covering free-text creation without `crypto.randomUUID()`.
- [x] Run focused frontend tests, typecheck, and diff checks.

## Evidence
- `frontend/src/App.tsx` now uses `generateAssignmentId()` with `randomUUID`, `getRandomValues`, and a final fallback.
- `frontend/src/App.test.tsx` covers saving `lentejas` when `crypto.randomUUID` is unavailable.
- Independent verification passed: 10 focused tests, frontend typecheck, and diff checks.
- Native review was not started because the repository review switch is disabled (`rdd_disabled`).
