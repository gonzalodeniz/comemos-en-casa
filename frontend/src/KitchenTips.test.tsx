// Comprueba que se muestran ambos trucos y su contenido seleccionable.
// @vitest-environment jsdom
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiRequest } from "./api";
import KitchenTips from "./KitchenTips";

vi.mock("./api", () => ({
  ApiError: class ApiError extends Error { status = 500; },
  apiRequest: vi.fn(),
}));

describe("KitchenTips", () => {
  beforeEach(() => vi.mocked(apiRequest).mockResolvedValue({ trucos: [
    { id: "lechuga", title: "Limpiar lechuga con Thermomix", content: "Lava y escurre las hojas." },
    { id: "sarten", title: "Limpiar una sartén de aluminio", content: "Usa detergente suave y una esponja." },
  ] }));

  it("shows both tips and their selected instructions", async () => {
    render(<KitchenTips onSessionExpired={vi.fn()} />);
    expect(await screen.findByRole("button", { name: "Limpiar lechuga con Thermomix" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Limpiar una sartén de aluminio" })).toBeTruthy();
    expect(screen.getByText("Lava y escurre las hojas.")).toBeTruthy();
    await userEvent.click(screen.getByRole("button", { name: "Limpiar una sartén de aluminio" }));
    await waitFor(() => expect(screen.getByText("Usa detergente suave y una esponja.")).toBeTruthy());
  });
});
