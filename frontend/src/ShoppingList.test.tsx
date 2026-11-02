// Verifica la representación del catálogo de la compra.
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import ShoppingList from "./ShoppingList";

describe("ShoppingList", () => {
  it("shows saved categories and a category creation form", () => {
    // La representación estática necesita callbacks, pero no ejecuta la carga de productos.
    const markup = renderToStaticMarkup(
      <ShoppingList
        categories={[{ id: "1", name: "Verduras" }]}
        onCreateCategory={vi.fn()}
        onGetProducts={vi.fn().mockResolvedValue([])}
        onCreateProduct={vi.fn().mockResolvedValue({ id: "product-1", name: "Manzanas" })}
      />,
    );

    expect(markup).toContain("Verduras");
    expect(markup).toContain('aria-label="Nombre de la categoría"');
    expect(markup).toContain("Crear categoría");
  });
});
