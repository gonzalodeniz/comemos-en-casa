import { Button, Field, Message, Panel } from "@comemos/ui";

export const Default = () => (
  <div style={{ padding: 16, background: "#f1f5f9" }}>
    <Panel>
      <h2 style={{ marginTop: 0 }}>Plan semanal</h2>
      <p>Organiza las comidas de la familia para toda la semana.</p>
    </Panel>
  </div>
);

export const NarrowSignIn = () => (
  <div style={{ padding: 16, background: "#f1f5f9" }}>
    <Panel narrow>
      <h2 style={{ marginTop: 0 }}>Iniciar sesión</h2>
      <form onSubmit={(event) => event.preventDefault()}>
        <Field label="Correo electrónico">
          <input type="email" placeholder="familia@ejemplo.com" />
        </Field>
        <Field label="Contraseña">
          <input type="password" defaultValue="contraseña" />
        </Field>
        <Message tone="error">Credenciales incorrectas.</Message>
        <Button type="submit" style={{ width: "100%", marginTop: 12 }}>Entrar</Button>
      </form>
    </Panel>
  </div>
);
