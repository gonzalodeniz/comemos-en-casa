// @vitest-environment jsdom
// Comprueba el flujo de borrado recurrente de comidas.
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import MealPlanning from "./MealPlanning";
import { applyMealPlanning, previewMealPlanning } from "./mealPlanningApi";

vi.mock("./mealPlanningDates", async (importOriginal) => ({ ...await importOriginal<typeof import("./mealPlanningDates")>(), localToday: () => "2026-11-02" }));
vi.mock("./mealPlanningApi", () => ({
  getFoodLabels: vi.fn().mockResolvedValue({ labels: [{ id: "fish", code: "fish", name: "Pescado" }] }),
  getMealPlanning: vi.fn().mockResolvedValue({ today: "2026-11-02", assignments: [{ id: "1", date: "2026-11-02", slot: "lunch", label: { id: "fish", code: "fish", name: "Pescado" } }] }),
  previewMealPlanning: vi.fn().mockResolvedValue({ requires_confirmation: true, preview_token: "token", changed_count: 2, dates: [
    { date: "2026-11-02", slot: "lunch", change: "delete", current_label: { id: "fish", name: "Pescado" } },
    { date: "2026-11-16", slot: "lunch", change: "delete", current_label: { id: "rice", name: "Arroz" } },
  ] }),
  applyMealPlanning: vi.fn().mockResolvedValue({ changed_count: 2 }),
}));
afterEach(() => { cleanup(); vi.clearAllMocks(); });
// Simula la consulta de medios que el calendario utiliza en el navegador.
window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() });
// Simula la observación de tamaño ausente en jsdom.
vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
Object.defineProperty(document, "fonts", { value: { ready: Promise.resolve() }, configurable: true });

// Verifica que el panel de borrado permite elegir frecuencia y fecha final.
it("configura el borrado periódico desde el panel de la comida", async () => {
  const usuario = userEvent.setup();
  render(<MealPlanning csrfToken="token" onSessionExpired={vi.fn()} />);
  await usuario.click(await screen.findByRole("button", { name: /Eliminar almuerzo.*Pescado/ }));
  const panel = screen.getByRole("dialog", { name: "Borrar comida" });
  await usuario.click(within(panel).getByRole("switch", { name: "Repetir" }));
  const intervalo = within(panel).getByLabelText("Intervalo en semanas");
  await usuario.clear(intervalo);
  await usuario.type(intervalo, "2");
  const fecha = within(panel).getByLabelText("Fecha final");
  await usuario.clear(fecha);
  await usuario.type(fecha, "2026-11-16");
  const editar = panel.querySelector(".drawer-edit-fields")!;
  expect(editar.nextElementSibling?.classList.contains("drawer-actions")).toBe(true);
  expect(within(panel).getByRole("button", { name: "Borrar" })).toBeTruthy();
  await usuario.click(within(panel).getByRole("button", { name: "Borrar" }));
  expect(previewMealPlanning).toHaveBeenCalledWith({ action: "delete", start_date: "2026-11-02", slot: "lunch", label_id: "fish", repeat: { interval_weeks: 2, end_date: "2026-11-16" } }, "token");
  expect(within(panel).getByText("Eliminar Pescado")).toBeTruthy();
  expect(within(panel).getByText("Eliminar Arroz")).toBeTruthy();
  expect(applyMealPlanning).not.toHaveBeenCalled();
  await usuario.click(within(panel).getByRole("button", { name: "Confirmar y guardar" }));
  expect(applyMealPlanning).toHaveBeenCalledOnce();
});

// Comprueba la apertura de los filtros, el cambio de vista y la persistencia de la comida.
it("pliega los filtros al abrir y recuerda la última comida seleccionada", async () => {
  const usuario = userEvent.setup();
  const consultaMedios = vi.mocked(window.matchMedia);
  consultaMedios.mockReturnValueOnce({ matches: true } as MediaQueryList);
  const props = { csrfToken: "token", onSessionExpired: vi.fn() };
  const primeraVista = render(<MealPlanning {...props} />);
  const filtros = screen.getByRole("button", { name: "Filtros de planificación" });
  expect(filtros.getAttribute("aria-expanded")).toBe("false");
  expect(document.getElementById("filtros-planificacion")?.dataset.abiertos).toBe("false");
  await screen.findByRole("button", { name: /Eliminar almuerzo.*Pescado/ });
  expect(screen.queryByRole("button", { name: /Añadir cena/ })).toBeNull();

  await usuario.click(filtros);
  expect(document.getElementById("filtros-planificacion")?.dataset.abiertos).toBe("true");
  const comidas = within(screen.getByRole("group", { name: "Comidas visibles" }));
  const periodo = within(screen.getByRole("group", { name: "Vista del calendario" }));
  expect(comidas.getAllByRole("button").map((boton) => boton.textContent?.trim())).toEqual(["Ambas", "☀️ Almuerzo", "🌙 Cena"]);
  expect(comidas.getByRole("button", { name: "Almuerzo", pressed: true })).toBeTruthy();
  expect(periodo.getByRole("button", { name: "Semana", pressed: true })).toBeTruthy();
  await usuario.click(comidas.getByRole("button", { name: "Cena" }));
  expect(screen.queryByRole("button", { name: /Eliminar almuerzo/ })).toBeNull();
  await usuario.click(periodo.getByRole("button", { name: "Mes" }));
  expect(await screen.findByRole("region", { name: "Planificación mensual" })).toBeTruthy();
  await usuario.click(filtros);
  expect(document.getElementById("filtros-planificacion")?.dataset.abiertos).toBe("false");

  primeraVista.unmount();
  render(<MealPlanning {...props} />);
  await usuario.click(screen.getByRole("button", { name: "Filtros de planificación" }));
  expect(screen.getByRole("button", { name: "Cena", pressed: true })).toBeTruthy();
  localStorage.removeItem("meal-planning-visible-slot");
});
