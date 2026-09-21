# Open calendar assignments directly in the edit modal

## Goal
Remove the assignment ellipsis action menu so selecting a meal card opens the existing `Editar comida` modal directly. The meal name and its image or placeholder must both open the editor for recipe and free-text assignments. Keep deletion in the editor, including the existing confirmation and API contract.

## Tasks
- [x] Remove the assignment-card ellipsis trigger and action modal.
- [x] Make assignment names and images/placeholders open the edit modal directly for recipe and free-text meals.
- [x] Add `Eliminar` to the edit modal while preserving the existing confirmation and `deleteAssignment` call.
- [x] Update frontend regression tests for direct opening, update behavior, and deletion from the edit modal.
- [x] Adjust calendar assignment and modal styles without changing backend code.

## Non-goals
- Do not change backend APIs or assignment persistence.
- Do not alter recipe links, calendar navigation, or create-assignment behavior.

## Evidence
- `frontend/src/App.tsx` renders no ellipsis trigger or action menu; assignment names and image/placeholder controls open `Editar comida`, and its `Eliminar` button uses the existing `window.confirm` text and `deleteAssignment` API call.
- `frontend/src/styles.css` styles direct assignment-card controls and the existing edit modal.
- `frontend/src/App.test.tsx` covers direct name/image/placeholder opening, update payload preservation, confirmation cancellation, and delete payload/success behavior.
- `npm --prefix frontend test -- src/App.test.tsx` passed: 12 focused tests.
- `npm --prefix frontend run typecheck` passed.
