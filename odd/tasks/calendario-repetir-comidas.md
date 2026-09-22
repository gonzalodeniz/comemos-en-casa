# Add recurring meal controls to calendar

## Goal
Allow users to repeat free-text meals every 1–4 weeks from the new-meal editor, using the recurrence API already implemented by the backend, and deploy the updated container.

## Tasks
- [x] Map existing frontend recurrence API contract and define editor state behavior.
- [x] Add recurrence controls, payload typing, and recurring occurrence presentation in the calendar UI.
- [x] Add deterministic frontend regression tests for recurrence selection and payloads.
- [x] Run frontend checks and deploy the rebuilt containers.
- [x] Verify the deployed bundle exposes the recurrence UI and service health.

## Non-goals
- Do not add recurrence support for recipe assignments; backend currently supports free-text meals only.
- Do not redesign recurrence series management beyond the create/edit/delete behavior needed for this flow.

## Evidence
- Frontend recurrence support added across `frontend/src/App.tsx`, `frontend/src/types.ts`, `frontend/src/api.ts`, `frontend/src/calendarReducer.ts`, and `frontend/src/styles.css`.
- `frontend/src/App.test.tsx` covers recurring creation payloads, series edit/delete flows, disabled series slot, and recipe exclusion.
- Verification passed: 15 focused frontend tests, frontend typecheck, frontend build, 121 backend tests, and `git diff --check`.
- Deployment completed with `make deploy`; frontend container rebuilt and restarted.
- Deployed verification passed: `/calendario` returned 200, `/health` returned 200, and the served bundle contains `recurrenceWeeks`, `Cada semana`, `Repetición`, and `series/`.
- Commit created: `22453dd feat(calendar): add recurring meal controls`.
