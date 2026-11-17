// Verifica los estados de éxito y error al crear copias desde la vista.
// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import Backups from "./Backups";

describe("Backups", () => {
  afterEach(() => { cleanup(); vi.restoreAllMocks(); });

  it("shows confirmation when the server creates a backup", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({ backups: [] }))).mockResolvedValueOnce(new Response(JSON.stringify({ filename: "backup.zip" }), { status: 201 }));
    render(<Backups csrfToken="csrf" onSessionExpired={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Crear copia" }));
    expect((await screen.findByRole("status")).textContent).toContain("backup.zip");
  });

  it("shows an error instead of success when backup creation fails", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(new Response(JSON.stringify({ backups: [] }))).mockResolvedValueOnce(new Response(JSON.stringify({ detail: "failed" }), { status: 500 }));
    render(<Backups csrfToken="csrf" onSessionExpired={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: "Crear copia" }));
    await waitFor(() => expect(screen.getByRole("alert").textContent).toContain("No se pudo crear"));
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("lists archives with a direct download link", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ backups: [{ filename: "backup-20261117T100000Z.zip", size: 42 }] })));
    render(<Backups csrfToken="csrf" onSessionExpired={vi.fn()} />);
    const link = await screen.findByRole("link", { name: "Descargar" });
    expect(link.getAttribute("href")).toBe("/comemos/api/v1/backups/backup-20261117T100000Z.zip");
    expect(link.getAttribute("download")).toBe("backup-20261117T100000Z.zip");
  });

  it("shows a list error when the server cannot return archives", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify({ detail: "failed" }), { status: 500 }));
    render(<Backups csrfToken="csrf" onSessionExpired={vi.fn()} />);
    expect((await screen.findByRole("alert")).textContent).toContain("No se pudieron cargar");
  });
});
