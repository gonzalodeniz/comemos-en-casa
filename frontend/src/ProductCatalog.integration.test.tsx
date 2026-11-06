// @vitest-environment jsdom
// Comprueba la consulta y la sesión del catálogo mediante interacciones.
import { cleanup, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "./api";
import ProductCatalog from "./ProductCatalog";

afterEach(cleanup);

it("muestra la imagen y el nombre de los productos de la categoría", async () => {
  const usuario = userEvent.setup();
  render(<ProductCatalog onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera", image_url: "/imagen" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  expect(await screen.findByText("Pera")).toBeTruthy();
  expect(document.querySelector('img[src$="/api/v1/imagen"]')).toBeTruthy();
});

it("notifica la expiración de la sesión al fallar la consulta de productos", async () => {
  const usuario = userEvent.setup();
  const expiracion = vi.fn();
  render(<ProductCatalog onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => { throw new ApiError(401, "Sesión caducada"); }} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={expiracion} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  expect(expiracion).toHaveBeenCalledOnce();
});

// Simula un recorte confirmado sin depender de la geometría del navegador de pruebas.
vi.mock("react-easy-crop", () => ({ default: ({ onCropComplete }: { onCropComplete: (area: unknown, pixels: { x: number; y: number; width: number; height: number }) => void }) => <button type="button" onClick={() => onCropComplete({}, { x: 0, y: 0, width: 10, height: 10 })}>Confirmar recorte</button> }));

it("crea una categoría con imagen importada y recortada", async () => {
  const usuario = userEvent.setup();
  const crear = vi.fn().mockResolvedValue(undefined);
  const preparar = vi.fn().mockResolvedValue("token");
  render(<ProductCatalog categories={[]} onGetProducts={vi.fn()} onCreateCategory={crear} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn().mockResolvedValue("data:image/png;base64,YQ==")} onPrepareImage={preparar} />);
  await usuario.click(screen.getByRole("button", { name: "Nueva categoría" }));
  await usuario.type(screen.getByLabelText("Nombre de la categoría"), "Frutas");
  await usuario.type(screen.getByLabelText("URL de imagen"), "https://example.com/imagen.png");
  await usuario.click(screen.getByRole("button", { name: "Importar imagen" }));
  await usuario.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(preparar).toHaveBeenCalledWith("data:image/png;base64,YQ==", { x: 0, y: 0, width: 10, height: 10 });
  expect(crear).toHaveBeenCalledWith("Frutas", "token");
});

it("quita la imagen de una categoría solo al guardar", async () => {
  const usuario = userEvent.setup();
  const actualizar = vi.fn().mockResolvedValue({ id: "1", name: "Frutas" });
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas", image_url: "/imagen" }]} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={actualizar} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Gestionar imagen de Frutas" }));
  await usuario.click(screen.getByLabelText("Quitar imagen actual"));
  expect(actualizar).not.toHaveBeenCalled();
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("1", { remove_image: true });
});

it("crea productos y actualiza su imagen", async () => {
  const usuario = userEvent.setup();
  const consultar = vi.fn().mockResolvedValueOnce([]).mockResolvedValue([{ id: "p", name: "Pera", image_url: "/imagen" }]);
  const crear = vi.fn().mockResolvedValue({ id: "p", name: "Pera" });
  const actualizar = vi.fn().mockResolvedValue({ id: "p", name: "Pera" });
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={consultar} onCreateCategory={vi.fn()} onCreateProduct={crear} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={actualizar} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  await usuario.click(screen.getByRole("button", { name: "Nuevo producto" }));
  await usuario.type(screen.getByLabelText("Nombre del producto"), "Pera");
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(crear).toHaveBeenCalledWith("1", "Pera", undefined);
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  await usuario.click(screen.getByLabelText("Quitar imagen actual"));
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("1", "p", { remove_image: true });
});

it("ofrece reintentar cuando falla la carga de categorías", async () => {
  const usuario = userEvent.setup();
  const reintentar = vi.fn();
  render(<ProductCatalog categories={[]} errorCategorias="Error de carga" onReintentarCategorias={reintentar} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  expect(screen.getByRole("alert").textContent).toContain("Error de carga");
  await usuario.click(screen.getByRole("button", { name: "Reintentar" }));
  expect(reintentar).toHaveBeenCalledOnce();
});

it("conserva la imagen anterior si falla la preparación de la nueva", async () => {
  const usuario = userEvent.setup();
  const actualizar = vi.fn();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas", image_url: "/imagen" }]} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={actualizar} onUpdateProductImage={vi.fn()} onImportImage={vi.fn().mockResolvedValue("data:image/png;base64,YQ==")} onPrepareImage={vi.fn().mockRejectedValue(new Error("fallo"))} />);
  await usuario.click(screen.getByRole("button", { name: "Gestionar imagen de Frutas" }));
  await usuario.type(screen.getByLabelText("URL de imagen"), "https://example.com/imagen.png");
  await usuario.click(screen.getByRole("button", { name: "Importar imagen" }));
  await usuario.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(await screen.findByRole("alert")).toBeTruthy();
  expect(actualizar).not.toHaveBeenCalled();
  expect(document.querySelector('img[src$="/api/v1/imagen"]')).toBeTruthy();
});

it("permite quitar la imagen después de cancelar una importación pendiente", async () => {
  const usuario = userEvent.setup();
  const actualizar = vi.fn().mockResolvedValue({ id: "1", name: "Frutas" });
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas", image_url: "/imagen" }]} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={actualizar} onUpdateProductImage={vi.fn()} onImportImage={() => new Promise(() => {})} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Gestionar imagen de Frutas" }));
  await usuario.type(screen.getByLabelText("URL de imagen"), "https://example.com/imagen.png");
  await usuario.click(screen.getByRole("button", { name: "Importar imagen" }));
  await usuario.click(screen.getByLabelText("Quitar imagen actual"));
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("1", { remove_image: true });
});
