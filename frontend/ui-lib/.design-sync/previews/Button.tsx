import { Button } from "@comemos/ui";

export const Variants = () => (
  <div style={{ display: "flex", flexWrap: "wrap", gap: 12, padding: 16 }}>
    <Button>Guardar menú</Button>
    <Button variant="secondary">Cancelar</Button>
    <Button variant="danger">Eliminar</Button>
    <Button variant="link">¿Olvidaste tu contraseña?</Button>
  </div>
);

export const Disabled = () => (
  <div style={{ display: "flex", flexWrap: "wrap", gap: 12, padding: 16 }}>
    <Button disabled>Guardando…</Button>
    <Button variant="secondary" disabled>Cancelar</Button>
    <Button variant="danger" disabled>Eliminar</Button>
  </div>
);

export const CalendarNavigation = () => (
  <div style={{ display: "flex", alignItems: "center", gap: 8, padding: 16, fontFamily: "var(--font-family-base)" }}>
    <Button variant="secondary" aria-label="Semana anterior">←</Button>
    <strong style={{ flex: 1, textAlign: "center" }}>Semana del 26 oct</strong>
    <Button variant="secondary" aria-label="Semana siguiente">→</Button>
    <Button variant="secondary">Hoy</Button>
  </div>
);
