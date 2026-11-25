// @vitest-environment jsdom
// Verifica navegación y respuestas tardías del selector progresivo.
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import SelectorCompra from "./SelectorCompra";

afterEach(cleanup);

// Comprueba que una búsqueda despliega el selector al alcanzar el umbral.
it("despliega los resultados al escribir tres letras con el selector recogido", async () => {
  const usuario = userEvent.setup();
  const buscar = vi.fn().mockResolvedValue([{ id: "s", name: "Sal fina" }]);
  render(<SelectorCompra categorias={[]} consultar={vi.fn()} buscar={buscar} seleccionar={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Recoger" }));
  const campo = screen.getByRole("textbox", { name: "Buscar productos" });
  await usuario.type(campo, "sa");
  expect(screen.getByRole("button", { name: "Mostrar" }).getAttribute("aria-expanded")).toBe("false");
  await usuario.type(campo, "l");
  expect(screen.getByRole("button", { name: "Recoger" }).getAttribute("aria-expanded")).toBe("true");
  expect(await screen.findByRole("button", { name: "Sal fina" })).toBeTruthy();
});

// Comprueba que los resultados conservan su imagen cuando está disponible.
it("muestra la imagen del producto encontrado", async () => {
  const usuario = userEvent.setup();
  render(<SelectorCompra categorias={[]} consultar={vi.fn()} buscar={vi.fn().mockResolvedValue([{ id: "s", name: "Sal fina", image_url: "/sal.webp" }, { id: "g", name: "Sal gorda" }])} seleccionar={vi.fn()} />);
  await usuario.type(screen.getByRole("textbox", { name: "Buscar productos" }), "sal");
  const fina = await screen.findByRole("button", { name: "Sal fina" });
  expect(fina.querySelector("img")?.getAttribute("src")).toContain("/api/v1/sal.webp");
  expect(screen.getByRole("button", { name: "Sal gorda" }).querySelector("img")).toBeNull();
});

// Comprueba la ayuda del buscador y el retorno al catálogo al limpiarlo.
it("muestra la ayuda y limpia la búsqueda", async () => {
  const usuario = userEvent.setup();
  render(<SelectorCompra categorias={[{ id: "f", name: "Fruta" }]} consultar={vi.fn()} buscar={vi.fn().mockResolvedValue([{ id: "s", name: "Sal" }])} seleccionar={vi.fn()} />);
  const campo = screen.getByPlaceholderText("Busca tus productos") as HTMLInputElement;
  await usuario.type(campo, "sal");
  await screen.findByRole("button", { name: "Sal" });
  await usuario.click(screen.getByRole("button", { name: "Limpiar búsqueda" }));
  expect(campo.value).toBe("");
  expect(screen.getByRole("button", { name: "Fruta" })).toBeTruthy();
});

// Comprueba que el umbral conserva la navegación y muestra resultados globales.
it("mantiene categorías con menos de tres letras y busca en todo el catálogo desde tres", async () => {
  const usuario = userEvent.setup();
  const buscar = vi.fn().mockResolvedValue([{ id: "s", name: "Sal fina" }, { id: "g", name: "Sal gorda" }]);
  render(<SelectorCompra categorias={[{ id: "f", name: "Fruta" }]} consultar={vi.fn().mockResolvedValue([])} buscar={buscar} seleccionar={vi.fn()} />);
  const campo = screen.getByRole("textbox", { name: "Buscar productos" });
  await usuario.type(campo, "sa");
  expect(screen.getByRole("button", { name: "Fruta" })).toBeTruthy();
  expect(buscar).not.toHaveBeenCalled();
  await usuario.type(campo, "l");
  expect(await screen.findByRole("button", { name: "Sal fina" })).toBeTruthy();
  expect(screen.getByRole("button", { name: "Sal gorda" })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Fruta" })).toBeNull();
});

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
