import { Field } from "@comemos/ui";

export const WithInput = () => (
  <div style={{ maxWidth: 360, padding: 16 }}>
    <Field label="Correo electrónico">
      <input type="email" placeholder="familia@ejemplo.com" />
    </Field>
  </div>
);

export const WithHint = () => (
  <div style={{ maxWidth: 360, padding: 16 }}>
    <Field label="Contraseña" hint="Mínimo 12 caracteres.">
      <input type="password" defaultValue="contraseña-segura" />
    </Field>
  </div>
);

export const WithSelect = () => (
  <div style={{ maxWidth: 360, padding: 16 }}>
    <Field label="Comida">
      <select defaultValue="dinner">
        <option value="lunch">Almuerzo</option>
        <option value="dinner">Cena</option>
      </select>
    </Field>
  </div>
);
