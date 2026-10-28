import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";
import MealPlanning from "./MealPlanning";

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
    expect(markup).toContain("Cargando planificación");
  });
});
