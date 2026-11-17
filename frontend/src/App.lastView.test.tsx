// @vitest-environment jsdom
// Comprueba la recuperación de la última vista desde la sesión autenticada.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";
import { apiRequest } from "./api";

const estado = vi.hoisted(() => ({ vista: "backups" as string | null }));
vi.mock("./api", () => ({
  ApiError: class extends Error {},
  apiRequest: vi.fn(async (path: string, options?: { body?: { vista: string } }) => {
    if (path === "/auth/session") return { user: { id: "1", name: "Persona", email: "p@example.test" }, csrf_token: "token", ultima_vista: estado.vista };
    if (path === "/users") return { users: [] };
    if (path === "/auth/last-view") { estado.vista = options?.body?.vista ?? null; return null; }
    throw new Error(`Unexpected request: ${path}`);
  }),
}));
vi.mock("./AppWorkspace", () => ({ default: ({ view, onViewChange }: { view: string; onViewChange: (view: string) => void }) => <div>Vista activa: {view}<button onClick={() => onViewChange("recipes")}>Recetas</button></div> }));

afterEach(() => { cleanup(); sessionStorage.clear(); estado.vista = "backups"; });

it("restaura la vista de la cuenta al recuperar la sesión", async () => {
  render(<App />);
  expect(await screen.findByText(/Vista activa: backups/)).toBeTruthy();
});

// Comprueba que una aplicación recién abierta recibe la última vista guardada.
it("restaura la vista seleccionada al abrir otra sesión", async () => {
  const primera = render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Recetas" }));
  await waitFor(() => expect(estado.vista).toBe("recipes"));
  primera.unmount();
  sessionStorage.clear();
  render(<App />);
  expect(await screen.findByText(/Vista activa: recipes/)).toBeTruthy();
});

// Comprueba que navegar guarda la vista en la cuenta autenticada.
it("guarda la vista seleccionada en el servidor", async () => {
  render(<App />);
  fireEvent.click(await screen.findByRole("button", { name: "Recetas" }));
  await waitFor(() => expect(apiRequest).toHaveBeenCalledWith("/auth/last-view", { method: "PUT", csrfToken: "token", body: { vista: "recipes" } }));
});

// Comprueba el destino inicial cuando no hay una vista válida para la cuenta.
it.each([null, "vista-desconocida"])("usa planificación si la vista guardada es %s", async (vista) => {
  estado.vista = vista;
  sessionStorage.setItem("comemos-en-casa:workspace-view", "backups");
  render(<App />);
  expect(await screen.findByText(/Vista activa: meal-planning/)).toBeTruthy();
});
