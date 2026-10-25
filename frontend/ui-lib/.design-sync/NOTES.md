# Design-sync notes (@comemos/ui)

- Config home is `frontend/ui-lib/`; run every command from there. Build the library first with `cd .. && npm run build:ui` (also `config.buildCmd`).
- `ui-lib/` has no `node_modules`: pass `--node-modules ../node_modules` (react resolves from `frontend/`).
- Entry is `./dist/index.js`; the stylesheet is `dist/ui.css` (this Vite version ignores `cssFileName`).
- Render check uses the system Chrome: `export DS_CHROMIUM_PATH=/usr/bin/google-chrome`. The `playwright` npm package lives only in the gitignored `.ds-sync/`; no Chromium was downloaded.
- `dtsPropsFor` for `Button` and `Panel` is required: the extractor dropped `disabled`, `type`, `onClick`, `aria-label` and `aria-labelledby` because the props come from `Omit<HTML*Attributes, "className">`. Keep both in sync with `src/ui/Button.tsx` and `src/ui/Panel.tsx`.
- The library CSS must set `font-family` and `box-sizing` itself (the app gets them from `App.css`'s `:root` and `* {}`). Without them previews render in serif and inputs overflow `Panel`. Text a preview writes outside a component needs `fontFamily: "var(--font-family-base)"`.
- `tokens/` and `fonts/` are empty by design: tokens ship inside `_ds_bundle.css`, and the font stack is system/Inter with no `@font-face`.
- Preview copy is Spanish, matching the product UI.

## Known render warns

- None after authoring; `Field` showed `[RENDER_THIN]` only while it was an unauthored floor card.

## Re-sync risks

- `dtsPropsFor` bodies are hand-written and will go stale if `Button`/`Panel` props change.
- `conventions.md` hard-codes the token names and the `#f1f5f9` page background; re-validate it on each sync (it is checked, never rewritten).
- The app does not consume `@comemos/ui` yet, and `src/ui/ui.css` duplicates rules from `App.css`. When `App.tsx` adopts the components, the sync should be re-run.
- Inter is named in `--font-family-base` but is never shipped; designs render in the system sans-serif fallback unless the host loads Inter.
- Verification used one machine's Google Chrome; screenshots were graded by eye on the absolute rubric.
