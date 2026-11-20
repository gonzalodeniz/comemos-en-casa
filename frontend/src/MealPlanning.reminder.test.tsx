// Comprueba la configuración opcional del recordatorio en el editor de comidas.
// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import MealPlanning from "./MealPlanning";

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
