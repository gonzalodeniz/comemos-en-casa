# Calendar visual refresh

- [x] Align the shared header with the calendar prototype: search on the right, no calendar/recipes top navigation on calendar routes, and prototype-like branding/session affordance.
- [x] Refresh the calendar sidebar navigation and planning illustration/message to match `prototipos/calendario-01.png`.
- [x] Refresh calendar surface, controls, grid, and footer styling to match the prototype while preserving responsive behavior.
- [x] Update regression tests and run frontend verification.

## Evidence

- `npm --prefix frontend run test -- src/App.test.tsx` — 9 tests passed.
- `npm --prefix frontend run typecheck` — passed.
- `git diff --check -- frontend/src/App.tsx frontend/src/App.test.tsx frontend/src/styles.css` — passed.
- No commit created; delivery remains a user decision.
