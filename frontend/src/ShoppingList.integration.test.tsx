// @vitest-environment jsdom
// Comprueba los flujos de la lista de compra desde la interfaz con la API simulada.
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";
import ShoppingList from "./ShoppingList";

vi.mock("./MealPlanning", () => ({ default: () => <div>Plan semanal</div> }));

afterEach(() => { cleanup(); vi.unstubAllGlobals(); sessionStorage.clear(); });

describe("shopping list integration", () => {
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
});
