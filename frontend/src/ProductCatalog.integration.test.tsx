// @vitest-environment jsdom
// Comprueba la consulta y la sesión del catálogo mediante interacciones.
import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { ApiError } from "./api";
import ProductCatalog from "./ProductCatalog";

afterEach(cleanup);
beforeEach(() => {
  // Simula el diálogo nativo que jsdom no implementa.
  HTMLDialogElement.prototype.showModal = function () { this.setAttribute("open", ""); };
  HTMLDialogElement.prototype.close = function () { this.removeAttribute("open"); };
});

// Comprueba el traslado desde el modal y la actualización de la categoría de origen.
it("mueve un producto a otra categoría solo al guardar el modal", async () => {
  const usuario = userEvent.setup();
  const pera = { id: "p", name: "Pera" };
  const categorias = [{ id: "1", name: "Frutas" }, { id: "2", name: "Verduras" }];
  let categoriaActual = "1";
  const actualizar = vi.fn(async (_origen: string, _producto: string, cambio: { category_id?: string }) => {
    categoriaActual = cambio.category_id ?? categoriaActual;
    return pera;
  });
  render(<ProductCatalog categories={categorias} onGetProducts={async (id) => id === categoriaActual ? [pera] : []} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={actualizar} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  const abrir = await screen.findByRole("button", { name: "Gestionar imagen de Pera" });
  await usuario.click(abrir);
  let dialogo = within(screen.getByRole("dialog", { name: "Producto Pera" }));
  const categoria = dialogo.getByRole<HTMLSelectElement>("combobox", { name: "Categoría" });
  expect(categoria.value).toBe("1");
  await usuario.selectOptions(categoria, "2");
  await usuario.click(dialogo.getByRole("button", { name: "Cancelar" }));
  expect(actualizar).not.toHaveBeenCalled();

  await usuario.click(abrir);
  dialogo = within(screen.getByRole("dialog", { name: "Producto Pera" }));
  expect(dialogo.getByRole<HTMLSelectElement>("combobox", { name: "Categoría" }).value).toBe("1");
  await usuario.selectOptions(dialogo.getByRole("combobox", { name: "Categoría" }), "2");
  await usuario.click(dialogo.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("1", "p", { name: "Pera", category_id: "2" });
  expect(await screen.findByText("No hay productos en esta categoría.")).toBeTruthy();
  expect(screen.queryByRole("dialog")).toBeNull();
  await usuario.click(screen.getByRole("button", { name: "Volver a categorías" }));
  await usuario.click(screen.getByRole("button", { name: "Verduras" }));
  expect(await screen.findByRole("button", { name: "Gestionar imagen de Pera" })).toBeTruthy();
});

// Comprueba que una búsqueda utiliza la categoría real del producto, no la que está abierta.
it("mueve un resultado de búsqueda a la categoría abierta", async () => {
  const usuario = userEvent.setup();
  const pera = { id: "p", name: "Pera" };
  const buscar = vi.fn().mockResolvedValueOnce({ products: [{ ...pera, category_id: "1" }] })
    .mockResolvedValue({ products: [{ ...pera, category_id: "2" }] });
  const actualizar = vi.fn().mockResolvedValue(pera);
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }, { id: "2", name: "Otros" }]} onGetProducts={async () => []} onSearchProducts={buscar} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={actualizar} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Otros" }));
  await usuario.type(screen.getByRole("textbox", { name: "Buscar productos" }), "per");
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  const dialogo = within(screen.getByRole("dialog", { name: "Producto Pera" }));
  const categoria = dialogo.getByRole<HTMLSelectElement>("combobox", { name: "Categoría" });
  expect(categoria.value).toBe("1");
  await usuario.selectOptions(categoria, "2");
  await usuario.click(dialogo.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("1", "p", { name: "Pera", category_id: "2" });
  expect(buscar).toHaveBeenCalledTimes(2);
  await usuario.click(screen.getByRole("button", { name: "Limpiar búsqueda" }));
  expect(screen.getByRole("button", { name: "Gestionar imagen de Pera" })).toBeTruthy();
});

