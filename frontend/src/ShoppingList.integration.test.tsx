// @vitest-environment jsdom
// Comprueba los flujos de la lista de compra desde la interfaz con la API simulada.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import ShoppingList from "./ShoppingList";

vi.mock("react-easy-crop", () => ({ default: ({ onCropComplete }: { onCropComplete: (area: unknown, pixels: { x: number; y: number; width: number; height: number }) => void }) => <button type="button" onClick={() => onCropComplete({}, { x: 1, y: 2, width: 8, height: 8 })}>Confirmar recorte</button> }));

vi.mock("./MealPlanning", () => ({ default: () => <div>Plan semanal</div> }));

afterEach(() => { cleanup(); vi.unstubAllGlobals(); sessionStorage.clear(); });

describe("shopping list integration", () => {
  it("does_not_remove_category_image_while_replacement_import_is_pending", async () => {
    const actualizar = vi.fn();
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta", image_url: "/old" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} onImportImage={() => new Promise(() => {})} onUpdateCategoryImage={actualizar} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Fruta" }));
    await user.type(screen.getByLabelText("URL de imagen de Fruta"), "https://example.com/fruit.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen de Fruta" }));
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Fruta" }));
    expect(actualizar).not.toHaveBeenCalled();
    expect((await screen.findByRole("alert")).textContent).toContain("Espera a que la imagen esté lista");
  });

  it("does_not_remove_product_image_while_replacement_import_is_pending", async () => {
    const actualizar = vi.fn();
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana", image_url: "/old" }]} onCreateProduct={vi.fn()} onImportImage={() => new Promise(() => {})} onUpdateProductImage={actualizar} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Manzana" }));
    await user.type(screen.getByLabelText("URL de imagen de Manzana"), "https://example.com/apple.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen de Manzana" }));
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Manzana" }));
    expect(actualizar).not.toHaveBeenCalled();
    expect((await screen.findByRole("alert")).textContent).toContain("Espera a que la imagen esté lista");
  });

  it("shows_error_for_non_image_dropped_on_product", async () => {
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    const zona = screen.getByLabelText("Imagen del producto").closest("label")!;
    fireEvent.drop(zona, { dataTransfer: { files: [new File(["text"], "nota.txt", { type: "text/plain" })] } });
    expect((await screen.findByRole("alert")).textContent).toContain("Selecciona una imagen válida");
  });

  it("waits_for_url_import_before_creating_product", async () => {
    const crear = vi.fn();
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={crear} onImportImage={() => new Promise(() => {})} />);
    await user.type(screen.getByLabelText("URL de imagen del producto"), "https://example.com/apple.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen" }));
    await user.type(screen.getByLabelText("Nombre del producto en Fruta"), "Manzana");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));
    expect(crear).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toContain("Espera a que la imagen esté lista");
  });

  it("keeps_latest_image_when_url_imports_finish_out_of_order", async () => {
    const pendientes: ((value: string) => void)[] = [];
    const importar = vi.fn().mockImplementation(() => new Promise<string>((resolve) => pendientes.push(resolve)));
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} onImportImage={importar} />);
    const url = screen.getByLabelText("URL de imagen del producto");
    await user.type(url, "https://example.com/first.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen" }));
    await user.clear(url);
    await user.type(url, "https://example.com/second.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen" }));
    await act(async () => pendientes[1]("data:image/png;base64,c2Vjb25k"));
    await screen.findByRole("img", { name: "Vista previa del producto" });
    await act(async () => pendientes[0]("data:image/png;base64,Zmlyc3Q="));
    expect(screen.getByRole("img", { name: "Vista previa del producto" }).getAttribute("src")).toBe("data:image/png;base64,c2Vjb25k");
  });

  it("keeps_latest_image_when_file_reads_finish_out_of_order", async () => {
    const lectores: { onload: (() => void) | null; result: string; readAsDataURL: () => void }[] = [];
    vi.stubGlobal("FileReader", class {
      onload: (() => void) | null = null;
      result = "";
      constructor() { lectores.push(this); }
      readAsDataURL() {}
    });
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }, { id: "verdura", name: "Verdura" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    const inputs = screen.getAllByLabelText("Imagen del producto");
    await user.upload(inputs[0], new File(["first"], "first.png", { type: "image/png" }));
    await user.upload(inputs[1], new File(["second"], "second.png", { type: "image/png" }));
    lectores[1].result = "data:image/png;base64,c2Vjb25k";
    await act(async () => lectores[1].onload?.());
    await screen.findByRole("img", { name: "Vista previa del producto" });
    lectores[0].result = "data:image/png;base64,Zmlyc3Q=";
    await act(async () => lectores[0].onload?.());
    await waitFor(() => expect(screen.getByRole("img", { name: "Vista previa del producto" }).getAttribute("src")).toBe("data:image/png;base64,c2Vjb25k"));
  });

  it("keeps_category_image_when_creation_fails", async () => {
    const crear = vi.fn().mockRejectedValue(new Error("error"));
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={crear} onGetProducts={async () => []} onCreateProduct={vi.fn()} onPrepareImage={vi.fn().mockResolvedValue("image-token")} />);
    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.type(screen.getByLabelText("Nombre de la categoría"), "Fruta");
    await user.click(screen.getByRole("button", { name: "Crear categoría" }));
    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo crear la categoría");
    expect(screen.getByRole("img", { name: "Vista previa de la categoría" })).toBeTruthy();
  });

  it("clears_category_image_only_after_successful_creation", async () => {
    const crear = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={crear} onGetProducts={async () => []} onCreateProduct={vi.fn()} onPrepareImage={vi.fn().mockResolvedValue("image-token")} />);
    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.type(screen.getByLabelText("Nombre de la categoría"), "Fruta");
    await user.click(screen.getByRole("button", { name: "Crear categoría" }));
    await waitFor(() => expect(crear).toHaveBeenCalledWith("Fruta", "image-token"));
    await waitFor(() => expect(screen.queryByRole("img", { name: "Vista previa de la categoría" })).toBeNull());
  });

  it("does_not_reuse_image_when_creating_next_product", async () => {
    const crear = vi.fn().mockResolvedValueOnce({ id: "manzana", name: "Manzana" }).mockResolvedValueOnce({ id: "pera", name: "Pera" });
    const preparar = vi.fn().mockResolvedValue("image-token");
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={crear} onPrepareImage={preparar} />);
    await user.upload(screen.getByLabelText("Imagen del producto"), new File(["image"], "apple.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.type(screen.getByLabelText("Nombre del producto en Fruta"), "Manzana");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));
    await waitFor(() => expect(crear).toHaveBeenCalledTimes(1));
    await user.type(screen.getByLabelText("Nombre del producto en Fruta"), "Pera");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));
    await waitFor(() => expect(crear).toHaveBeenNthCalledWith(2, "fruta", "Pera"));
    expect(preparar).toHaveBeenCalledTimes(1);
  });

  it("renders_category_cropper_in_positioned_crop_area", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));
    await screen.findByRole("img", { name: "Vista previa de la categoría" });
    expect(screen.getByLabelText("Recortar imagen").classList.contains("crop-area")).toBe(true);
  });

  it("renders_product_cropper_in_positioned_crop_area", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    await user.upload(screen.getByLabelText("Imagen del producto"), new File(["image"], "apple.png", { type: "image/png" }));
    await screen.findByRole("img", { name: "Vista previa del producto" });
    expect(screen.getByLabelText("Recortar imagen").classList.contains("crop-area")).toBe(true);
  });

  it("keeps_category_image_and_shows_error_when_edit_import_fails", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta", image_url: "/old" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} onImportImage={vi.fn().mockRejectedValue(new Error("error"))} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    await user.type(screen.getByLabelText("URL de imagen de Fruta"), "https://example.com/fruit.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen de Fruta" }));
    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo importar la imagen");
    expect(screen.getByRole("img", { name: "Fruta" }).getAttribute("src")).toBe("/comemos/api/v1/old");
  });

  it("keeps_product_image_and_shows_error_when_edit_import_fails", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana", image_url: "/old" }]} onCreateProduct={vi.fn()} onImportImage={vi.fn().mockRejectedValue(new Error("error"))} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.type(screen.getByLabelText("URL de imagen de Manzana"), "https://example.com/apple.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen de Manzana" }));
    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo importar la imagen");
    expect(screen.getByRole("img", { name: "Manzana" }).getAttribute("src")).toBe("/comemos/api/v1/old");
  });

  it("indicates_category_image_removal_is_pending", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta", image_url: "/old" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Fruta" }));
    expect(screen.getByText("La imagen se quitará al guardar.")).toBeTruthy();
  });

  it("indicates_product_image_removal_is_pending", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana", image_url: "/old" }]} onCreateProduct={vi.fn()} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Manzana" }));
    expect(screen.getByText("La imagen se quitará al guardar.")).toBeTruthy();
  });

  it("replaces_product_image_when_url_import_follows_removal", async () => {
    const actualizar = vi.fn().mockResolvedValue({ id: "manzana", name: "Manzana", image_url: "/new" });
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana", image_url: "/old" }]} onCreateProduct={vi.fn()} onImportImage={vi.fn().mockResolvedValue("data:image/png;base64,aW1hZ2U=")} onPrepareImage={vi.fn().mockResolvedValue("image-token")} onUpdateProductImage={actualizar} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Manzana" }));
    await user.type(screen.getByLabelText("URL de imagen de Manzana"), "https://example.com/apple.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen de Manzana" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Manzana" }));
    await waitFor(() => expect(actualizar).toHaveBeenCalledWith("fruta", "manzana", { image_token: "image-token" }));
  });

  it("replaces_category_image_when_new_selection_follows_removal", async () => {
    const actualizar = vi.fn().mockResolvedValue({ id: "fruta", name: "Fruta", image_url: "/new" });
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta", image_url: "/old" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} onPrepareImage={vi.fn().mockResolvedValue("image-token")} onUpdateCategoryImage={actualizar} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Fruta" }));
    await user.upload(screen.getByLabelText("Imagen de Fruta"), new File(["image"], "fruit.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Fruta" }));
    await waitFor(() => expect(actualizar).toHaveBeenCalledWith("fruta", { image_token: "image-token" }));
  });

  it("replaces_product_image_when_new_selection_follows_removal", async () => {
    const actualizar = vi.fn().mockResolvedValue({ id: "manzana", name: "Manzana", image_url: "/new" });
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana", image_url: "/old" }]} onCreateProduct={vi.fn()} onPrepareImage={vi.fn().mockResolvedValue("image-token")} onUpdateProductImage={actualizar} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Manzana" }));
    await user.upload(screen.getByLabelText("Imagen de Manzana"), new File(["image"], "apple.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Manzana" }));
    await waitFor(() => expect(actualizar).toHaveBeenCalledWith("fruta", "manzana", { image_token: "image-token" }));
  });

  it("previews_existing_category_image_after_url_import", async () => {
    const user = userEvent.setup();
    const importar = vi.fn().mockResolvedValue("data:image/png;base64,aW1hZ2U=");
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} onImportImage={importar} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    await user.type(screen.getByLabelText("URL de imagen de Fruta"), "https://example.com/fruit.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen de Fruta" }));
    expect(importar).toHaveBeenCalledWith("https://example.com/fruit.png");
    expect(await screen.findByRole("img", { name: "Vista previa de Fruta" })).toBeTruthy();
  });

  it("previews_existing_category_image_after_paste", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    const zona = screen.getByLabelText("Imagen de Fruta").closest("label")!;
    fireEvent.paste(zona, { clipboardData: { files: [new File(["image"], "fruit.png", { type: "image/png" })] } });
    expect(await screen.findByRole("img", { name: "Vista previa de Fruta" })).toBeTruthy();
  });

  it("previews_existing_category_image_after_drop", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    const zona = screen.getByLabelText("Imagen de Fruta").closest("label")!;
    fireEvent.drop(zona, { dataTransfer: { files: [new File(["image"], "fruit.png", { type: "image/png" })] } });
    expect(await screen.findByRole("img", { name: "Vista previa de Fruta" })).toBeTruthy();
  });

  it("previews_existing_product_image_after_url_import", async () => {
    const user = userEvent.setup();
    const importar = vi.fn().mockResolvedValue("data:image/png;base64,aW1hZ2U=");
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana" }]} onCreateProduct={vi.fn()} onImportImage={importar} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.type(screen.getByLabelText("URL de imagen de Manzana"), "https://example.com/apple.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen de Manzana" }));
    expect(importar).toHaveBeenCalledWith("https://example.com/apple.png");
    expect(await screen.findByRole("img", { name: "Vista previa de Manzana" })).toBeTruthy();
  });

  it("previews_existing_product_image_after_paste", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana" }]} onCreateProduct={vi.fn()} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    const zona = screen.getByLabelText("Imagen de Manzana").closest("label")!;
    fireEvent.paste(zona, { clipboardData: { files: [new File(["image"], "apple.png", { type: "image/png" })] } });
    expect(await screen.findByRole("img", { name: "Vista previa de Manzana" })).toBeTruthy();
  });

  it("previews_existing_product_image_after_drop", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana" }]} onCreateProduct={vi.fn()} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    const zona = screen.getByLabelText("Imagen de Manzana").closest("label")!;
    fireEvent.drop(zona, { dataTransfer: { files: [new File(["image"], "apple.png", { type: "image/png" })] } });
    expect(await screen.findByRole("img", { name: "Vista previa de Manzana" })).toBeTruthy();
  });

  it("removes_existing_category_image", async () => {
    const actualizar = vi.fn().mockResolvedValue({ id: "fruta", name: "Fruta", image_url: null });
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta", image_url: "/fruit" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} onUpdateCategoryImage={actualizar} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Fruta" }));
    expect(actualizar).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Fruta" }));
    await waitFor(() => expect(actualizar).toHaveBeenCalledWith("fruta", { remove_image: true }));
  });

  it("saves_existing_category_image_with_prepared_token", async () => {
    const actualizar = vi.fn().mockResolvedValue({ id: "fruta", name: "Fruta", image_url: "/new-image" });
    const preparar = vi.fn().mockResolvedValue("image-token");
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} onPrepareImage={preparar} onUpdateCategoryImage={actualizar} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    await user.upload(screen.getByLabelText("Imagen de Fruta"), new File(["image"], "fruit.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Fruta" }));
    await waitFor(() => expect(actualizar).toHaveBeenCalledWith("fruta", { image_token: "image-token" }));
  });

  it("previews_and_crops_existing_category_image", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    await user.upload(screen.getByLabelText("Imagen de Fruta"), new File(["image"], "fruit.png", { type: "image/png" }));
    expect(await screen.findByRole("img", { name: "Vista previa de Fruta" })).toBeTruthy();
    expect(screen.getByRole("slider", { name: "Zoom de Fruta" })).toBeTruthy();
  });

  it("opens_existing_category_image_controls", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    await user.click(screen.getByRole("button", { name: "Gestionar imagen de Fruta" }));
    expect(screen.getByLabelText("Imagen de Fruta")).toBeTruthy();
  });

  it("removes_existing_product_image", async () => {
    const actualizar = vi.fn().mockResolvedValue({ id: "manzana", name: "Manzana", image_url: null });
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana", image_url: "/apple" }]} onCreateProduct={vi.fn()} onUpdateProductImage={actualizar} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.click(screen.getByRole("button", { name: "Quitar imagen de Manzana" }));
    expect(actualizar).not.toHaveBeenCalled();
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Manzana" }));
    await waitFor(() => expect(actualizar).toHaveBeenCalledWith("fruta", "manzana", { remove_image: true }));
    expect(screen.queryByRole("img", { name: "Manzana" })).toBeNull();
  });

  it("saves_existing_product_image_with_prepared_token", async () => {
    const actualizar = vi.fn().mockResolvedValue({ id: "manzana", name: "Manzana", image_url: "/new-image" });
    const preparar = vi.fn().mockResolvedValue("image-token");
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana" }]} onCreateProduct={vi.fn()} onPrepareImage={preparar} onUpdateProductImage={actualizar} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.upload(screen.getByLabelText("Imagen de Manzana"), new File(["image"], "apple.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Manzana" }));
    await waitFor(() => expect(actualizar).toHaveBeenCalledWith("fruta", "manzana", { image_token: "image-token" }));
  });

  it("shows_replaced_product_image_in_existing_shopping_list_entry", async () => {
    const user = userEvent.setup();
    const actualizar = vi.fn().mockResolvedValue({ id: "manzana", name: "Manzana", image_url: "/new-image" });
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana", image_url: "/old-image" }]} onCreateProduct={vi.fn()} onPrepareImage={vi.fn().mockResolvedValue("image-token")} onUpdateProductImage={actualizar} onGetShoppingList={async () => ({ items: [{ id: "item", product_id: "manzana", image_url: "/old-image", quantity: 1, unit: "unit" }] })} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.upload(screen.getByLabelText("Imagen de Manzana"), new File(["image"], "apple.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.click(screen.getByRole("button", { name: "Guardar imagen de Manzana" }));
    const lista = screen.getByRole("region", { name: "Lista de la compra" });
    await waitFor(() => expect(within(lista).getByRole("img", { name: "Manzana" }).getAttribute("src")).toContain("/new-image"));
  });

  it("previews_and_crops_existing_product_image", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana" }]} onCreateProduct={vi.fn()} />);
    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));
    await user.upload(screen.getByLabelText("Imagen de Manzana"), new File(["image"], "apple.png", { type: "image/png" }));
    expect(await screen.findByRole("img", { name: "Vista previa de Manzana" })).toBeTruthy();
    expect(screen.getByRole("slider", { name: "Zoom de Manzana" })).toBeTruthy();
  });

  it("opens_existing_product_image_controls", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={vi.fn()} onGetProducts={async () => [{ id: "manzana", name: "Manzana" }]} onCreateProduct={vi.fn()} />);

    await user.click(await screen.findByRole("button", { name: "Gestionar imagen de Manzana" }));

    expect(screen.getByLabelText("Imagen de Manzana")).toBeTruthy();
  });

  it("shows_category_image_preview_after_url_import", async () => {
    const importar = vi.fn().mockResolvedValue("data:image/png;base64,aW1hZ2U=");
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} onImportImage={importar} />);
    await user.type(screen.getByLabelText("URL de imagen de la categoría"), "https://example.com/fruit.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen de categoría" }));
    expect(importar).toHaveBeenCalledWith("https://example.com/fruit.png");
    expect((await screen.findByRole("img", { name: "Vista previa de la categoría" })).getAttribute("src")).toBe("data:image/png;base64,aW1hZ2U=");
  });

  it("shows_category_image_preview_after_paste", async () => {
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    const zona = screen.getByLabelText("Imagen de la categoría").closest("label")!;
    fireEvent.paste(zona, { clipboardData: { files: [new File(["image"], "fruit.png", { type: "image/png" })] } });
    expect(await screen.findByRole("img", { name: "Vista previa de la categoría" })).toBeTruthy();
  });

  it("shows_category_image_preview_after_drop", async () => {
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    const zona = screen.getByLabelText("Imagen de la categoría").closest("label")!;
    fireEvent.drop(zona, { dataTransfer: { files: [new File(["image"], "fruit.png", { type: "image/png" })] } });
    expect(await screen.findByRole("img", { name: "Vista previa de la categoría" })).toBeTruthy();
  });

  it("shows_error_when_category_image_preparation_fails", async () => {
    const crear = vi.fn();
    const preparar = vi.fn().mockRejectedValue(new Error("Invalid image"));
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={crear} onGetProducts={async () => []} onCreateProduct={vi.fn()} onPrepareImage={preparar} />);

    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.type(screen.getByLabelText("Nombre de la categoría"), "Fruta");
    await user.click(screen.getByRole("button", { name: "Crear categoría" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo preparar la imagen");
    expect(crear).not.toHaveBeenCalled();
  });

  it("shows_error_when_category_image_file_cannot_be_read", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("FileReader", class {
      onerror: (() => void) | null = null;
      readAsDataURL() { this.onerror?.(); }
    });
    render(<ShoppingList categories={[]} onCreateCategory={vi.fn()} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);

    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo leer la imagen");
  });

  it("waits_for_category_image_file_read_before_creating", async () => {
    const crear = vi.fn();
    const user = userEvent.setup();
    vi.stubGlobal("FileReader", class { readAsDataURL() {} });
    render(<ShoppingList categories={[]} onCreateCategory={crear} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);

    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));
    await user.type(screen.getByLabelText("Nombre de la categoría"), "Fruta");
    await user.click(screen.getByRole("button", { name: "Crear categoría" }));

    expect(crear).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toContain("Espera a que la imagen esté lista");
  });

  it("waits_for_category_crop_before_creating", async () => {
    const crear = vi.fn();
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={crear} onGetProducts={async () => []} onCreateProduct={vi.fn()} onPrepareImage={vi.fn()} />);

    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));
    await screen.findByRole("img", { name: "Vista previa de la categoría" });
    await user.type(screen.getByLabelText("Nombre de la categoría"), "Fruta");
    await user.click(screen.getByRole("button", { name: "Crear categoría" }));

    expect(crear).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toContain("Espera a que la imagen esté lista");
  });

  it("creates_category_with_prepared_image_token", async () => {
    const crear = vi.fn();
    const preparar = vi.fn().mockResolvedValue("category-image-token");
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={crear} onGetProducts={async () => []} onCreateProduct={vi.fn()} onPrepareImage={preparar} />);

    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.type(screen.getByLabelText("Nombre de la categoría"), "Fruta");
    await user.click(screen.getByRole("button", { name: "Crear categoría" }));

    await waitFor(() => expect(crear).toHaveBeenCalledWith("Fruta", "category-image-token"));
  });

  it("shows_category_image_file_picker_and_crop_preview", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);

    await user.upload(screen.getByLabelText("Imagen de la categoría"), new File(["image"], "fruit.png", { type: "image/png" }));

    expect(await screen.findByRole("img", { name: "Vista previa de la categoría" })).toBeTruthy();
    expect(screen.getByRole("slider", { name: "Zoom" })).toBeTruthy();
  });

  it("shows_error_when_product_image_url_import_fails", async () => {
    const importar = vi.fn().mockRejectedValue(new Error("Import failed"));
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={vi.fn()} onImportImage={importar} />);

    await user.type(screen.getByLabelText("URL de imagen del producto"), "https://example.com/apple.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo importar la imagen");
    expect(screen.queryByRole("img", { name: "Vista previa del producto" })).toBeNull();
  });

  it("shows_product_image_preview_after_url_import", async () => {
    const importar = vi.fn().mockResolvedValue("data:image/png;base64,aW1hZ2U=");
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={vi.fn()} onImportImage={importar} />);

    await user.type(screen.getByLabelText("URL de imagen del producto"), "https://example.com/apple.png");
    await user.click(screen.getByRole("button", { name: "Importar imagen" }));

    expect(importar).toHaveBeenCalledWith("https://example.com/apple.png");
    expect((await screen.findByRole("img", { name: "Vista previa del producto" })).getAttribute("src")).toBe("data:image/png;base64,aW1hZ2U=");
  });

  it("shows_product_image_preview_after_paste", async () => {
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    const zona = screen.getByLabelText("Imagen del producto").closest("label")!;

    fireEvent.paste(zona, { clipboardData: { files: [new File(["image"], "apple.png", { type: "image/png" })] } });

    expect(await screen.findByRole("img", { name: "Vista previa del producto" })).toBeTruthy();
  });

  it("shows_product_image_preview_after_drop", async () => {
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);
    const zona = screen.getByLabelText("Imagen del producto").closest("label")!;

    fireEvent.drop(zona, { dataTransfer: { files: [new File(["image"], "apple.png", { type: "image/png" })] } });

    expect(await screen.findByRole("img", { name: "Vista previa del producto" })).toBeTruthy();
  });

  it("keeps_product_image_preview_in_selected_category_form", async () => {
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "fruta", name: "Fruta" }, { id: "verdura", name: "Verdura" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);

    await user.upload(screen.getAllByLabelText("Imagen del producto")[0], new File(["image"], "apple.png", { type: "image/png" }));

    expect(await screen.findAllByRole("img", { name: "Vista previa del producto" })).toHaveLength(1);
  });

  it("shows_error_when_product_image_preparation_fails", async () => {
    const crear = vi.fn();
    const preparar = vi.fn().mockRejectedValue(new Error("Invalid image"));
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "category-1", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={crear} onPrepareImage={preparar} />);

    await user.upload(screen.getByLabelText("Imagen del producto"), new File(["image"], "apple.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.type(screen.getByLabelText("Nombre del producto en Fruta"), "Manzana");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo preparar la imagen");
    expect(crear).not.toHaveBeenCalled();
  });

  it("shows_error_when_product_image_file_cannot_be_read", async () => {
    const user = userEvent.setup();
    vi.stubGlobal("FileReader", class {
      onerror: (() => void) | null = null;
      readAsDataURL() { this.onerror?.(); }
    });
    render(<ShoppingList categories={[{ id: "category-1", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={vi.fn()} />);

    await user.upload(screen.getByLabelText("Imagen del producto"), new File(["image"], "apple.png", { type: "image/png" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo leer la imagen");
  });

  it("waits_for_product_image_file_read_before_creating", async () => {
    const crear = vi.fn();
    const user = userEvent.setup();
    vi.stubGlobal("FileReader", class { readAsDataURL() {} });
    render(<ShoppingList categories={[{ id: "category-1", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={crear} />);

    await user.upload(screen.getByLabelText("Imagen del producto"), new File(["image"], "apple.png", { type: "image/png" }));
    await user.type(screen.getByLabelText("Nombre del producto en Fruta"), "Manzana");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));

    expect(crear).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toContain("Espera a que la imagen esté lista");
  });

  it("waits_for_product_crop_before_creating", async () => {
    const crear = vi.fn();
    const preparar = vi.fn();
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "category-1", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={crear} onPrepareImage={preparar} />);

    await user.upload(screen.getByLabelText("Imagen del producto"), new File(["image"], "apple.png", { type: "image/png" }));
    await screen.findByRole("img", { name: "Vista previa del producto" });
    await user.type(screen.getByLabelText("Nombre del producto en Fruta"), "Manzana");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));

    expect(crear).not.toHaveBeenCalled();
    expect(preparar).not.toHaveBeenCalled();
    expect(screen.getByRole("alert").textContent).toContain("Espera a que la imagen esté lista");
  });

  it("creates_product_with_prepared_image_token", async () => {
    const crear = vi.fn().mockResolvedValue({ id: "product-1", name: "Manzana" });
    const preparar = vi.fn().mockResolvedValue("image-token");
    const user = userEvent.setup();
    render(<ShoppingList categories={[{ id: "category-1", name: "Fruta" }]} onCreateCategory={() => undefined} onGetProducts={async () => []} onCreateProduct={crear} onPrepareImage={preparar} />);

    await user.upload(screen.getByLabelText("Imagen del producto"), new File(["image"], "apple.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.type(screen.getByLabelText("Nombre del producto en Fruta"), "Manzana");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));

    await waitFor(() => expect(crear).toHaveBeenCalledWith("category-1", "Manzana", "image-token"));
  });

  it("renders_product_images_in_catalog_and_shopping_list", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta", image_url: "/category-image.webp" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas", image_url: "/product-image.webp" }] }), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [{ id: "item-1", product_id: "product-1", product_name: "Manzanas", image_url: "/product-image.webp", quantity: 2, unit: "unit" }] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));

    await waitFor(() => expect(screen.getAllByRole("img", { name: "Manzanas" })).toHaveLength(2));
  });

  it("shows_product_image_file_picker_and_crop_preview", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [] }), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    const archivo = await screen.findByLabelText("Imagen del producto") as HTMLInputElement;
    await user.upload(archivo, new File(["image"], "apple.png", { type: "image/png" }));

    expect(await screen.findByRole("img", { name: "Vista previa del producto" })).toBeTruthy();
    expect(screen.getByRole("slider", { name: "Zoom" })).toBeTruthy();
  });

  it("prepares_cropped_product_image_before_create", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, _init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products") && _init?.method === "POST") return new Response(JSON.stringify({ id: "product-1", name: "Manzana" }), { status: 201 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [] }), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({ image_token: "prepared-token" }), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    await user.upload(await screen.findByLabelText("Imagen del producto"), new File(["image"], "apple.png", { type: "image/png" }));
    await user.click(await screen.findByRole("button", { name: "Confirmar recorte" }));
    await user.type(screen.getByLabelText("Nombre del producto en Fruta"), "Manzana");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));

    await waitFor(() => expect(fetchMock.mock.calls.some(([url]) => String(url).endsWith("/food-labels/images/prepare"))).toBe(true));
    const [, options] = fetchMock.mock.calls.find(([url]) => String(url).endsWith("/food-labels/images/prepare"))!;
    expect(JSON.parse(String(options?.body))).toMatchObject({ crop: { x: 1, y: 2, width: 8, height: 8 } });
  });

  // Comprueba que un error al cargar la lista se muestra en la interfaz.
  it("muestra_error_al_fallar_carga_lista_de_la_compra", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [] }), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ detail: "Unavailable" }), { status: 404 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo cargar la lista de la compra.");
  });

  // Comprueba que los totales en unidades y en peso se mantienen separados.
  it("mantiene_separadas_cantidades_en_unidades_y_peso", async () => {
    const respuestas = [
      { product_id: "product-1", quantity: 2, unit: "unit" },
      { product_id: "product-1", quantity: 500, unit: "g" },
    ];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/shopping-list") && init?.method === "POST") return new Response(JSON.stringify(respuestas.shift()), { status: 201 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    const cantidad = await screen.findByLabelText("Cantidad de Manzanas");
    await user.type(cantidad, "2");
    await user.selectOptions(screen.getByLabelText("Unidad de Manzanas"), "unit");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));
    await user.clear(cantidad);
    await user.type(cantidad, "500");
    await user.selectOptions(screen.getByLabelText("Unidad de Manzanas"), "g");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));

    const llamadas = fetchMock.mock.calls.filter(([url, init]) => String(url).endsWith("/shopping-list") && init?.method === "POST");
    expect(llamadas).toHaveLength(2);
    expect(JSON.parse(String(llamadas[0]?.[1]?.body))).toEqual({ product_id: "product-1", quantity: 2, unit: "unit" });
    expect(JSON.parse(String(llamadas[1]?.[1]?.body))).toEqual({ product_id: "product-1", quantity: 500, unit: "g" });
    const lista = screen.getByRole("region", { name: "Lista de la compra" });
    await waitFor(() => expect(lista.textContent).toContain("Manzanas: 2 unidad"));
    expect(lista.textContent).toContain("Manzanas: 500 g");
    expect(lista.querySelectorAll("li")).toHaveLength(2);
  });

  // Comprueba que las cantidades unitarias se agregan según la respuesta del servidor.
  it("actualiza_total_al_anadir_el_mismo_producto_en_unidades", async () => {
    const respuestas = [
      { product_id: "product-1", quantity: 2, unit: "unit" },
      { product_id: "product-1", quantity: 5, unit: "unit" },
    ];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/shopping-list") && init?.method === "POST") return new Response(JSON.stringify(respuestas.shift()), { status: 201 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    const cantidad = await screen.findByLabelText("Cantidad de Manzanas");
    await user.type(cantidad, "2");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));
    await user.clear(cantidad);
    await user.type(cantidad, "3");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));

    const llamadas = fetchMock.mock.calls.filter(([url, init]) => String(url).endsWith("/shopping-list") && init?.method === "POST");
    expect(llamadas).toHaveLength(2);
    expect(JSON.parse(String(llamadas[0]?.[1]?.body))).toEqual({ product_id: "product-1", quantity: 2, unit: "unit" });
    expect(JSON.parse(String(llamadas[1]?.[1]?.body))).toEqual({ product_id: "product-1", quantity: 3, unit: "unit" });
    const lista = screen.getByRole("region", { name: "Lista de la compra" });
    await waitFor(() => expect(lista.textContent).toContain("Manzanas: 5 unidad"));
    expect(lista.querySelectorAll("li")).toHaveLength(1);
  });

  // Comprueba que la UI sustituye el total por el agregado devuelto por el servidor.
  it("actualiza_total_al_anadir_el_mismo_producto_con_pesos_compatibles", async () => {
    const respuestas = [
      { product_id: "product-1", quantity: 500, unit: "g" },
      { product_id: "product-1", quantity: 750, unit: "g" },
    ];
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/shopping-list") && init?.method === "POST") return new Response(JSON.stringify(respuestas.shift()), { status: 201 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    const cantidad = await screen.findByLabelText("Cantidad de Manzanas");
    await user.type(cantidad, "0.5");
    await user.selectOptions(screen.getByLabelText("Unidad de Manzanas"), "kg");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));
    await user.clear(cantidad);
    await user.type(cantidad, "250");
    await user.selectOptions(screen.getByLabelText("Unidad de Manzanas"), "g");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));

    const llamadas = fetchMock.mock.calls.filter(([url, init]) => String(url).endsWith("/shopping-list") && init?.method === "POST");
    expect(llamadas).toHaveLength(2);
    expect(JSON.parse(String(llamadas[0]?.[1]?.body))).toEqual({ product_id: "product-1", quantity: 0.5, unit: "kg" });
    expect(JSON.parse(String(llamadas[1]?.[1]?.body))).toEqual({ product_id: "product-1", quantity: 250, unit: "g" });
    const lista = screen.getByRole("region", { name: "Lista de la compra" });
    await waitFor(() => expect(lista.textContent).toContain("Manzanas: 750 g"));
    expect(lista.querySelectorAll("li")).toHaveLength(1);
  });

  // Comprueba que la vista carga y presenta los productos compartidos al abrirse.
  it("carga_lista_de_la_compra_al_abrir_la_vista", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [{ product_id: "product-1", quantity: 1500, unit: "g" }] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/shopping-list"), expect.objectContaining({ method: "GET" })));
    await waitFor(() => expect(screen.getByRole("region", { name: "Lista de la compra" }).textContent).toContain("Manzanas: 1500 g"));
  });

  // Comprueba el envío a la API y la presentación del total de peso agregado.
  it("muestra_lista_de_la_compra_con_totales_y_medidas", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/shopping-list") && init?.method === "POST") return new Response(JSON.stringify({ product_id: "product-1", quantity: 1500, unit: "g" }), { status: 201 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    await user.type(await screen.findByLabelText("Cantidad de Manzanas"), "1.5");
    await user.selectOptions(screen.getByLabelText("Unidad de Manzanas"), "kg");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/shopping-list"), expect.anything()));
    const [, init] = fetchMock.mock.calls.find(([url, options]) => String(url).endsWith("/shopping-list") && options?.method === "POST")!;
    expect(new Headers(init?.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init?.body))).toEqual({ product_id: "product-1", quantity: 1.5, unit: "kg" });
    const listaDeLaCompra = await screen.findByRole("region", { name: "Lista de la compra" });
    expect(listaDeLaCompra.textContent).toContain("Manzanas");
    expect(listaDeLaCompra.textContent).toContain("1500 g");
  });

  it("loads and shows shared categories after opening its own view", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) {
        return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      }
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Verduras" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [] }), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();

    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));

    expect(await screen.findByText("Verduras")).toBeTruthy();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining("/shopping-categories"), expect.anything()));
  });

  it("creates a category from the shopping list form", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories") && init?.method === "POST") return new Response(JSON.stringify({ id: "category-1", name: "Verduras" }), { status: 201 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [] }), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    await user.type(screen.getByLabelText("Nombre de la categoría"), "Verduras");
    await user.click(screen.getByRole("button", { name: "Crear categoría" }));

    expect(await screen.findByText("Verduras")).toBeTruthy();
    const [, init] = fetchMock.mock.calls.find(([url, options]) => String(url).endsWith("/shopping-categories") && options?.method === "POST")!;
    expect(new Headers(init?.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init?.body))).toEqual({ name: "Verduras" });
  });

  // Simula la API para verificar el formulario, la petición y el producto visible.
  it("creates a product from its category", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories") && init?.method !== "POST") return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Verduras" }] }), { status: 200 });
      if (url.endsWith("/category-1/products") && init?.method !== "POST") return new Response(JSON.stringify({ products: [] }), { status: 200 });
      if (url.endsWith("/category-1/products") && init?.method === "POST") return new Response(JSON.stringify({ id: "product-1", name: "Manzanas" }), { status: 201 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    await user.type(await screen.findByLabelText("Nombre del producto en Verduras"), "Manzanas");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));

    expect(await screen.findByText("Manzanas")).toBeTruthy();
    const [, init] = fetchMock.mock.calls.find(([url, options]) => String(url).endsWith("/category-1/products") && options?.method === "POST")!;
    expect(new Headers(init?.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init?.body))).toEqual({ name: "Manzanas" });
  });

  // Comprueba que un error de la API se muestra y permite reintentar el envío.
  it("shows an error and preserves the product name when creation fails", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Verduras" }] }), { status: 200 });
      if (url.endsWith("/category-1/products") && init?.method === "POST") return new Response(JSON.stringify({ detail: "Database unavailable" }), { status: 500 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [] }), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    const input = await screen.findByLabelText("Nombre del producto en Verduras");
    await user.type(input, "Manzanas");
    await user.click(screen.getByRole("button", { name: "Crear producto" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No se pudo crear el producto");
    expect((input as HTMLInputElement).value).toBe("Manzanas");
  });

  // Comprueba que una entrada pendiente se puede marcar desde la interfaz.
  it("marca_un_producto_como_comprado_y_lo_mueve_a_la_seccion_inferior", async () => {
    const item = { id: "item-1", product_id: "product-1", quantity: 3, unit: "unit" };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/item-1/purchase") && init?.method === "POST") return new Response(JSON.stringify(item), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [item], purchased_items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));

    await user.click(await screen.findByRole("button", { name: "Marcar Manzanas como comprado" }));

    const [, init] = fetchMock.mock.calls.find(([url, options]) => String(url).endsWith("/item-1/purchase") && options?.method === "POST")!;
    expect(new Headers(init?.headers).get("X-CSRF-Token")).toBe("csrf-1");
    const lista = screen.getByRole("region", { name: "Lista de la compra" });
    expect(lista.textContent).toContain("Pendientes");
    expect(lista.textContent).toContain("Comprados");
    expect(lista.textContent!.indexOf("Pendientes")).toBeLessThan(lista.textContent!.indexOf("Comprados"));
    expect(lista.textContent).toContain("Manzanas: 3 unidad");
    expect(lista.querySelectorAll("li")).toHaveLength(1);
  });

  // Comprueba que el estado comprado se recupera del servidor al volver a abrir la lista.
  it("mantiene_el_estado_comprado_al_recargar_la_lista", async () => {
    const item = { id: "item-1", product_id: "product-1", quantity: 3, unit: "unit" };
    let comprado = false;
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/item-1/purchase") && init?.method === "POST") {
        comprado = true;
        return new Response(JSON.stringify(item), { status: 200 });
      }
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: comprado ? [] : [item], purchased_items: comprado ? [item] : [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    await user.click(await screen.findByRole("button", { name: "Marcar Manzanas como comprado" }));
    await user.click(screen.getByRole("button", { name: "Plan semanal" }));
    await user.click(screen.getByRole("button", { name: "Lista de la compra" }));

    const lista = await screen.findByRole("region", { name: "Lista de la compra" });
    await waitFor(() => expect(lista.textContent).toContain("Comprados"));
    expect(lista.textContent).toContain("Manzanas: 3 unidad");
    expect(lista.textContent!.indexOf("Pendientes")).toBeLessThan(lista.textContent!.indexOf("Comprados"));
    expect(lista.querySelectorAll("li")).toHaveLength(1);
    expect(fetchMock.mock.calls.filter(([url, init]) => String(url).endsWith("/shopping-list") && init?.method !== "POST")).toHaveLength(2);
  });

  // Comprueba que los productos comprados ofrecen la acción para volver a pendientes.
  it("renders_unmark_action_for_purchased_items", async () => {
    const comprado = { id: "item-1", product_id: "product-1", quantity: 3, unit: "unit" };
    render(<ShoppingList
      categories={[{ id: "category-1", name: "Fruta" }]}
      onCreateCategory={() => {}}
      onGetProducts={async () => [{ id: "product-1", name: "Manzanas", category_id: "category-1" }]}
      onCreateProduct={async () => ({ id: "product-1", name: "Manzanas", category_id: "category-1" })}
      onGetShoppingList={async () => ({ items: [], purchased_items: [comprado] })}
      onUnmarkPurchased={async () => comprado}
    />);

    expect(await screen.findByRole("button", { name: "Desmarcar Manzanas como pendiente" })).toBeTruthy();
  });

  // Comprueba que desmarcar mueve el producto desde Comprados a Pendientes.
  it("unmarking_refreshes_pending_and_purchased_sections", async () => {
    const comprado = { id: "item-1", product_id: "product-1", quantity: 3, unit: "unit" };
    const user = userEvent.setup();
    render(<ShoppingList
      categories={[{ id: "category-1", name: "Fruta" }]}
      onCreateCategory={() => {}}
      onGetProducts={async () => [{ id: "product-1", name: "Manzanas", category_id: "category-1" }]}
      onCreateProduct={async () => ({ id: "product-1", name: "Manzanas", category_id: "category-1" })}
      onGetShoppingList={async () => ({ items: [], purchased_items: [comprado] })}
      onUnmarkPurchased={async () => comprado}
    />);
    const lista = await screen.findByRole("region", { name: "Lista de la compra" });

    await user.click(await within(lista).findByRole("button", { name: "Desmarcar Manzanas como pendiente" }));

    const seccionPendientes = within(lista).getByRole("heading", { name: "Pendientes" }).nextElementSibling;
    const seccionComprados = within(lista).getByRole("heading", { name: "Comprados" }).nextElementSibling;
    if (!(seccionPendientes instanceof HTMLElement) || !(seccionComprados instanceof HTMLElement)) {
      throw new Error("No se encontraron las listas de pendientes y comprados.");
    }
    expect(within(seccionPendientes).getByText("Manzanas: 3 unidad")).toBeTruthy();
    expect(within(seccionComprados).queryByText("Manzanas: 3 unidad")).toBeNull();
  });

  // Comprueba que la aplicación envía el desmarcado a la API y actualiza ambas secciones.
  it("unmarking_posts_to_api_and_updates_sections", async () => {
    const comprado = { id: "item-1", product_id: "product-1", quantity: 3, unit: "unit" };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/item-1/unpurchase") && init?.method === "POST") return new Response(JSON.stringify(comprado), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [], purchased_items: [comprado] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    const lista = await screen.findByRole("region", { name: "Lista de la compra" });

    await user.click(await within(lista).findByRole("button", { name: "Desmarcar Manzanas como pendiente" }));

    const llamada = fetchMock.mock.calls.find(([url, options]) => String(url).endsWith("/item-1/unpurchase") && options?.method === "POST");
    expect(llamada).toBeTruthy();
    expect(new Headers(llamada?.[1]?.headers).get("X-CSRF-Token")).toBe("csrf-1");
    const seccionPendientes = within(lista).getByRole("heading", { name: "Pendientes" }).nextElementSibling;
    const seccionComprados = within(lista).getByRole("heading", { name: "Comprados" }).nextElementSibling;
    if (!(seccionPendientes instanceof HTMLElement) || !(seccionComprados instanceof HTMLElement)) {
      throw new Error("No se encontraron las listas de pendientes y comprados.");
    }
    expect(within(seccionPendientes).getByText("Manzanas: 3 unidad")).toBeTruthy();
    expect(within(seccionComprados).queryByText("Manzanas: 3 unidad")).toBeNull();
  });

  // Comprueba que volver a añadir un producto comprado crea una entrada pendiente distinta.
  it("vuelve_a_anadir_un_producto_comprado_como_entrada_pendiente", async () => {
    const comprado = { id: "item-bought", product_id: "product-1", quantity: 3, unit: "unit" };
    const pendiente = { id: "item-pending", product_id: "product-1", quantity: 2, unit: "unit" };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/shopping-list") && init?.method === "POST") return new Response(JSON.stringify(pendiente), { status: 201 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [], purchased_items: [comprado] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    await user.type(await screen.findByLabelText("Cantidad de Manzanas"), "2");
    await user.click(screen.getByRole("button", { name: "Añadir Manzanas a la lista" }));

    const lista = screen.getByRole("region", { name: "Lista de la compra" });
    await waitFor(() => expect(lista.querySelectorAll("li")).toHaveLength(2));
    expect(lista.textContent).toContain("Pendientes");
    expect(lista.textContent).toContain("Comprados");
    expect(lista.textContent).toContain("Manzanas: 2 unidad");
    expect(lista.textContent).toContain("Manzanas: 3 unidad");
    const [, request] = fetchMock.mock.calls.find(([url, options]) => String(url).endsWith("/shopping-list") && options?.method === "POST")!;
    expect(JSON.parse(String(request?.body))).toEqual({ product_id: "product-1", quantity: 2, unit: "unit" });
  });

  // Comprueba que al marcar desde la interfaz se refleja la fusión devuelta por la API.
  it("fusiona_cantidades_compradas_compatibles_al_marcar", async () => {
    const comprado = { id: "item-bought", product_id: "product-1", quantity: 3, unit: "unit" };
    const pendiente = { id: "item-pending", product_id: "product-1", quantity: 2, unit: "unit" };
    const fusionado = { ...comprado, quantity: 5 };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/item-pending/purchase") && init?.method === "POST") return new Response(JSON.stringify(fusionado), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [pendiente], purchased_items: [comprado] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    await user.click(await screen.findByRole("button", { name: "Marcar Manzanas como comprado" }));

    const lista = screen.getByRole("region", { name: "Lista de la compra" });
    expect(lista.textContent).toContain("Manzanas: 5 unidad");
    expect(lista.querySelectorAll("li")).toHaveLength(1);
    expect(lista.querySelector("h4")?.textContent).toBe("Pendientes");
    expect(lista.textContent!.indexOf("Pendientes")).toBeLessThan(lista.textContent!.indexOf("Comprados"));
    expect(fetchMock.mock.calls.some(([url, init]) => String(url).endsWith("/item-pending/purchase") && init?.method === "POST")).toBe(true);
  });

  // Comprueba que unidades incompatibles continúan como entradas compradas distintas.
  it("mantiene_separadas_las_medidas_incompatibles_al_marcar", async () => {
    const comprado = { id: "item-bought", product_id: "product-1", quantity: 3, unit: "unit" };
    const pendiente = { id: "item-pending", product_id: "product-1", quantity: 500, unit: "g" };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (url.endsWith("/item-pending/purchase") && init?.method === "POST") return new Response(JSON.stringify(pendiente), { status: 200 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [pendiente], purchased_items: [comprado] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    await user.click(await screen.findByRole("button", { name: "Marcar Manzanas como comprado" }));

    const lista = screen.getByRole("region", { name: "Lista de la compra" });
    await waitFor(() => expect(lista.querySelectorAll("li")).toHaveLength(2));
    expect(lista.textContent).toContain("Manzanas: 3 unidad");
    expect(lista.textContent).toContain("Manzanas: 500 g");
    expect(lista.querySelector("h4")?.textContent).toBe("Pendientes");
    expect(lista.textContent!.indexOf("Pendientes")).toBeLessThan(lista.textContent!.indexOf("Comprados"));
  });

  // Comprueba que los fallos al consultar productos se comunican en la categoría correspondiente.
  it("shows an error when loading products fails", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Verduras" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ detail: "Database unavailable" }), { status: 500 });
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify({ items: [] }), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));

    expect((await screen.findByRole("alert")).textContent).toContain("No se pudieron cargar los productos");
  });

  // Comprueba que eliminar desde ambas secciones afecta solo a la entrada elegida.
  it("deleting_item_from_either_section_updates_only_that_entry", async () => {
    const pendiente = { id: "item-pending", product_id: "product-1", quantity: 2, unit: "unit" };
    const comprado = { id: "item-bought", product_id: "product-1", quantity: 3, unit: "unit" };
    const lista = { items: [pendiente], purchased_items: [comprado] };
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Fruta" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [{ id: "product-1", name: "Manzanas" }] }), { status: 200 });
      if (init?.method === "DELETE" && url.endsWith("/item-pending")) { lista.items = []; return new Response(null, { status: 204 }); }
      if (init?.method === "DELETE" && url.endsWith("/item-bought")) { lista.purchased_items = []; return new Response(null, { status: 204 }); }
      if (url.endsWith("/shopping-list")) return new Response(JSON.stringify(lista), { status: 200 });
      return new Response(JSON.stringify({}), { status: 404 });
    });
    vi.stubGlobal("fetch", fetchMock);
    const user = userEvent.setup();
    render(<App />);
    await user.click(await screen.findByRole("button", { name: "Lista de la compra" }));
    const region = await screen.findByRole("region", { name: "Lista de la compra" });
    const pending = within(region).getByRole("heading", { name: "Pendientes" }).nextElementSibling as HTMLElement;
    const purchased = within(region).getByRole("heading", { name: "Comprados" }).nextElementSibling as HTMLElement;

    await user.click(await within(pending).findByRole("button", { name: /Eliminar/ }));
    await waitFor(() => expect(within(pending).queryByText("Manzanas: 2 unidad")).toBeNull());
    expect(within(purchased).getByText("Manzanas: 3 unidad")).toBeTruthy();
    await user.click(await within(purchased).findByRole("button", { name: /Eliminar/ }));
    await waitFor(() => expect(within(purchased).queryByText("Manzanas: 3 unidad")).toBeNull());
  });
});
