// Comprueba que el filtro visual conserva únicamente la comida elegida.
import { renderToStaticMarkup } from "react-dom/server";
import { expect, it } from "vitest";
import CalendarDay from "./CalendarDay";

it("filtra las comidas tanto en vista normal como compacta", () => {
  for (const compact of [false, true]) {
    const html = renderToStaticMarkup(<CalendarDay date="2026-11-17" weekday="Martes" today={false} compact={compact} visibleSlot="lunch" assignments={new Map()} disabled={false} onEdit={() => {}} onDelete={() => {}} />);
    expect(html).toContain("Añadir almuerzo");
    expect(html).not.toContain("Añadir cena");
    expect(html).toContain("2026-11-17");
  }
});
