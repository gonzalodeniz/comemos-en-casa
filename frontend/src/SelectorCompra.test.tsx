// @vitest-environment jsdom
// Verifica navegación y respuestas tardías del selector progresivo.
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import SelectorCompra from "./SelectorCompra";

afterEach(cleanup);

// Comprueba que solo se consulta la categoría seleccionada y se puede volver.
it("navega entre categorías y productos", async () => {
  const usuario = userEvent.setup();
  const consultar = vi.fn().mockResolvedValue([{ id: "m", name: "Manzana" }]);
  render(<SelectorCompra categorias={[{ id: "f", name: "Fruta" }, { id: "v", name: "Verdura" }]} consultar={consultar} seleccionar={vi.fn()} />);
  expect(consultar).not.toHaveBeenCalled();
  await usuario.click(screen.getByRole("button", { name: "Fruta" }));
  expect(await screen.findByRole("button", { name: "Manzana" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Verdura" })).toBeNull();
  await usuario.click(screen.getByRole("button", { name: "Volver a categorías" }));
  expect(screen.getByRole("button", { name: "Verdura" })).toBeTruthy();
});

// Impide que una petición tardía reemplace los productos de otra categoría.
it("ignora una respuesta de una categoría abandonada", async () => {
  const usuario = userEvent.setup();
  let resolver: (productos: { id: string; name: string }[]) => void = () => {};
  const consultar = vi.fn().mockImplementation((id: string) => id === "f" ? new Promise((resolve) => { resolver = resolve; }) : Promise.resolve([{ id: "p", name: "Puerro" }]));
  render(<SelectorCompra categorias={[{ id: "f", name: "Fruta" }, { id: "v", name: "Verdura" }]} consultar={consultar} seleccionar={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Fruta" }));
  await usuario.click(screen.getByRole("button", { name: "Volver a categorías" }));
  await usuario.click(screen.getByRole("button", { name: "Verdura" }));
  await screen.findByRole("button", { name: "Puerro" });
  resolver([{ id: "m", name: "Manzana" }]);
  await Promise.resolve();
  expect(screen.queryByRole("button", { name: "Manzana" })).toBeNull();
});