// Comprueba la búsqueda global, la edición con la categoría del resultado y la limpieza.
it("busca productos en todo el catálogo y permite gestionar el resultado", async () => {
  const usuario = userEvent.setup();
  const buscar = vi.fn().mockResolvedValue({ products: [{ id: "p", category_id: "2", name: "Sal fina", image_url: "/sal.webp" }] });
  const actualizar = vi.fn().mockResolvedValue({ id: "p", name: "Sal gruesa" });
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }, { id: "2", name: "Despensa" }]} onGetProducts={vi.fn().mockResolvedValue([{ id: "m", name: "Manzana" }])} onSearchProducts={buscar} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={actualizar} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  const campo = screen.getByPlaceholderText("Busca tus productos");
  await usuario.type(campo, "sa");
  expect(buscar).not.toHaveBeenCalled();
  expect(screen.getByText("Manzana")).toBeTruthy();
  await usuario.type(campo, "l");
  const resultado = await screen.findByRole("button", { name: "Gestionar imagen de Sal fina" });
  expect(buscar).toHaveBeenCalledWith("sal");
  expect(resultado.querySelector('img[src$="/api/v1/sal.webp"]')).toBeTruthy();
  expect(screen.queryByText("Manzana")).toBeNull();
  await usuario.click(resultado);
  const nombre = screen.getByLabelText("Nombre del producto");
  await usuario.clear(nombre);
  await usuario.type(nombre, "Sal gruesa");
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("2", "p", { name: "Sal gruesa" });
  await usuario.click(screen.getByRole("button", { name: "Limpiar búsqueda" }));
  expect(screen.getByText("Manzana")).toBeTruthy();
});

it("muestra la imagen y el nombre de los productos de la categoría", async () => {
  const usuario = userEvent.setup();
  render(<ProductCatalog onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera", image_url: "/imagen" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  expect(await screen.findByText("Pera")).toBeTruthy();
  expect(document.querySelector('img[src$="/api/v1/imagen"]')).toBeTruthy();
});

// Comprueba que el nombre se edita sin exigir un cambio de imagen.
it("renombra un producto sin modificar su imagen", async () => {
  const usuario = userEvent.setup();
  const actualizar = vi.fn().mockResolvedValue({ id: "p", name: "Pera conferencia", image_url: "/imagen" });
  render(<ProductCatalog onUpdateCategoryImage={vi.fn()} onUpdateProductImage={actualizar} onImportImage={vi.fn()} onPrepareImage={vi.fn()} categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera", image_url: "/imagen" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  expect(screen.getByRole("dialog", { name: "Producto Pera" })).toBeTruthy();
  const nombre = screen.getByLabelText("Nombre del producto");
  await usuario.clear(nombre);
  await usuario.type(nombre, "Pera conferencia");
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("1", "p", { name: "Pera conferencia" });
  expect(await screen.findByText("Pera conferencia")).toBeTruthy();
});

// Comprueba la edición del nombre de una categoría sin modificar su imagen.
it("renombra una categoría desde el catálogo", async () => {
  const usuario = userEvent.setup();
  const actualizar = vi.fn().mockResolvedValue({ id: "1", name: "Fruta fresca", image_url: "/imagen" });
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas", image_url: "/imagen" }]} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={actualizar} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Editar categoría Frutas" }));
  const nombre = screen.getByLabelText("Nombre de la categoría");
  expect((nombre as HTMLInputElement).value).toBe("Frutas");
  await usuario.clear(nombre);
  await usuario.type(nombre, "Fruta fresca");
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("1", { name: "Fruta fresca" });
});

// Comprueba que la edición de categoría se presenta como ventana modal.
it("abre la edición de categoría en un diálogo modal", async () => {
  const usuario = userEvent.setup();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas", image_url: "/imagen" }]} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Editar categoría Frutas" }));
  expect(screen.getByRole("dialog", { name: "Categoría Frutas" })).toBeTruthy();
});

