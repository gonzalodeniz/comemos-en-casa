// @vitest-environment jsdom
// Verifica la representación y las interacciones del catálogo de la compra.
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import ShoppingList from "./ShoppingList";

afterEach(() => cleanup());

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

  // Comprueba que el producto existente se envía con la cantidad y la unidad elegidas.
  it("anade_producto_del_catalogo_con_cantidad_y_medida", async () => {
    const user = userEvent.setup();
    const onAddToShoppingList = vi.fn();

    render(<ShoppingList
      categories={[{ id: "category-1", name: "Fruta" }]}
      onCreateCategory={vi.fn()}
      onGetProducts={vi.fn().mockResolvedValue([{ id: "product-1", name: "Manzanas" }])}
      onCreateProduct={vi.fn()}
      onAddToShoppingList={onAddToShoppingList}
    />);

    await user.type(await screen.findByLabelText("Cantidad de Manzanas"), "1.5");
    await user.selectOptions(screen.getByLabelText("Unidad de Manzanas"), "kg");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));

    expect(onAddToShoppingList).toHaveBeenCalledWith("product-1", 1.5, "kg");
  });
});
