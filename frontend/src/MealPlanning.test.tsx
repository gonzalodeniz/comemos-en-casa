import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import MealPlanning, { adjacentWeek, extendWeeks, filterFoodLabels, repeatFromInterval, snapshotOperation, weekLabel } from "./MealPlanning";
import { addCalendarDays } from "./mealPlanningDates";

describe("MealPlanning presentation", () => {
  it("renders the weekly layout with accessible date and view controls", () => {
    const markup = renderToStaticMarkup(<MealPlanning csrfToken="test" onSessionExpired={() => {}} />);

    expect(markup).toContain("Planificación de comidas");
    expect(markup).toContain("Semana del");
    expect(markup).not.toContain('aria-label="Semana anterior"');
    expect(markup).not.toContain('aria-label="Semana siguiente"');
    expect(markup).toContain('aria-label="Vista del calendario"');
    expect(markup).toContain('aria-pressed="true" disabled="">Semana');
    expect(markup).toContain('aria-pressed="false" disabled="">Mes');
    expect(markup).toContain("Volver a hoy");
    expect(markup.match(/<article/g)).toHaveLength(7);
    expect(markup.match(/class="meal-slot /g)).toHaveLength(14);
    expect(markup.match(/week-heading-label/g)).toHaveLength(2);
    expect(markup).not.toContain("day-actions");
    expect(markup).toContain("Cargando planificación");
  });

});

describe("continuous weekly planning", () => {
  it("finds adjacent weeks at either end of the loaded range", () => {
    const starts = ["2026-12-21", "2026-12-28", "2027-01-04"] as const;
    expect(adjacentWeek([...starts], -1)).toBe("2026-12-14");
    expect(adjacentWeek([...starts], 1)).toBe("2027-01-11");
  });

  it("labels weeks across months and years without losing context", () => {
    expect(weekLabel("2026-11-02")).toBe("Semana del 2 al 8 de noviembre de 2026");
    expect(weekLabel("2026-12-28")).toBe("Semana del 28 de diciembre de 2026 al 3 de enero de 2027");
  });

  it("bounds the loaded window while allowing scrolling in either direction", () => {
    const starts = Array.from({ length: 26 }, (_, index) => addCalendarDays("2026-01-05", index * 7));
    const next = extendWeeks(starts, 1);
    expect(next).toHaveLength(26);
    expect(next[0]).toBe(starts[1]);
    expect(next[25]).toBe(addCalendarDays(starts[25], 7));
    const previous = extendWeeks(next, -1);
    expect(previous).toEqual(starts);
  });
});

describe("dish search", () => {
  const labels = [{ id: "1", code: "rice", name: "Arroz" }, { id: "2", code: "fish", name: "Pescado" }];
  it("filters the existing catalogue case-insensitively without changing it", () => {
    expect(filterFoodLabels(labels, "  PESc ")).toEqual([labels[1]]);
    expect(filterFoodLabels(labels, "missing")).toEqual([]);
    expect(filterFoodLabels(labels, "")).toEqual(labels);
  });
});

it("keeps a preview operation unchanged if the editor changes while a request is pending", () => {
  const operation = { action: "assign" as const, start_date: "2026-10-27", slot: "lunch" as const, label_id: "rice", repeat: { interval_weeks: 1, end_date: "2026-12-01" } };
  const snapshot = snapshotOperation(operation);
  operation.label_id = "fish";
  operation.repeat.interval_weeks = 2;
  expect(snapshot.label_id).toBe("rice");
  expect(snapshot.repeat?.interval_weeks).toBe(1);
});

describe("repeat interval payload", () => {
  it("omits recurrence for a zero-week interval", () => {
    expect(repeatFromInterval("0", "2026-12-01")).toBeNull();
  });

  it("includes the interval and end date for positive intervals", () => {
    expect(repeatFromInterval("3", "2026-12-01")).toEqual({ interval_weeks: 3, end_date: "2026-12-01" });
  });
});