// Comprueba que el error de duplicidad se muestra sin cerrar el editor.
it("avisa al intentar renombrar una categoría con un nombre duplicado", async () => {
  const usuario = userEvent.setup();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn().mockRejectedValue(new ApiError(409, "Duplicate"))} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Editar categoría Frutas" }));
  await usuario.clear(screen.getByLabelText("Nombre de la categoría"));
  await usuario.type(screen.getByLabelText("Nombre de la categoría"), "Verduras");
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect((await screen.findByRole("alert")).textContent).toBe("Ya existe una categoría con ese nombre.");
  expect((screen.getByLabelText("Nombre de la categoría") as HTMLInputElement).value).toBe("Verduras");
});

// Comprueba que cancelar descarta el nombre escrito.
it("cancela la edición del nombre de una categoría", async () => {
  const usuario = userEvent.setup();
  const actualizar = vi.fn();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={actualizar} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Editar categoría Frutas" }));
  await usuario.clear(screen.getByLabelText("Nombre de la categoría"));
  await usuario.type(screen.getByLabelText("Nombre de la categoría"), "Verduras");
  await usuario.click(screen.getByRole("button", { name: "Cancelar" }));
  expect(actualizar).not.toHaveBeenCalled();
  expect(screen.getByRole("button", { name: "Frutas" })).toBeTruthy();
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
  const dialogo = within(screen.getByRole("dialog", { name: "Nueva categoría" }));
  await usuario.type(dialogo.getByLabelText("Nombre de la categoría"), "Frutas");
  await usuario.type(screen.getByLabelText("URL de imagen"), "https://example.com/imagen.png");
  await usuario.click(screen.getByRole("button", { name: "Importar imagen" }));
  await usuario.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(preparar).toHaveBeenCalledWith("data:image/png;base64,YQ==", { x: 0, y: 0, width: 10, height: 10 });
  expect(crear).toHaveBeenCalledWith("Frutas", "token");
  expect(screen.queryByRole("dialog")).toBeNull();
});

// Comprueba el error dentro del modal y que el cierre descarta el borrador.
it("mantiene el formulario en el modal si falla la creación y permite descartarlo", async () => {
  const usuario = userEvent.setup();
  const crear = vi.fn().mockRejectedValue(new ApiError(409, "Duplicate"));
  render(<ProductCatalog categories={[]} onGetProducts={vi.fn()} onCreateCategory={crear} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  const abrir = screen.getByRole("button", { name: "Nueva categoría" });
  await usuario.click(abrir);
  const ventana = screen.getByRole("dialog", { name: "Nueva categoría" });
  const dialogo = within(ventana);
  const nombre = dialogo.getByLabelText<HTMLInputElement>("Nombre de la categoría");
  await usuario.type(nombre, "Frutas");
  await usuario.click(dialogo.getByRole("button", { name: "Guardar" }));
  expect((await dialogo.findByRole("alert")).textContent).toBe("Ya existe una categoría con ese nombre.");
  expect(nombre.value).toBe("Frutas");

  // jsdom no genera el evento nativo de cierre al pulsar Escape.
  fireEvent(ventana, new Event("cancel", { cancelable: true }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(document.activeElement).toBe(abrir);

  await usuario.click(abrir);
  const reabierto = within(screen.getByRole("dialog", { name: "Nueva categoría" }));
  expect(reabierto.getByLabelText<HTMLInputElement>("Nombre de la categoría").value).toBe("");
  await usuario.click(reabierto.getByRole("button", { name: "Cancelar" }));
  expect(screen.queryByRole("dialog")).toBeNull();
  expect(crear).toHaveBeenCalledOnce();
});

it("quita la imagen de una categoría solo al guardar", async () => {
  const usuario = userEvent.setup();
  const actualizar = vi.fn().mockResolvedValue({ id: "1", name: "Frutas" });
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas", image_url: "/imagen" }]} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={actualizar} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} />);
  await usuario.click(screen.getByRole("button", { name: "Editar categoría Frutas" }));
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
  expect(actualizar).toHaveBeenCalledWith("1", "p", { name: "Pera", remove_image: true });
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
  await usuario.click(screen.getByRole("button", { name: "Editar categoría Frutas" }));
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
  await usuario.click(screen.getByRole("button", { name: "Editar categoría Frutas" }));
  await usuario.type(screen.getByLabelText("URL de imagen"), "https://example.com/imagen.png");
  await usuario.click(screen.getByRole("button", { name: "Importar imagen" }));
  await usuario.click(screen.getByLabelText("Quitar imagen actual"));
  await usuario.click(screen.getByRole("button", { name: "Guardar" }));
  expect(actualizar).toHaveBeenCalledWith("1", { remove_image: true });
});

// Comprueba el aviso cuando el producto aparece en la lista de compra.
it("avisa en la confirmación cuando el producto está en la lista", async () => {
  const usuario = userEvent.setup();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} onConsultarUso={async () => true} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  await usuario.click(screen.getByRole("button", { name: "Borrar producto" }));
  expect(await screen.findByText(/está en la lista de la compra/i)).toBeTruthy();
});

// Comprueba el aviso cuando el producto no aparece en la lista.
it("avisa en la confirmación cuando el producto no está en la lista", async () => {
  const usuario = userEvent.setup();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} onConsultarUso={async () => false} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  await usuario.click(screen.getByRole("button", { name: "Borrar producto" }));
  expect(await screen.findByText(/no está en la lista de la compra/i)).toBeTruthy();
});

// Comprueba que cancelar la confirmación no elimina el producto.
it("cancela el borrado sin modificar el catálogo", async () => {
  const usuario = userEvent.setup();
  const borrar = vi.fn();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} onConsultarUso={async () => true} onBorrarProducto={borrar} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  await usuario.click(screen.getByRole("button", { name: "Borrar producto" }));
  await usuario.click(await screen.findByRole("button", { name: "No borrar" }));
  expect(borrar).not.toHaveBeenCalled();
  expect(screen.getByRole("dialog", { name: "Producto Pera" })).toBeTruthy();
});

