import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import ShoppingList from "./ShoppingList";

describe("ShoppingList", () => {
  it("shows saved categories and a category creation form", () => {
    const markup = renderToStaticMarkup(
      <ShoppingList categories={[{ id: "1", name: "Verduras" }]} onCreateCategory={vi.fn()} />,
    );

    expect(markup).toContain("Verduras");
    expect(markup).toContain('aria-label="Nombre de la categoría"');
    expect(markup).toContain("Crear categoría");
  });
});
