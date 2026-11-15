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
    await userEvent.setup().click(screen.getByRole("tab", { name: "Recetas" }));
    const seccion = await screen.findByRole("region", { name: "Sopa" });
    expect(within(seccion).getByRole("heading", { name: "Pendientes" })).toBeTruthy();
    expect(within(seccion).getByText("agua")).toBeTruthy();
    expect(within(seccion).getByText("sal")).toBeTruthy();
  });

  // Verifica que las acciones compactas conservan nombre y descripción accesibles.
  it("muestra acciones con iconos y descripción en la lista", async () => {
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={vi.fn()} onCreateProduct={vi.fn()}
      onGetShoppingList={vi.fn().mockResolvedValue({ items: [{ id: "1", product_id: "p", product_name: "Manzana", quantity: 2, unit: "unit", image_url: "/manzana" }] })}
      onMarkPurchased={vi.fn()} onDeleteItem={vi.fn()} />);
    const accion = await screen.findByRole("checkbox", { name: "Marcar Manzana como comprado" });
    expect((accion as HTMLInputElement).checked).toBe(false);
    expect(screen.getByRole("button", { name: "Eliminar Manzana de Pendientes" }).querySelector("svg")).not.toBeNull();
    expect(screen.getByRole("img", { name: "Manzana" }).classList.contains("compra-miniatura")).toBe(true);
  });

  // Comprueba el borrado selectivo y la recuperación ante un fallo parcial.
  it("elimina comprados confirmados y conserva los que fallan", async () => {
    const usuario = userEvent.setup();
    const confirmar = vi.spyOn(window, "confirm").mockReturnValue(true);
    const borrar = vi.fn().mockImplementation((id: string) => id === "fallo" ? Promise.reject(new Error("error")) : Promise.resolve(null));
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={vi.fn()} onCreateProduct={vi.fn()} onDeleteItem={borrar}
      onGetShoppingList={vi.fn().mockResolvedValue({ items: [{ id: "pendiente", product_id: "p", product_name: "Pera", quantity: 1, unit: "unit" }], purchased_items: [
        { id: "ok", product_id: "a", product_name: "Manzana", quantity: 2, unit: "unit" },
        { id: "fallo", product_id: "b", product_name: "Pan", quantity: 1, unit: "unit" },
      ] })} />);
    expect((await screen.findByRole("checkbox", { name: "Desmarcar Manzana como pendiente" }) as HTMLInputElement).checked).toBe(true);
    await usuario.click(screen.getByRole("button", { name: "Eliminar todos los productos comprados" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(borrar).toHaveBeenCalledTimes(2);
    expect(borrar).not.toHaveBeenCalledWith("pendiente");
    expect(screen.queryByText((_, elemento) => elemento?.classList.contains("compra-fila-texto") === true && elemento.textContent === "Manzana: 2 unidad")).toBeNull();
    expect(screen.getByText((_, elemento) => elemento?.classList.contains("compra-fila-texto") === true && elemento.textContent === "Pan: 1 unidad")).toBeTruthy();
    expect(screen.getByText((_, elemento) => elemento?.classList.contains("compra-fila-texto") === true && elemento.textContent === "Pera: 1 unidad")).toBeTruthy();
    confirmar.mockRestore();
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
    await userEvent.setup().click(screen.getByRole("tab", { name: "Recetas" }));
    await user.click(await screen.findByRole("checkbox", { name: "Marcar agua como comprado" }));
    expect(onMarkRecipeIngredient).toHaveBeenCalledWith("agua-1");
    const seccion = screen.getByRole("region", { name: "Sopa" });
    expect(within(seccion).getByRole("heading", { name: "Comprados" })).toBeTruthy();
    expect(within(seccion).getByText("agua")).toBeTruthy();
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
    await userEvent.setup().click(screen.getByRole("tab", { name: "Recetas" }));
    await user.click(await screen.findByRole("checkbox", { name: "Desmarcar agua como comprado" }));
    expect(onUnmarkRecipeIngredient).toHaveBeenCalledWith("agua-1");
    const seccion = screen.getByRole("region", { name: "Sopa" });
    expect(within(seccion).getByRole("heading", { name: "Pendientes" })).toBeTruthy();
    expect(within(seccion).getByText("agua")).toBeTruthy();
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
    await userEvent.setup().click(screen.getByRole("tab", { name: "Recetas" }));
    await user.click(await screen.findByRole("button", { name: "Eliminar agua" }));
    expect(onDeleteRecipeIngredient).toHaveBeenCalledWith("agua-1");
    expect(screen.queryByText("agua")).toBeNull();
    expect(screen.getByText("sal")).not.toBeNull();
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
    await userEvent.setup().click(screen.getByRole("tab", { name: "Recetas" }));
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

// Comprueba la edición de un producto pendiente y la presentación del texto guardado.
it("edita un producto pendiente con texto libre", async () => {
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
  const usuario = userEvent.setup();
  const entrada = { id: "i", product_id: "p", product_name: "Pera", quantity: 2, unit: "unit" };
  const guardar = vi.fn().mockResolvedValue({ ...entrada, quantity_text: "un puñado" });
  render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={vi.fn()} onCreateProduct={vi.fn()} onUpdateShoppingItem={guardar} onGetShoppingList={vi.fn().mockResolvedValue({ items: [entrada] })} />);
  await usuario.click(await screen.findByRole("button", { name: "Editar Pera" }));
  await usuario.click(screen.getByRole("button", { name: "Texto libre" }));
  await usuario.type(screen.getByLabelText("Texto libre", { selector: "input" }), "un puñado");
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(guardar).toHaveBeenCalledWith("i", { quantity_text: "un puñado" });
  expect((await screen.findByRole("button", { name: "Editar Pera" })).textContent).toBe("Pera: un puñado");
});

// Comprueba la separación de las vistas y la pestaña inicial.
it("abre Productos por defecto y separa las recetas", async () => {
  const usuario = userEvent.setup();
  render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={vi.fn()} onCreateProduct={vi.fn()}
    onGetShoppingList={vi.fn().mockResolvedValue({ items: [], recipe_sections: [{ id: "s", name: "Sopa", ingredients: [] }] })} />);
  expect(screen.getByRole("tab", { name: "Productos" }).getAttribute("aria-selected")).toBe("true");
  expect(screen.getByRole("region", { name: "Añadir productos" })).toBeTruthy();
  expect(screen.queryByRole("region", { name: "Sopa" })).toBeNull();
  await usuario.click(screen.getByRole("tab", { name: "Recetas" }));
  expect(await screen.findByRole("region", { name: "Sopa" })).toBeTruthy();
  expect(screen.queryByRole("region", { name: "Añadir productos" })).toBeNull();
  expect(screen.queryByRole("region", { name: "Lista de la compra" })).toBeNull();
});
