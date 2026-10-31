import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import CalendarDay from "./CalendarDay";
import type { MealAssignment, MealSlot } from "./mealPlanningApi";

const date = "2026-10-27";

function day(slots: MealSlot[] = [], options = {}) {
  const assignments = new Map<string, MealAssignment>(slots.map((slot) => [`${date}:${slot}`, { id: slot, date, slot, label: { id: "rice", code: "arroz", name: "Arroz" } }]));
  return CalendarDay({ date, weekday: "Martes", today: true, assignments, disabled: false, onEdit: vi.fn(), onDelete: vi.fn(), ...options });
}

describe("CalendarDay", () => {
  it("identifies today and displays real assignments without fabricated recipes", () => {
    const markup = renderToStaticMarkup(day(["lunch"]));

    expect(markup).toContain('aria-current="date"');
    expect(markup).toContain('dateTime="2026-10-27"');
    expect(markup).toContain("Arroz");
    expect(markup).not.toContain('meal-card-status lunch');
    expect(markup).toContain("Sin planificar");
    expect(markup).toContain('aria-label="Editar almuerzo del martes, 27 de octubre de 2026"');
    expect(markup).toContain('aria-label="Eliminar almuerzo del martes, 27 de octubre de 2026: Arroz"');
    expect(markup).toContain('aria-label="Añadir cena del martes, 27 de octubre de 2026"');
    expect(markup).not.toContain("day-actions");
  });

  it("opens the editor only through the edit controls, not by clicking the cell", () => {
    const onEdit = vi.fn();
    const element = day(["lunch", "dinner"], { onEdit });
    const cards = element.props.children[1].props.children;

    cards[0].props.children[0].props.children[2].props.onClick();
    cards[1].props.children[0].props.children[2].props.onClick();

    expect(onEdit.mock.calls).toEqual([[date, "lunch"], [date, "dinner"]]);
  });

  it("renders the catalog image in the planning card when available", () => {
    const assignments = new Map<string, MealAssignment>([[`${date}:lunch`, {
      id: "assignment", date, slot: "lunch",
      label: { id: "rice", code: "arroz", name: "Arroz", image_url: "/food-labels/rice/image" },
    }]]);
    const markup = renderToStaticMarkup(CalendarDay({ date, weekday: "Martes", today: false, assignments, disabled: false, onEdit: vi.fn(), onDelete: vi.fn() }));
    expect(markup).toContain('src="/comemos/api/v1/food-labels/rice/image"');
    expect(markup).toContain('class="meal-thumbnail"');
    expect(markup).toContain("Arroz");
  });

  it("keeps the utensil fallback and month status alongside the dish name", () => {
    const assignments = new Map<string, MealAssignment>([[`${date}:lunch`, {
      id: "assignment", date, slot: "lunch",
      label: { id: "rice", code: "arroz", name: "Arroz" },
    }]]);
    const markup = renderToStaticMarkup(CalendarDay({ date, weekday: "Martes", today: false, compact: true, assignments, disabled: false, onEdit: vi.fn(), onDelete: vi.fn() }));

    expect(markup).toContain('class="meal-thumbnail"');
    expect(markup).toContain('class="app-icon "');
    expect(markup).toContain("Arroz");
    expect(markup).toContain('class="meal-card-status lunch"');
  });

  it("disables all controls while loading or saving", () => {
    const markup = renderToStaticMarkup(day([], { disabled: true }));
    expect(markup.match(/disabled=""/g)).toHaveLength(2);
  });

  it("keeps month cells compact and excludes redundant day-level actions", () => {
    const markup = renderToStaticMarkup(day(["lunch"], { compact: true, outsideMonth: true }));
    expect(markup).toContain("outside-month compact-day");
    expect(markup.match(/<button/g)).toHaveLength(3);
    expect(markup).not.toContain("add-meal");
  });
});
