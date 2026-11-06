// @vitest-environment jsdom
// Comprueba la incorporación de recetas a la lista de la compra.
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import Recipes from "./Recipes";

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

it("añade la receta seleccionada a la lista de la compra", async () => {
  let terminar!: (respuesta: Response) => void;
  const peticion = vi.fn((entrada: RequestInfo | URL, _opciones?: RequestInit) => {
    const ruta = String(entrada);
    if (ruta.endsWith("/food-labels")) return Promise.resolve(new Response(JSON.stringify({ labels: [] })));
    if (ruta.endsWith("/recipes")) return Promise.resolve(new Response(JSON.stringify({ recipes: [
      { id: "receta-1", title: "Sopa", image_url: null, ingredients: "agua", preparation: null, foods: [] },
    ] })));
    if (ruta.endsWith("/recipes/receta-1/shopping-section")) return new Promise<Response>((resolve) => { terminar = resolve; });
    return Promise.resolve(new Response("{}", { status: 404 }));
  });
  vi.stubGlobal("fetch", peticion);
  const usuario = userEvent.setup();
  render(<Recipes csrfToken="token-csrf" onSessionExpired={vi.fn()} />);
  await usuario.click(await screen.findByRole("button", { name: "Sopa" }));
  await usuario.click(screen.getByRole("button", { name: "Añadir a la lista de compra" }));
  await waitFor(() => expect(peticion).toHaveBeenCalledWith(
    expect.stringMatching(/\/recipes\/receta-1\/shopping-section$/),
    expect.objectContaining({ method: "POST", headers: expect.any(Headers) }),
  ));
  const boton = screen.getByRole("button", { name: "Añadiendo…" });
  expect((boton as HTMLButtonElement).disabled).toBe(true);
  terminar(new Response(JSON.stringify({ id: "seccion-1", name: "Sopa" }), { status: 201 }));
  expect((await screen.findByRole("status")).textContent).toContain("Receta añadida a la lista de compra.");
  const opciones = peticion.mock.calls.find(([ruta]) => String(ruta).endsWith("/shopping-section"))?.[1] as RequestInit;
  expect((opciones.headers as Headers).get("X-CSRF-Token")).toBe("token-csrf");
});
