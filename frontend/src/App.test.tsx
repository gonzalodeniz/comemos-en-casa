import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import App from "./App";
import { deleteAssignment, getCalendarContext, getCalendarWeek, getCurrentUser, updateAssignment } from "./api";
import type { CalendarAssignment } from "./types";

vi.mock("./api", () => ({
  ApiError: class ApiError extends Error {},
  addRecipeToCollection: vi.fn(),
  createAssignment: vi.fn(),
  createCollection: vi.fn(),
  createRecipe: vi.fn(),
  deleteAssignment: vi.fn(),
  deleteRecipe: vi.fn(),
  getCalendarContext: vi.fn(),
  getCalendarWeek: vi.fn(),
  getCollections: vi.fn(),
  getCurrentUser: vi.fn(),
  getFavorites: vi.fn(),
  getPublicRecipe: vi.fn(),
  getRecipeCatalogue: vi.fn(),
  logout: vi.fn(),
  searchPublicRecipes: vi.fn(),
  setFavorite: vi.fn(),
  setRecipeStatus: vi.fn(),
  updateAssignment: vi.fn(),
  updateRecipe: vi.fn(),
  uploadRecipeImage: vi.fn(),
}));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

function mockCalendar(weekStart = "2026-09-14", assignments: CalendarAssignment[] = []) {
  vi.mocked(getCurrentUser).mockResolvedValue(null);
  vi.mocked(getCalendarContext).mockResolvedValue({
    timezone: "Europe/Madrid",
    currentWeekStart: "2026-09-14",
    guestMode: false,
  });
  vi.mocked(getCalendarWeek).mockImplementation(async (requestedWeekStart) => ({
    timezone: "Europe/Madrid",
    weekStart: requestedWeekStart,
    weekEnd: requestedWeekStart === "2026-09-07" ? "2026-09-13" : requestedWeekStart === "2026-09-21" ? "2026-09-27" : "2026-09-20",
    assignments,
  }));
  vi.mocked(deleteAssignment).mockResolvedValue();
  return weekStart;
}

test("renders the calendar without network access", async () => {
  mockCalendar();
  const fetchSpy = vi.spyOn(globalThis, "fetch");

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

  expect(await screen.findByRole("heading", { name: /Semana del 14 de septiembre – 20 de septiembre/ })).toBeTruthy();
  expect(document.querySelector("main.calendar-workspace header")).toBeNull();
  expect(await screen.findByRole("table")).toBeTruthy();
  expect(getCalendarContext).toHaveBeenCalledOnce();
  expect(getCalendarWeek).toHaveBeenCalledWith("2026-09-14", expect.any(AbortSignal));
  expect(fetchSpy).not.toHaveBeenCalled();
});