// Comprueba el borrado confirmado y la actualización del catálogo.
it("confirma el borrado y actualiza el catálogo", async () => {
  const usuario = userEvent.setup();
  const borrar = vi.fn().mockResolvedValue(undefined);
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} onConsultarUso={async () => true} onBorrarProducto={borrar} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  await usuario.click(screen.getByRole("button", { name: "Borrar producto" }));
  await usuario.click(await screen.findByRole("button", { name: "Confirmar borrado" }));
  expect(borrar).toHaveBeenCalledWith("1", "p");
  expect(await screen.findByText("No hay productos en esta categoría.")).toBeTruthy();
});

// Comprueba que las acciones del editor de producto son iconos accesibles.
it("muestra acciones con iconos en la edición de producto", async () => {
  const usuario = userEvent.setup();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} onConsultarUso={async () => false} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  for (const nombre of ["Guardar", "Cancelar", "Borrar producto"]) {
    const boton = screen.getByRole("button", { name: nombre });
    expect(boton.querySelector("svg")).toBeTruthy();
    expect(boton.textContent).toBe("");
  }
});

// Comprueba las acciones iconográficas y su exclusividad durante la confirmación.
it("sustituye temporalmente guardar y cancelar por iconos de confirmación", async () => {
  const usuario = userEvent.setup();
  render(<ProductCatalog categories={[{ id: "1", name: "Frutas" }]} onGetProducts={async () => [{ id: "p", name: "Pera" }]} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} onSessionExpired={vi.fn()} onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} onConsultarUso={async () => false} />);
  await usuario.click(screen.getByRole("button", { name: "Frutas" }));
  await usuario.click(await screen.findByRole("button", { name: "Gestionar imagen de Pera" }));
  await usuario.click(screen.getByRole("button", { name: "Borrar producto" }));
  expect(screen.queryByRole("button", { name: "Guardar" })).toBeNull();
  expect(screen.queryByRole("button", { name: "Cancelar" })).toBeNull();
  for (const nombre of ["Confirmar borrado", "No borrar"]) expect(screen.getByRole("button", { name: nombre }).querySelector("svg")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Confirmar borrado" }).parentElement).toBe(screen.getByRole("button", { name: "No borrar" }).parentElement);
});
