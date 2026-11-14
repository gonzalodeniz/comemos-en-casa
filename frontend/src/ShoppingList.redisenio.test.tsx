// @vitest-environment jsdom
// Especifica el recorrido futuro; se activará al implementar las fases 2 y 3.
import { cleanup, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import ShoppingList from "./ShoppingList";

// Simula el diálogo nativo, que jsdom no implementa.
HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
afterEach(() => cleanup());

describe("Rediseño de la lista de la compra", () => {
  // La categoría seleccionada reemplaza al listado y permite volver.
  it("navega de categorías a productos y vuelve", async () => {
    const usuario = userEvent.setup();
    const consultar = vi.fn().mockResolvedValue([{ id: "manzana", name: "Manzana" }]);
    render(<ShoppingList mostrarAdministracion={false} categories={[{ id: "fruta", name: "Fruta" }, { id: "verdura", name: "Verdura" }]}
      onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onGetProducts={consultar} />);

    expect(consultar).not.toHaveBeenCalled();
    await usuario.click(screen.getByRole("button", { name: "Fruta" }));
    expect(consultar).toHaveBeenCalledWith("fruta");
    expect(await screen.findByRole("button", { name: "Manzana" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Verdura" })).toBeNull();
    await usuario.click(screen.getByRole("button", { name: "Volver a categorías" }));
    expect(screen.getByRole("button", { name: "Verdura" })).toBeTruthy();
  });

  // El diálogo envía la cantidad elegida y conserva la categoría tras añadir.
  it("añade un producto desde el diálogo y permanece en la categoría", async () => {
    const usuario = userEvent.setup();
    const agregar = vi.fn().mockResolvedValue({ id: "entrada", product_id: "manzana", product_name: "Manzana", quantity: 1.5, unit: "kg" });
    render(<ShoppingList mostrarAdministracion={false} categories={[{ id: "fruta", name: "Fruta" }]}
      onCreateCategory={vi.fn()} onCreateProduct={vi.fn()}
      onGetProducts={vi.fn().mockResolvedValue([{ id: "manzana", name: "Manzana" }])}
      onAddToShoppingList={agregar} />);

    await usuario.click(screen.getByRole("button", { name: "Fruta" }));
    await usuario.click(await screen.findByRole("button", { name: "Manzana" }));
    const dialogo = screen.getByRole("dialog");
    await usuario.clear(within(dialogo).getByLabelText("Cantidad"));
    await usuario.type(within(dialogo).getByLabelText("Cantidad"), "1.5");
    await usuario.selectOptions(within(dialogo).getByLabelText("Unidad"), "kg");
    await usuario.click(within(dialogo).getByRole("button", { name: "Añadir" }));
    expect(agregar).toHaveBeenCalledWith("manzana", 1.5, "kg");
    expect(await screen.findByRole("button", { name: "Manzana" })).toBeTruthy();
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});
