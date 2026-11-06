// Comprueba la presentación inicial del catálogo de productos.
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import ProductCatalog from "./ProductCatalog";

describe("ProductCatalog", () => {
  it("muestra categorías ordenadas sin buscador ni filtros", () => {
    const markup = renderToStaticMarkup(<ProductCatalog onUpdateCategoryImage={vi.fn()} onUpdateProductImage={vi.fn()} onImportImage={vi.fn()} onPrepareImage={vi.fn()} categories={[{ id: "1", name: "Verduras" }, { id: "2", name: "Frutas" }]} onSessionExpired={vi.fn()} onGetProducts={vi.fn()} onCreateCategory={vi.fn()} onCreateProduct={vi.fn()} />);
    expect(markup.indexOf("Frutas")).toBeLessThan(markup.indexOf("Verduras"));
    expect(markup).not.toContain("Buscar");
    expect(markup).not.toContain("Alimentación");
  });
});
