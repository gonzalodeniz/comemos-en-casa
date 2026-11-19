// Comprueba que se muestran ambos trucos y su contenido seleccionable.
// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from "@testing-library/react";
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
    await userEvent.click(screen.getByRole("button", { name: "Editar truco" }));
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
    expect(screen.getByText("Contenido editado.")).toBeTruthy();
  });

  it("shows both tips and their selected instructions", async () => {
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    expect(await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Limpiar una sartén de aluminio" })).toBeTruthy();
    expect(screen.getByText("Lava y escurre las hojas.")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Limpiar una sartén de aluminio" }));
    await waitFor(() => expect(screen.getByText("Usa detergente suave y una esponja.")).toBeTruthy());
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
    expect(screen.getByText("Contenido nuevo.")).toBeTruthy();
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
});
