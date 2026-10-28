import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import CalendarDay from "./CalendarDay";
import type { MealAssignment, MealSlot } from "./mealPlanningApi";

const date = "2026-10-27";

function day(slots: MealSlot[] = [], options = {}) {
  const assignments = new Map<string, MealAssignment>(slots.map((slot) => [`${date}:${slot}`, { id: slot, date, slot, label: { id: "rice", code: "arroz", name: "Arroz" } }]));
  return CalendarDay({ date, weekday: "Martes", today: true, assignments, disabled: false, onEdit: vi.fn(), ...options });
}

describe("CalendarDay", () => {
  it("identifies today and displays real assignments without fabricated recipes", () => {
    const markup = renderToStaticMarkup(day(["lunch"]));

    expect(markup).toContain('aria-current="date"');
    expect(markup).toContain('dateTime="2026-10-27"');
    expect(markup).toContain("Arroz");
    expect(markup).toContain("Almuerzo");
    expect(markup).toContain("Sin planificar");
    expect(markup).toContain("Editar almuerzo del martes, 27 de octubre de 2026: Arroz");
    expect(markup).toContain("Planificar cena del martes, 27 de octubre de 2026");
  });

  it("keeps both meal cards individually editable", () => {
    const onEdit = vi.fn();
    const element = day(["lunch", "dinner"], { onEdit });
    const buttons = element.props.children[1].props.children;

    buttons[0].props.onClick();
    buttons[1].props.onClick();

    expect(onEdit.mock.calls).toEqual([[date, "lunch"], [date, "dinner"]]);
  });

  it("disables all controls while loading or saving", () => {
    const markup = renderToStaticMarkup(day([], { disabled: true }));
    expect(markup.match(/disabled=""/g)).toHaveLength(2);
  });

  it("keeps month cells compact and excludes redundant day-level actions", () => {
    const markup = renderToStaticMarkup(day(["lunch"], { compact: true, outsideMonth: true }));
    expect(markup).toContain("outside-month compact-day");
    expect(markup.match(/<button/g)).toHaveLength(2);
    expect(markup).not.toContain("add-meal");
  });
});
