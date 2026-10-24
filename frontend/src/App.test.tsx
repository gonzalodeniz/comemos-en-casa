// Verifica la representación inicial de la aplicación.
// Comprueba que el encabezado y el estado de carga de sesión estén presentes en el marcado renderizado.

import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import App from "./App";

describe("App", () => {
  it("renders the application heading and session loading state", () => {
    const markup = renderToStaticMarkup(<App />);

    expect(markup).toContain("Comemos en casa");
    expect(markup).toContain("Comprobando la sesión");
  });
});
