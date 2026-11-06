// Verifica las peticiones del cliente de planificación y catálogos.
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  applyMealPlanning,
  getFoodLabels,
  getMealPlanning,
  previewMealPlanning,
  type MealPlanningOperation,
} from "./mealPlanningApi";

afterEach(() => vi.unstubAllGlobals());

const operation: MealPlanningOperation = {
  action: "assign",
  start_date: "2026-11-02",
  slot: "dinner",
  label_id: "label-1",
  repeat: { interval_weeks: 2, end_date: "2026-11-30" },
};

describe("meal planning API client", () => {
  it("updates_existing_category_image_with_token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "category-1", name: "Fruta" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const { updateShoppingCategoryImage } = await import("./mealPlanningApi");
    await updateShoppingCategoryImage("category-1", "csrf-1", { image_token: "image-token" });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/shopping-categories/category-1");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(String(init.body))).toEqual({ image_token: "image-token" });
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
  });

  it("updates_existing_product_image_with_token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "product-1", name: "Manzana" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    const { updateShoppingProductImage } = await import("./mealPlanningApi");
    await updateShoppingProductImage("category-1", "product-1", "csrf-1", { image_token: "image-token" });
    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/shopping-categories/category-1/products/product-1");
    expect(init.method).toBe("PATCH");
    expect(JSON.parse(String(init.body))).toEqual({ image_token: "image-token" });
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
  });

  // Comprueba que la creación de categoría envía el token de imagen preparado.
  it("creates_shopping_category_with_prepared_image_token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "category-1", name: "Fruta" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    const { createShoppingCategory } = await import("./mealPlanningApi");

    await createShoppingCategory("Fruta", "csrf-1", "image-token");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/shopping-categories");
    expect(JSON.parse(String(init.body))).toEqual({ name: "Fruta", image_token: "image-token" });
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
  });
  // Comprueba que el token de imagen preparado acompaña a la creación del producto.
  it("creates_shopping_product_with_prepared_image_token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ id: "product-1", name: "Manzana" }), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);
    const { createShoppingProduct } = await import("./mealPlanningApi");

    await createShoppingProduct("category-1", "Manzana", "csrf-1", "image-token");

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/shopping-categories/category-1/products");
    expect(JSON.parse(String(init.body))).toEqual({ name: "Manzana", image_token: "image-token" });
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
  });
  // Comprueba que se consulta la lista de la compra con el cliente autenticado.
  it("carga_lista_de_la_compra_con_sus_productos", async () => {
    const response = { items: [{ product_id: "product-1", quantity: 1500, unit: "g" }] };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const { obtenerListaCompra } = await import("./mealPlanningApi");
    await expect(obtenerListaCompra()).resolves.toEqual(response);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/shopping-list");
    expect(init.method).toBe("GET");
    expect(init.credentials).toBe("include");
  });

  // Comprueba que se añade un producto a la lista con CSRF y se devuelve el total agregado.
  it("agrega_producto_a_la_lista_con_csrf_y_medida", async () => {
    const response = { product_id: "product-1", quantity: 1500, unit: "g" };
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(response), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    const { agregarProductoListaCompra } = await import("./mealPlanningApi");
    await expect(agregarProductoListaCompra("product-1", 1.5, "kg", "csrf-1")).resolves.toEqual(response);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/shopping-list");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init.body))).toEqual({ product_id: "product-1", quantity: 1.5, unit: "kg" });
  });

  // Comprueba que se elimina una entrada concreta con el token CSRF.
  it("elimina_una_entrada_de_lista_con_csrf", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    const { eliminarEntradaListaCompra } = await import("./mealPlanningApi");
    await expect(eliminarEntradaListaCompra("item-1", "csrf-1")).resolves.toBeNull();

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/shopping-list/item-1");
    expect(init.method).toBe("DELETE");
    expect(init.credentials).toBe("include");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
  });

  it("loads the food-label catalog using the shared authenticated client", async () => {
    const response = { labels: [{ id: "label-1", code: "fish", name: "Fish" }] };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(response), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(getFoodLabels()).resolves.toEqual(response);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/food-labels");
    expect(init.method).toBe("GET");
    expect(init.credentials).toBe("include");
  });

  it("loads and creates shopping categories through the shared API", async () => {
    const response = { categories: [{ id: "category-1", name: "Verduras" }] };
    const fetchMock = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(response), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(response.categories[0]), { status: 201 }));
    vi.stubGlobal("fetch", fetchMock);

    const { getShoppingCategories, createShoppingCategory } = await import("./mealPlanningApi");
    await expect(getShoppingCategories()).resolves.toEqual(response);
    await expect(createShoppingCategory("Verduras", "csrf-1")).resolves.toEqual(response.categories[0]);

    expect(fetchMock.mock.calls[0]?.[0]).toContain("/api/v1/shopping-categories");
    const [url, init] = fetchMock.mock.calls[1] as [string, RequestInit];
    expect(url).toContain("/api/v1/shopping-categories");
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init.body))).toEqual({ name: "Verduras" });
  });

  it("requests an inclusive planning range with encoded calendar-date parameters", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ assignments: [] }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getMealPlanning("2026-11-02", "2026-11-08");

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    const parsed = new URL(url, "http://localhost");
    expect(parsed.pathname).toContain("/api/v1/meal-planning");
    expect(parsed.searchParams.get("start_date")).toBe("2026-11-02");
    expect(parsed.searchParams.get("end_date")).toBe("2026-11-08");
  });

  it("sends the preview operation and CSRF token without a confirmation flag", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ preview_token: "preview-1" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(previewMealPlanning(operation, "csrf-1")).resolves.toMatchObject({
      preview_token: "preview-1",
    });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/meal-planning/preview");
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init.body))).toEqual(operation);
  });

  it("applies only the operation bound to its preview token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ changed_count: 2 }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(applyMealPlanning(operation, "preview-1", "csrf-1")).resolves.toMatchObject({
      changed_count: 2,
    });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init.body))).toEqual({
      ...operation,
      confirmed: true,
      preview_token: "preview-1",
    });
  });
});
