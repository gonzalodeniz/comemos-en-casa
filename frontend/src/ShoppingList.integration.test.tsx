// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

vi.mock("./MealPlanning", () => ({ default: () => <div>Plan semanal</div> }));

afterEach(() => { cleanup(); vi.unstubAllGlobals(); sessionStorage.clear(); });

describe("shopping list integration", () => {
  it("loads and shows shared categories after opening its own view", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) {
        return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      }
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Verduras" }] }), { status: 200 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [] }), { status: 200 });
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

  it("creates a product from its category", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories") && init?.method !== "POST") return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Verduras" }] }), { status: 200 });
      if (url.endsWith("/category-1/products") && init?.method !== "POST") return new Response(JSON.stringify({ products: [] }), { status: 200 });
      if (url.endsWith("/category-1/products") && init?.method === "POST") return new Response(JSON.stringify({ id: "product-1", name: "Manzanas" }), { status: 201 });
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

  it("shows an error and preserves the product name when creation fails", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/auth/session")) return new Response(JSON.stringify({ user: { id: "user-1", name: "Ada", email: "ada@example.test" }, csrf_token: "csrf-1" }), { status: 200 });
      if (url.endsWith("/users")) return new Response(JSON.stringify({ users: [] }), { status: 200 });
      if (url.endsWith("/shopping-categories")) return new Response(JSON.stringify({ categories: [{ id: "category-1", name: "Verduras" }] }), { status: 200 });
      if (url.endsWith("/category-1/products") && init?.method === "POST") return new Response(JSON.stringify({ detail: "Database unavailable" }), { status: 500 });
      if (url.endsWith("/category-1/products")) return new Response(JSON.stringify({ products: [] }), { status: 200 });
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
});
