// @vitest-environment jsdom
// Verifica la representación y las interacciones del catálogo de la compra.
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderToStaticMarkup } from "react-dom/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import ShoppingList from "./ShoppingList";

afterEach(() => cleanup());

describe("ShoppingList", () => {
  // Comprueba la presentación de ingredientes copiados en el orden original.
  it("muestra la sección de receta con sus ingredientes en orden", async () => {
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()}
      onGetProducts={vi.fn()} onCreateProduct={vi.fn()}
      onGetShoppingList={vi.fn().mockResolvedValue({ items: [], recipe_sections: [
        { id: "seccion", name: "Sopa", ingredients: [
          { id: "a", text: "agua", purchased: false },
          { id: "b", text: "sal", purchased: false },
        ] },
      ] })} />);
    const seccion = await screen.findByRole("region", { name: "Sopa" });
    expect(within(seccion).getAllByRole("listitem").map(item => item.firstChild?.textContent)).toEqual(["agua", "sal"]);
  });

  it("marca como comprado un ingrediente de receta", async () => {
    const onMarkRecipeIngredient = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()}
      onGetProducts={vi.fn()} onCreateProduct={vi.fn()}
      onMarkRecipeIngredient={onMarkRecipeIngredient}
      onGetShoppingList={vi.fn().mockResolvedValue({ items: [], recipe_sections: [
        { id: "seccion", name: "Sopa", ingredients: [{ id: "agua-1", text: "agua", purchased: false }] },
      ] })} />);
    await user.click(await screen.findByRole("button", { name: "Marcar agua como comprado" }));
    expect(onMarkRecipeIngredient).toHaveBeenCalledWith("agua-1");
  });

  it("devuelve a pendiente un ingrediente de receta", async () => {
    const onUnmarkRecipeIngredient = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()}
      onGetProducts={vi.fn()} onCreateProduct={vi.fn()}
      onUnmarkRecipeIngredient={onUnmarkRecipeIngredient}
      onGetShoppingList={vi.fn().mockResolvedValue({ items: [], recipe_sections: [
        { id: "seccion", name: "Sopa", ingredients: [{ id: "agua-1", text: "agua", purchased: true }] },
      ] })} />);
    await user.click(await screen.findByRole("button", { name: "Desmarcar agua como comprado" }));
    expect(onUnmarkRecipeIngredient).toHaveBeenCalledWith("agua-1");
  });

  it("elimina un ingrediente de receta de su sección", async () => {
    const onDeleteRecipeIngredient = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()}
      onGetProducts={vi.fn()} onCreateProduct={vi.fn()}
      onDeleteRecipeIngredient={onDeleteRecipeIngredient}
      onGetShoppingList={vi.fn().mockResolvedValue({ items: [], recipe_sections: [
        { id: "seccion", name: "Sopa", ingredients: [
          { id: "agua-1", text: "agua", purchased: false },
          { id: "sal-1", text: "sal", purchased: false },
        ] },
      ] })} />);
    await user.click(await screen.findByRole("button", { name: "Eliminar agua" }));
    expect(onDeleteRecipeIngredient).toHaveBeenCalledWith("agua-1");
    expect(screen.queryByText("agua", { selector: "li" })).toBeNull();
    expect(screen.getByText("sal", { selector: "li" })).not.toBeNull();
  });

  it("elimina una sección de receta completa", async () => {
    const onDeleteRecipeSection = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()}
      onGetProducts={vi.fn()} onCreateProduct={vi.fn()}
      onDeleteRecipeSection={onDeleteRecipeSection}
      onGetShoppingList={vi.fn().mockResolvedValue({ items: [], recipe_sections: [
        { id: "seccion", name: "Sopa", ingredients: [{ id: "agua-1", text: "agua", purchased: false }] },
        { id: "otra", name: "Ensalada", ingredients: [{ id: "tomate-1", text: "tomate", purchased: false }] },
      ] })} />);
    await user.click(await screen.findByRole("button", { name: "Eliminar sección Sopa" }));
    expect(onDeleteRecipeSection).toHaveBeenCalledWith("seccion");
    expect(screen.queryByRole("region", { name: "Sopa" })).toBeNull();
    expect(screen.getByRole("region", { name: "Ensalada" })).not.toBeNull();
  });
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
