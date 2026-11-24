// @vitest-environment jsdom
// Comprueba el retorno desde recetas a las vistas que conservaron su estado.
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

vi.mock("./api", () => ({
  ApiError: class extends Error {},
  apiRequest: vi.fn(async (ruta: string) => ruta === "/auth/session" ? { user: { id: "1", name: "Persona", email: "p@example.test" }, csrf_token: "token", ultima_vista: "food-catalog" } : ruta === "/users" ? { users: [] } : null),
}));
vi.mock("./FoodCatalog", () => ({ default: ({ onOpenRecipes }: { onOpenRecipes: (id: string) => void }) => <section><input aria-label="Filtro de comidas" /><button onClick={() => onOpenRecipes("1")}>Abrir recetas de comida</button></section> }));
vi.mock("./MealPlanning", () => ({ default: ({ onOpenRecipes }: { onOpenRecipes: (id: string) => void }) => <section><input aria-label="Estado del plan" /><button onClick={() => onOpenRecipes("1")}>Abrir recetas del plan</button></section> }));
vi.mock("./Recipes", () => ({ default: ({ onBack }: { onBack?: () => void }) => <section><h1>Listado de recetas</h1>{onBack && <button onClick={onBack}>Volver al origen</button>}</section> }));

afterEach(() => { cleanup(); sessionStorage.clear(); });

// Verifica que el filtro sigue intacto y que el acceso directo no ofrece retorno.
it("recupera el filtro de Comidas y omite volver al entrar directamente", async () => {
  render(<App />);
  const filtro = await screen.findByRole("textbox", { name: "Filtro de comidas" });
  fireEvent.change(filtro, { target: { value: "arroz" } });
  fireEvent.click(screen.getByRole("button", { name: "Abrir recetas de comida" }));
  fireEvent.click(screen.getByRole("button", { name: "Volver al origen" }));
  expect((screen.getByRole("textbox", { name: "Filtro de comidas" }) as HTMLInputElement).value).toBe("arroz");
  fireEvent.click(within(screen.getByRole("navigation", { name: "Accesos rápidos" })).getByRole("button", { name: "Recetas" }));
  expect(screen.queryByRole("button", { name: "Volver al origen" })).toBeNull();
});

// Verifica que se conservan el plan montado y su desplazamiento al volver.
it("recupera el estado y desplazamiento del plan semanal", async () => {
  render(<App />);
  await screen.findByRole("textbox", { name: "Filtro de comidas" });
  fireEvent.click(within(screen.getByRole("navigation", { name: "Accesos rápidos" })).getByRole("button", { name: "Plan semanal" }));
  const plan = screen.getByRole("textbox", { name: "Estado del plan" });
  fireEvent.change(plan, { target: { value: "posición" } });
  const contenido = document.getElementById("workspace-content")!;
  contenido.scrollTop = 450;
  fireEvent.click(screen.getByRole("button", { name: "Abrir recetas del plan" }));
  contenido.scrollTop = 0;
  fireEvent.click(screen.getByRole("button", { name: "Volver al origen" }));
  expect((screen.getByRole("textbox", { name: "Estado del plan" }) as HTMLInputElement).value).toBe("posición");
  expect(contenido.scrollTop).toBe(450);
});