test("composes the weekly planning frame with seven days and both meal rows", async () => {
  mockCalendar();

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

  expect(await screen.findByRole("heading", { name: /Semana del 14 de septiembre – 20 de septiembre/ })).toBeTruthy();
  const brand = screen.getByRole("link", { name: /Como en casa/ });
  expect(brand.textContent).toContain("Como en casa");
  const primaryNav = screen.getByRole("navigation", { name: "Navegación principal" });
  expect(within(primaryNav).queryByRole("link", { name: "Calendario" })).toBeNull();
  expect(within(primaryNav).queryByRole("link", { name: "Recetas" })).toBeNull();
  expect(screen.getByRole("searchbox", { name: "Buscar recetas" })).toBeTruthy();
  const calendarSidebar = screen.getByRole("navigation", { name: "Secciones del espacio de planificación" });
  expect(calendarSidebar.textContent).toContain("Calendario");
  expect(within(calendarSidebar).getByRole("link", { name: "Calendario" }).getAttribute("href")).toBe("/calendario");
  expect(screen.getByRole("complementary", { name: "Consejo de planificación" }).textContent).toContain("Buena comida, mejores momentos");
  const weekControls = document.querySelector(".week-controls");
  expect(weekControls).not.toBeNull();
  expect(within(weekControls as HTMLElement).getByRole("button", { name: "+ Añadir comida" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Semana anterior" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Hoy" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Semana siguiente" })).toBeTruthy();
  expect(screen.getByRole("heading", { name: /Semana del 14 de septiembre – 20 de septiembre/ })).toBeTruthy();
  expect(await screen.findByRole("table")).toBeTruthy();
  expect(screen.getAllByRole("columnheader")).toHaveLength(8);
  expect(screen.getByRole("columnheader", { name: /lunes 14/ })).toBeTruthy();
  expect(screen.getByRole("columnheader", { name: /domingo 20/ })).toBeTruthy();
  expect(screen.getByRole("rowheader", { name: /Comida/ })).toBeTruthy();
  expect(screen.getByRole("rowheader", { name: /Cena/ })).toBeTruthy();
});

test("uses a vertical day-by-day calendar on mobile without rendering the wide table", async () => {
  vi.stubGlobal("matchMedia", vi.fn().mockImplementation((query: string) => ({
    matches: query === "(max-width: 760px)",
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  })));
  mockCalendar();

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

  expect(await screen.findByLabelText("Calendario semanal por día")).toBeTruthy();
  expect(screen.queryByRole("table")).toBeNull();
  expect(screen.getAllByRole("heading", { name: /lunes 14|martes 15|miércoles 16|jueves 17|viernes 18|sábado 19|domingo 20/ })).toHaveLength(7);
  expect(screen.getAllByRole("button", { name: /^Añadir comida el/ })).toHaveLength(7);
  expect(screen.getAllByRole("button", { name: /^Añadir cena el/ })).toHaveLength(7);
});

test("keeps week controls and the global add action on existing calendar flows", async () => {
  mockCalendar("2026-09-07");

  render(<MemoryRouter initialEntries={["/semanas/2026-09-07"]}><App /></MemoryRouter>);

  await screen.findByRole("heading", { name: /Semana del 7 de septiembre – 13 de septiembre/ });
  fireEvent.click(screen.getByRole("button", { name: "Hoy" }));
  await waitFor(() => expect(getCalendarWeek).toHaveBeenCalledWith("2026-09-14", expect.any(AbortSignal)));
  fireEvent.click(screen.getByRole("button", { name: "Semana anterior" }));
  await waitFor(() => expect(getCalendarWeek).toHaveBeenCalledWith("2026-09-07", expect.any(AbortSignal)));
  fireEvent.click(screen.getByRole("button", { name: "Semana siguiente" }));
  await waitFor(() => expect(getCalendarWeek).toHaveBeenCalledWith("2026-09-14", expect.any(AbortSignal)));
  fireEvent.click(screen.getByRole("button", { name: "+ Añadir comida" }));
  expect(await screen.findByRole("heading", { name: /Comida/ })).toBeTruthy();
});

test("renders recipe cards with an informative image and keeps titles when the image is unavailable", async () => {
  mockCalendar("2026-09-14", [
    {
      id: "recipe-with-image",
      date: "2026-09-14",
      slot: "lunch",
      kind: "recipe",
      recipe: { id: "recipe-1", available: true, title: "Arroz al horno", coverImageUrl: "https://example.test/arroz.jpg" },
    },
    {
      id: "recipe-without-image",
      date: "2026-09-15",
      slot: "dinner",
      kind: "recipe",
      recipe: { id: "recipe-2", available: true, title: "Una receta con un título deliberadamente largo para comprobar su lectura", coverImageUrl: null },
    },
    {
      id: "missing-recipe",
      date: "2026-09-16",
      slot: "lunch",
      kind: "recipe",
      recipe: { id: null, available: false, title: "Receta retirada", coverImageUrl: null },
    },
  ]);

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

  expect(await screen.findByAltText("Portada de Arroz al horno")).toBeTruthy();
  expect(screen.getByRole("article", { name: /Arroz al horno, comida del lun, 14 sept/ })).toBeTruthy();
  expect(screen.getByText("Una receta con un título deliberadamente largo para comprobar su lectura")).toBeTruthy();
  expect(screen.getByText("Receta no disponible")).toBeTruthy();
  expect(screen.getAllByText("🍲").length).toBeGreaterThan(0);
});

test("opens the existing contextual creation flow with the selected day and meal slot", async () => {
  mockCalendar();

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

  const calendarScroll = await screen.findByLabelText("Calendario semanal desplazable horizontalmente");
  expect(calendarScroll.getAttribute("role")).toBe("region");
  expect(calendarScroll.getAttribute("aria-describedby")).toBe("calendar-scroll-instructions");
  calendarScroll.focus();
  expect(document.activeElement).toBe(calendarScroll);
  const lunchButtons = screen.getAllByRole("button", { name: /^Añadir comida el/ });
  const dinnerButtons = screen.getAllByRole("button", { name: /^Añadir cena el/ });
  expect(lunchButtons).toHaveLength(7);
  expect(dinnerButtons).toHaveLength(7);
  lunchButtons.forEach((button) => expect(button.textContent).toBe("+ Añadir comida"));
  dinnerButtons.forEach((button) => expect(button.textContent).toBe("+ Añadir cena"));
  expect(lunchButtons[0].closest("td")?.getAttribute("headers")).toBe("calendar-slot-lunch calendar-day-2026-09-14");
  expect(dinnerButtons[6].closest("td")?.getAttribute("headers")).toBe("calendar-slot-dinner calendar-day-2026-09-20");
  fireEvent.click(await screen.findByRole("button", { name: "Añadir comida el lun, 14 sept" }));
  expect(await screen.findByRole("heading", { name: /Comida/ })).toBeTruthy();
  expect(screen.getByText(/Nueva comida/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
  fireEvent.click(screen.getByRole("button", { name: "Añadir cena el dom, 20 sept" }));
  expect(await screen.findByRole("heading", { name: /Cena/ })).toBeTruthy();
});

test("keeps existing card edit and delete actions reachable", async () => {
  const assignment: CalendarAssignment = {
    id: "free-text-assignment",
    date: "2026-09-14",
    slot: "dinner",
    kind: "free_text",
    text: "Guiso de verduras",
  };
  mockCalendar("2026-09-14", [assignment]);
  vi.mocked(updateAssignment).mockResolvedValue(assignment);
  const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

  await screen.findByRole("article", { name: /Guiso de verduras, cena del lun, 14 sept/ });
  fireEvent.click(screen.getByRole("button", { name: "Editar Guiso de verduras" }));
  expect(await screen.findByText("Editar comida")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
  await waitFor(() => expect(updateAssignment).toHaveBeenCalledWith("free-text-assignment", {
    date: "2026-09-14",
    slot: "dinner",
    kind: "free_text",
    text: "Guiso de verduras",
  }));
  fireEvent.click(screen.getByRole("button", { name: "Eliminar Guiso de verduras" }));
  await waitFor(() => expect(deleteAssignment).toHaveBeenCalledWith("free-text-assignment"));
  expect(confirmSpy).toHaveBeenCalledOnce();
});

test("marks the calendar region as busy while the weekly data is loading", async () => {
  vi.mocked(getCurrentUser).mockResolvedValue(null);
  vi.mocked(getCalendarContext).mockResolvedValue({ timezone: "Europe/Madrid", currentWeekStart: "2026-09-14", guestMode: false });
  vi.mocked(getCalendarWeek).mockReturnValue(new Promise(() => undefined));

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

  const calendar = await screen.findByRole("region", { name: /Semana del/ });
  await waitFor(() => expect(calendar.getAttribute("aria-busy")).toBe("true"));
});

test("keeps the existing calendar error visible", async () => {
  vi.mocked(getCurrentUser).mockResolvedValue(null);
  vi.mocked(getCalendarContext).mockResolvedValue({ timezone: "Europe/Madrid", currentWeekStart: "2026-09-14", guestMode: false });
  vi.mocked(getCalendarWeek).mockRejectedValue(new Error("offline"));

  render(<MemoryRouter initialEntries={["/"]}><App /></MemoryRouter>);

  expect(await screen.findByRole("alert")).toBeTruthy();
});
