// Comprueba que se muestran ambos trucos y su contenido seleccionable.
// @vitest-environment jsdom
import { cleanup, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest } from "./api";
import KitchenTips from "./KitchenTips";

vi.mock("./api", () => ({
  ApiError: class ApiError extends Error { status = 500; },
  apiRequest: vi.fn(),
}));

describe("KitchenTips", () => {
  afterEach(cleanup);
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(apiRequest).mockResolvedValue({ trucos: [
    { id: "lechuga", title: "Limpiar lechuga con Thermomix", content: "Lava y escurre las hojas." },
    { id: "sarten", title: "Limpiar una sartén de aluminio", content: "Usa detergente suave y una esponja." },
  ] });
  });

  it("edits a tip using its current values and updates the detail", async () => {
    vi.mocked(apiRequest).mockImplementation(async (_path, opciones) => {
      if (opciones?.method === "PATCH") return { id: "lechuga", title: "Título editado", content: "Contenido editado." };
      return { trucos: [{ id: "lechuga", title: "Lechuga", content: "Contenido original." }] };
    });
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    await screen.findByRole("button", { name: "Lechuga" });
    await userEvent.click(screen.getByRole("button", { name: "Editar truco Lechuga" }));
    const titulo = screen.getByLabelText("Título") as HTMLInputElement;
    const contenido = screen.getByLabelText("Contenido") as HTMLTextAreaElement;
    expect(titulo.value).toBe("Lechuga");
    expect(contenido.value).toBe("Contenido original.");
    await userEvent.clear(titulo);
    await userEvent.type(titulo, "Título editado");
    await userEvent.clear(contenido);
    await userEvent.type(contenido, "Contenido editado.");
    await userEvent.click(screen.getByRole("button", { name: "Guardar cambios" }));
    expect(await screen.findByRole("button", { name: "Título editado" })).toBeTruthy();
    expect(within(screen.getByRole("article")).getByText("Contenido editado.")).toBeTruthy();
  });

  it("shows both tips and their selected instructions", async () => {
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    expect(await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Limpiar una sartén de aluminio" })).toBeTruthy();
    expect(within(screen.getByRole("article")).getByText("Lava y escurre las hojas.")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Limpiar una sartén de aluminio" }));
    await waitFor(() => expect(within(screen.getByRole("article")).getByText("Usa detergente suave y una esponja.")).toBeTruthy());
  });

  // Verifica la búsqueda local y la conservación del detalle seleccionado.
  it("filters tips by title or content without changing the selected tip", async () => {
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" });
    const buscador = screen.getByRole("searchbox", { name: "Buscar trucos" });
    await userEvent.type(buscador, "SARTEN");
    expect(screen.queryByRole("button", { name: "Limpiar lechuga con Thermomix" })).toBeNull();
    expect(screen.getByRole("button", { name: "Limpiar una sartén de aluminio" })).toBeTruthy();
    expect(within(screen.getByRole("article")).getByRole("heading", { name: "Limpiar lechuga con Thermomix" })).toBeTruthy();
    await userEvent.clear(buscador);
    await userEvent.type(buscador, "detergente");
    expect(screen.getByRole("button", { name: "Limpiar una sartén de aluminio" })).toBeTruthy();
    await userEvent.type(buscador, " inexistente");
    expect(screen.getByRole("status").textContent).toMatch(/No se encontraron trucos/);
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });

  it("shows edit and delete actions as accessible icon buttons", async () => {
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" });
    for (const name of ["Editar truco Limpiar lechuga con Thermomix", "Eliminar truco Limpiar lechuga con Thermomix"]) {
      const button = screen.getByRole("button", { name });
      expect(button.querySelector("svg")).toBeTruthy();
      expect(button.textContent).toBe("");
    }
  });

  it("keeps the form fields and save action accessible when creating and editing", async () => {
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" });
    expect(screen.getByRole("textbox", { name: "Título" })).toBeTruthy();
    expect(screen.getByRole("textbox", { name: "Contenido" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Guardar truco" })).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Editar truco Limpiar lechuga con Thermomix" }));
    expect(screen.getByRole("textbox", { name: "Título" })).toBeTruthy();
    expect(screen.getByRole("textbox", { name: "Contenido" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Guardar cambios" })).toBeTruthy();
  });

  it("creates a tip and displays it without reloading", async () => {
    vi.mocked(apiRequest).mockImplementation(async (_path, opciones) => {
      if ((opciones as { method?: string } | undefined)?.method === "POST") {
        return { id: "nuevo", title: "Nuevo truco", content: "Contenido nuevo." };
      }
      return { trucos: [
        { id: "lechuga", title: "Limpiar lechuga con Thermomix", content: "Lava y escurre las hojas." },
        { id: "sarten", title: "Limpiar una sartén de aluminio", content: "Usa detergente suave y una esponja." },
      ] };
    });
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" });
    await userEvent.type(screen.getByLabelText("Título"), "Nuevo truco");
    await userEvent.type(screen.getByLabelText("Contenido"), "Contenido nuevo.");
    await userEvent.click(screen.getByRole("button", { name: "Guardar truco" }));
    expect(await screen.findByRole("button", { name: "Nuevo truco" })).toBeTruthy();
    expect(within(screen.getByRole("article")).getByText("Contenido nuevo.")).toBeTruthy();
  });

  it("shows which required field is blank without sending the request", async () => {
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" });
    await userEvent.type(screen.getByLabelText("Título"), "   ");
    await userEvent.type(screen.getByLabelText("Contenido"), "Texto válido");
    await userEvent.click(screen.getByRole("button", { name: "Guardar truco" }));
    expect((await screen.findByRole("alert")).textContent).toBe("El título es obligatorio.");
    expect(apiRequest).toHaveBeenCalledTimes(1);
  });

  it("confirms deletion, cancels without changes, then removes the selected tip", async () => {
    vi.stubGlobal("confirm", vi.fn().mockReturnValueOnce(false).mockReturnValueOnce(true));
    vi.mocked(apiRequest).mockImplementation(async (_path, opciones) => {
      if ((opciones as { method?: string } | undefined)?.method === "DELETE") return undefined;
      return { trucos: [
        { id: "lechuga", title: "Limpiar lechuga con Thermomix", content: "Lava y escurre las hojas." },
        { id: "sarten", title: "Limpiar una sartén de aluminio", content: "Usa detergente suave y una esponja." },
      ] };
    });
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" });
    await userEvent.click(screen.getByRole("button", { name: "Eliminar truco Limpiar lechuga con Thermomix" }));
    expect(within(screen.getByRole("article")).getByText("Lava y escurre las hojas.")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Eliminar truco Limpiar lechuga con Thermomix" }));
    expect(await screen.findByRole("button", { name: "Limpiar una sartén de aluminio" })).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Limpiar lechuga con Thermomix" })).toBeNull();
  });

  it("shows an empty state and keeps the form available after deleting the last tip", async () => {
    vi.mocked(apiRequest).mockImplementation(async (_path, opciones) => {
      if ((opciones as { method?: string } | undefined)?.method === "DELETE") return undefined;
      return { trucos: [{ id: "lechuga", title: "Lechuga", content: "Contenido." }] };
    });
    vi.stubGlobal("confirm", vi.fn().mockReturnValue(true));
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    await screen.findByRole("button", { name: "Lechuga" });
    await userEvent.click(screen.getByRole("button", { name: "Eliminar truco Lechuga" }));
    expect(await screen.findByText("No hay trucos de cocina todavía.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Guardar truco" })).toBeTruthy();
  });
});
