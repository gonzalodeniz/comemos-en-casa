import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import MealPlanning, { filterFoodLabels, snapshotOperation } from "./MealPlanning";

describe("MealPlanning presentation", () => {
  it("renders the weekly layout with accessible date and view controls", () => {
    const markup = renderToStaticMarkup(<MealPlanning csrfToken="test" onSessionExpired={() => {}} />);

    expect(markup).toContain("Planificación de comidas");
    expect(markup).toContain("Semana del");
    expect(markup).toContain('aria-label="Semana anterior"');
    expect(markup).toContain('aria-label="Semana siguiente"');
    expect(markup).toContain('aria-label="Vista del calendario"');
    expect(markup).toContain('aria-pressed="true" disabled="">Semana');
    expect(markup).toContain('aria-pressed="false" disabled="">Mes');
    expect(markup).toContain("Volver a hoy");
    expect(markup.match(/<article/g)).toHaveLength(7);
    expect(markup.match(/class="meal-slot /g)).toHaveLength(14);
    expect(markup.match(/week-heading-label/g)).toHaveLength(2);
    expect(markup.match(/class="day-actions"/g)).toHaveLength(7);
    expect(markup).toContain("Cargando planificación");
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
