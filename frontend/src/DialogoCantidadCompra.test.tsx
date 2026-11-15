// @vitest-environment jsdom
// Comprueba el envío, errores y foco del diálogo de cantidades.
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import DialogoCantidadCompra from "./DialogoCantidadCompra";

beforeEach(() => {
  // Simula las operaciones nativas ausentes en jsdom.
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
});
afterEach(() => cleanup());

// Comprueba que la respuesta de la API se transmite sin recalcular cantidades.
it("envía cantidad y unidad y entrega la respuesta del servidor", async () => {
  const usuario = userEvent.setup();
  const entrada = { id: "i", product_id: "m", quantity: 1500, unit: "g" };
  const agregar = vi.fn().mockResolvedValue(entrada);
  const alAgregar = vi.fn();
  const cerrar = vi.fn();
  render(<DialogoCantidadCompra producto={{ id: "m", name: "Manzana" }} agregar={agregar} alAgregar={alAgregar} cerrar={cerrar} />);
  const cantidad = screen.getByLabelText("Unidades", { selector: "input" });
  expect(document.activeElement).toBe(cantidad);
  await usuario.clear(cantidad);
  await usuario.type(cantidad, "1.5");
  await usuario.click(screen.getByRole("button", { name: "Kilogramos" }));
  await usuario.click(screen.getByRole("button", { name: "Añadir" }));
  expect(agregar).toHaveBeenCalledWith("m", 1.5, "kg");
  await waitFor(() => expect(alAgregar).toHaveBeenCalledWith(entrada));
  expect(cerrar).toHaveBeenCalledOnce();
});

// Un fallo conserva los valores y permite volver a enviar.
it("conserva la cantidad cuando falla y permite reintentar", async () => {
  const usuario = userEvent.setup();
  const agregar = vi.fn().mockRejectedValueOnce(new Error("fallo")).mockResolvedValueOnce({ product_id: "m", quantity: 3, unit: "unit" });
  const cerrar = vi.fn();
  render(<DialogoCantidadCompra producto={{ id: "m", name: "Manzana" }} agregar={agregar} alAgregar={vi.fn()} cerrar={cerrar} />);
  const cantidad = screen.getByLabelText("Unidades", { selector: "input" }) as HTMLInputElement;
  await usuario.clear(cantidad);
  await usuario.type(cantidad, "3");
  await usuario.click(screen.getByRole("button", { name: "Añadir" }));
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect(cantidad.value).toBe("3");
  expect(cerrar).not.toHaveBeenCalled();
  await usuario.click(screen.getByRole("button", { name: "Añadir" }));
  await waitFor(() => expect(cerrar).toHaveBeenCalledOnce());
});

// Comprueba que se puede añadir una descripción libre sin cantidad numérica.
it("añade un producto con texto libre", async () => {
  const usuario = userEvent.setup();
  const entrada = { id: "i", product_id: "m", quantity: 0, unit: "unit", quantity_text: "un puñado" };
  const agregar = vi.fn().mockResolvedValue(entrada);
  const alAgregar = vi.fn();
  render(<DialogoCantidadCompra producto={{ id: "m", name: "Manzana" }} agregar={agregar} alAgregar={alAgregar} cerrar={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Texto libre" }));
  await usuario.type(screen.getByLabelText("Texto libre", { selector: "input" }), "un puñado");
  await usuario.click(screen.getByRole("button", { name: "Añadir" }));
  expect(agregar).toHaveBeenCalledWith("m", 0, "unit", "un puñado");
  expect(alAgregar).toHaveBeenCalledWith(entrada);
});
