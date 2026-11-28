// Comprueba la configuración opcional del recordatorio en el editor de comidas.
// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import MealPlanning from "./MealPlanning";
import { ApiError } from "./api";
import { applyMealPlanning, getMealPlanning, previewMealPlanning, type MealPlanningPreview, type MealPlanningResponse } from "./mealPlanningApi";

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

// Representa la semana inicial y el plato disponible en el catálogo.
const semana: MealPlanningResponse = { today: "2026-11-02", start_date: "2026-11-02", end_date: "2026-11-08", timezone: "Atlantic/Canary", assignments: [] };
const pescado = { id: "fish", code: "fish", name: "Pescado" };

// Comprueba que el editor reabre la comida con lo que devuelve la consulta posterior al guardado.
it.each(["sin aviso", "activo", "vencido"])("guarda y vuelve a abrir la comida (%s)", async (estado) => {
  const aviso = { days_before: 0, send_time: "18:30", message: "Sacar pescado" };
  const conRecordatorio = estado !== "sin aviso";
  const vencido = estado === "vencido";
  vi.mocked(getMealPlanning).mockResolvedValue(semana);
  vi.mocked(applyMealPlanning).mockImplementationOnce(async (operation) => {
    vi.mocked(getMealPlanning).mockResolvedValue({
      ...semana, assignments: [{ id: "1", date: semana.today, slot: "lunch", label: pescado, reminder: conRecordatorio ? { ...aviso, ...(vencido ? { skipped: true } : {}) } : null }],
    });
    return { operation, changed_count: 1, changed_dates: [semana.today] };
  });
  const usuario = userEvent.setup();
  render(<MealPlanning csrfToken="token" onSessionExpired={vi.fn()} />);
  await usuario.click(await screen.findByRole("button", { name: "Añadir almuerzo del lunes, 2 de noviembre de 2026" }));
  if (conRecordatorio) {
    await usuario.click(screen.getByRole("switch", { name: "Recordatorio" }));
    fireEvent.change(screen.getByLabelText("Días de antelación"), { target: { value: "0" } });
    fireEvent.change(screen.getByLabelText("Hora del recordatorio"), { target: { value: "18:30" } });
    await usuario.type(screen.getByLabelText("Mensaje del recordatorio"), aviso.message);
  }
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  const operacion = { action: "assign", start_date: semana.today, slot: "lunch", label_id: pescado.id, repeat: null, ...(conRecordatorio ? { reminder: aviso } : {}) };
  expect(previewMealPlanning).toHaveBeenCalledWith(operacion, "token");
  expect(applyMealPlanning).toHaveBeenCalledWith(operacion, "token", "token");
  if (vencido) expect(await screen.findByRole("img", { name: "Recordatorio vencido: no se enviará" })).toBeTruthy();
  await usuario.click(await screen.findByRole("button", { name: /Editar almuerzo del lunes, 2 de noviembre de 2026/ }));
  expect(screen.getByRole<HTMLInputElement>("switch", { name: "Recordatorio" }).checked).toBe(conRecordatorio);
  if (conRecordatorio) {
    expect(screen.getByLabelText<HTMLInputElement>("Días de antelación").value).toBe("0");
    expect(screen.getByLabelText<HTMLInputElement>("Hora del recordatorio").value).toBe(aviso.send_time);
    expect(screen.getByLabelText<HTMLTextAreaElement>("Mensaje del recordatorio").value).toBe(aviso.message);
  }
  if (vencido) {
    expect(screen.getByText(/Este aviso no se enviará/)).toBeTruthy();
    fireEvent.change(screen.getByLabelText("Hora del recordatorio"), { target: { value: "19:30" } });
    expect(screen.queryByText(/Este aviso no se enviará/)).toBeNull();
  }
});

// Comprueba que un conflicto al guardar directamente no pierde el borrador del recordatorio.
it("pide confirmación tras un conflicto y conserva el recordatorio", async () => {
  const aviso = { days_before: 1, send_time: "09:00", message: "Preparar pescado" };
  const operacion = { action: "assign", start_date: semana.today, slot: "lunch", label_id: pescado.id, repeat: null, reminder: aviso } as const;
  const anterior: MealPlanningPreview = { operation: operacion, requires_confirmation: false, preview_token: "anterior", dates: [], changed_count: 1, changed_dates: [semana.today], change_count: 1 };
  vi.mocked(getMealPlanning).mockResolvedValue(semana);
  vi.mocked(applyMealPlanning).mockRejectedValueOnce(new ApiError(409, "Planning changed"));
  vi.mocked(previewMealPlanning).mockResolvedValueOnce(anterior).mockResolvedValueOnce({
    ...anterior, preview_token: "actual",
    dates: [{ date: semana.today, slot: "lunch", change: "update_reminder", current_label: pescado, resulting_label: pescado }],
  });
  const usuario = userEvent.setup();
  render(<MealPlanning csrfToken="token" onSessionExpired={vi.fn()} />);
  await usuario.click(await screen.findByRole("button", { name: "Añadir almuerzo del lunes, 2 de noviembre de 2026" }));
  await usuario.click(screen.getByRole("switch", { name: "Recordatorio" }));
  await usuario.type(screen.getByLabelText("Mensaje del recordatorio"), aviso.message);
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  const confirmar = await screen.findByRole("button", { name: "Confirmar y guardar" });
  expect(screen.getByText("Actualizar recordatorio de Pescado")).toBeTruthy();
  expect(applyMealPlanning).toHaveBeenCalledTimes(1);
  await usuario.click(confirmar);
  expect(applyMealPlanning).toHaveBeenLastCalledWith(operacion, "actual", "token");
  expect(await screen.findByText("Se guardó 1 cambio.")).toBeTruthy();
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
