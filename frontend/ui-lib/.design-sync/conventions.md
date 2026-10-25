# Comemos en casa UI conventions

Small presentational library (`window.ComemosUI`): `Button`, `Field`, `Message`, `Panel`. There is no provider and no theme wrapper: components work as soon as `styles.css` is loaded. Without `styles.css` they render as unstyled browser defaults.

## Styling idiom: CSS custom properties, no utility classes

Components are styled by their own `ui-*` classes (`ui-button`, `ui-field`, `ui-panel`, `ui-message`). Never write those classes yourself and never invent new `ui-*` names: use the components and their props. For your own layout glue (flex/grid wrappers, spacing, headings, plain text) use inline styles that reference the tokens below with `var(--*)`.

Plain text you write outside a component is NOT styled for you. Set `fontFamily: "var(--font-family-base)"` on your outer wrapper, or text falls back to the browser serif.

Tokens (defined in `_ds_bundle.css`, which `styles.css` imports):
- Font: `--font-family-base`
- Text: `--color-text`, `--color-text-muted`
- Surfaces and borders: `--color-surface`, `--color-border`, `--color-border-subtle`
- Brand green: `--color-primary`, `--color-primary-strong`, `--color-focus-ring`
- Secondary / danger: `--color-secondary-text`, `--color-secondary-bg`, `--color-danger`
- Feedback: `--color-error-text`, `--color-error-bg`, `--color-success-text`, `--color-success-bg`
- Shape: `--radius-control`, `--radius-button`, `--radius-message`, `--radius-panel`, `--shadow-panel`

Page background in the product is `#f1f5f9` (slate); `Panel` is white with a soft shadow, so place panels on that background.

## Component rules

- `Button`: `variant` is `primary` (default), `secondary`, `danger` or `link`. `type` defaults to `button`; pass `type="submit"` for the form's main action. Icon-only buttons need `aria-label`.
- `Field`: wraps ONE `input` or `select` and renders the label above it. Pass `label` and optional `hint`; do not add your own `<label>`.
- `Message`: `tone="error"` (announced as alert) or `tone="success"` (announced as status). Children are the text.
- `Panel`: a white card. `narrow` makes a centered 460px column for auth forms.
- Product copy is Spanish; keep UI text in Spanish.

## Where the truth lives

Read `styles.css` and `_ds_bundle.css` before styling, and each component's `<Name>.d.ts` (props) and `<Name>.prompt.md` (usage).

## Example: sign-in card

```jsx
const { Panel, Field, Message, Button } = window.ComemosUI;

<div style={{ padding: 16, background: "#f1f5f9", fontFamily: "var(--font-family-base)" }}>
  <Panel narrow>
    <h2 style={{ marginTop: 0 }}>Iniciar sesión</h2>
    <form>
      <Field label="Correo electrónico"><input type="email" /></Field>
      <Field label="Contraseña"><input type="password" /></Field>
      <Message tone="error">Credenciales incorrectas.</Message>
      <Button type="submit" style={{ width: "100%", marginTop: 12 }}>Entrar</Button>
    </form>
  </Panel>
</div>
```
