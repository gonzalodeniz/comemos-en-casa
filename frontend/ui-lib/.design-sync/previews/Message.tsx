import { Message } from "@comemos/ui";

export const Error = () => (
  <div style={{ padding: 16 }}>
    <Message tone="error">No se pudo guardar el plan semanal. Inténtalo de nuevo.</Message>
  </div>
);

export const Success = () => (
  <div style={{ padding: 16 }}>
    <Message tone="success">El plan semanal se guardó correctamente.</Message>
  </div>
);

export const Stacked = () => (
  <div style={{ display: "grid", gap: 8, padding: 16 }}>
    <Message tone="success">Usuario actualizado.</Message>
    <Message tone="error">El enlace no incluye un token válido.</Message>
  </div>
);
