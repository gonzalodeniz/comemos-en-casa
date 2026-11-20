// Comprueba la configuración opcional del recordatorio en el editor de comidas.
// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import MealPlanning from "./MealPlanning";
import { getMealPlanning } from "./mealPlanningApi";

vi.mock("./mealPlanningApi", () => ({
  getFoodLabels: vi.fn().mockResolvedValue({ labels: [{ id: "fish", code: "fish", name: "Pescado" }] }),
  getMealPlanning: vi.fn().mockResolvedValue({ today: "2026-11-02", assignments: [] }),
  previewMealPlanning: vi.fn().mockResolvedValue({ requires_confirmation: false, preview_token: "token", changed_count: 1, dates: [] }),
  applyMealPlanning: vi.fn().mockResolvedValue({ changed_count: 1 }),
}));
vi.mock("./mealPlanningDates", async (original) => ({ ...await original<typeof import("./mealPlanningDates")>(), localToday: () => "2026-11-02" }));
window.matchMedia = vi.fn().mockReturnValue({ matches: false, addEventListener: vi.fn(), removeEventListener: vi.fn() });
vi.stubGlobal("ResizeObserver", class { observe() {} unobserve() {} disconnect() {} });
Object.defineProperty(document, "fonts", { value: { ready: Promise.resolve() }, configurable: true });
afterEach(() => { cleanup(); vi.clearAllMocks(); });

it("muestra los campos opcionales del recordatorio y acepta cero días", async () => {
  const user = userEvent.setup();
  render(<MealPlanning csrfToken="token" onSessionExpired={vi.fn()} />);
  await user.click(await screen.findByRole("button", { name: "Añadir almuerzo del lunes, 2 de noviembre de 2026" }));
  const dialog = screen.getByRole("dialog", { name: "Asignar comida" });
  expect(dialog.textContent?.indexOf("Recordatorio")).toBeGreaterThan(dialog.textContent?.indexOf("Repetir") ?? -1);
  expect(screen.queryByLabelText("Días de antelación")).toBeNull();
  await user.click(screen.getByRole("switch", { name: "Recordatorio" }));
  const days = screen.getByLabelText("Días de antelación");
  await user.clear(days);
  await user.type(days, "0");
  expect((days as HTMLInputElement).value).toBe("0");
  expect(screen.getByLabelText("Hora del recordatorio")).toBeTruthy();
  expect(screen.getByLabelText("Mensaje del recordatorio")).toBeTruthy();
});

// Comprueba que editar una comida conserva su recordatorio existente.
it("muestra el recordatorio guardado al editar la comida", async () => {
  vi.mocked(getMealPlanning).mockResolvedValue({ today: "2026-11-02", start_date: "2026-11-02", end_date: "2026-11-08", timezone: "Atlantic/Canary", assignments: [{ id: "1", date: "2026-11-02", slot: "lunch", label: { id: "fish", code: "fish", name: "Pescado" }, reminder: { days_before: 2, send_time: "18:30", message: "Sacar pescado" } }] } as Awaited<ReturnType<typeof getMealPlanning>>);
  const user = userEvent.setup();
  render(<MealPlanning csrfToken="token" onSessionExpired={vi.fn()} />);
  await user.click(await screen.findByRole("button", { name: /Editar almuerzo del lunes, 2 de noviembre de 2026/ }));
  expect((screen.getByRole("switch", { name: "Recordatorio" }) as HTMLInputElement).checked).toBe(true);
  expect((screen.getByLabelText("Días de antelación") as HTMLInputElement).value).toBe("2");
  expect((screen.getByLabelText("Hora del recordatorio") as HTMLInputElement).value).toBe("18:30");
  expect((screen.getByLabelText("Mensaje del recordatorio") as HTMLTextAreaElement).value).toBe("Sacar pescado");
});
