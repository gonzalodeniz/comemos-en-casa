// Comprueba las operaciones confirmadas sin modificar archivos reales.
// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import Backups from "./Backups";
// Define una copia generada por el formato actual del servidor.
const copia = { filename: "backup-20261117T100000Z.zip", size: 1048576 };
// Mantiene el estado simulado para comprobar actualizaciones.
let archivos = [copia];
let fallar = false;
let llamadas: string[] = [];
beforeEach(() => {
  archivos = [copia]; fallar = false; llamadas = [];
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", { configurable: true, value: function (this: HTMLDialogElement) { this.setAttribute("open", ""); } });
  Object.defineProperty(HTMLDialogElement.prototype, "close", { configurable: true, value: function (this: HTMLDialogElement) { this.removeAttribute("open"); } });
  vi.spyOn(globalThis, "fetch").mockImplementation(async (entrada, opciones) => {
    const url = String(entrada); const metodo = opciones?.method ?? "GET";
    llamadas.push(`${metodo} ${url}`);
    if (metodo === "GET") return new Response(JSON.stringify(url.endsWith("schedule") ? { enabled: true, frequency: "weekly", maximum: 4 } : { backups: archivos }));
    if (fallar) return new Response(JSON.stringify({ detail: "Fallo de prueba" }), { status: 500 });
    if (metodo === "DELETE") { archivos = []; return new Response(null, { status: 204 }); }
    if (url.endsWith("schedule")) return new Response(JSON.stringify({ enabled: true, frequency: "daily", maximum: 5 }));
    return new Response(JSON.stringify(url.endsWith("restore") ? { status: "restored" } : { filename: copia.filename }));
  });
});
afterEach(() => { cleanup(); vi.restoreAllMocks(); });
// Espera la consulta inicial antes de iniciar operaciones.
async function iniciar() {
  render(<Backups csrfToken="csrf" onSessionExpired={vi.fn()} />);
  await screen.findByText("Semanal · Máx. 4 copias");
  await screen.findByRole("link", { name: `Descargar ${copia.filename}` });
}
it("muestra metadatos reales y conserva la descarga", async () => {
  await iniciar();
  expect(screen.getByText("1 MB (1 copias)")).toBeTruthy();
  expect(screen.getByRole("link").getAttribute("download")).toBe(copia.filename);
});
it("crea una copia y vuelve a consultar el listado", async () => {
  await iniciar(); fireEvent.click(screen.getByRole("button", { name: "Crear copia ahora" }));
  expect((await screen.findByRole("status")).textContent).toContain("Copia creada");
  await waitFor(() => expect(llamadas.filter((valor) => valor === "GET /comemos/api/v1/backups").length).toBe(2));
});
it("no anuncia éxito al fallar la creación", async () => {
  await iniciar(); fallar = true; fireEvent.click(screen.getByRole("button", { name: "Crear copia ahora" }));
  expect((await screen.findByRole("alert")).textContent).toContain("No se pudo crear");
  expect(screen.queryByRole("status")).toBeNull();
});
it("confirma la eliminación y actualiza el resumen", async () => {
  await iniciar(); fireEvent.click(screen.getByRole("button", { name: `Eliminar copia ${copia.filename}` }));
  expect(llamadas.some((valor) => valor.startsWith("DELETE"))).toBe(false);
  fireEvent.click(screen.getByRole("button", { name: "Confirmar eliminación" }));
  expect(await screen.findByText("Todavía no hay copias de seguridad")).toBeTruthy();
});
it("permite cancelar la restauración sin efectos", async () => {
  await iniciar(); fireEvent.click(screen.getByRole("button", { name: "Restaurar" }));
  expect(screen.getByRole("dialog")).toBeTruthy(); fireEvent.click(screen.getByRole("button", { name: "Cancelar" }));
  expect(llamadas.some((valor) => valor.includes("/restore"))).toBe(false);
});
it("mantiene el error crítico de restauración sin anunciar éxito", async () => {
  await iniciar(); fallar = true; fireEvent.click(screen.getByRole("button", { name: "Restaurar" }));
  fireEvent.click(screen.getByRole("button", { name: "Confirmar restauración" }));
  expect((await screen.findByRole("alert")).textContent).toContain("recuperación manual");
  expect(screen.queryByRole("status")).toBeNull();
});
it("carga la configuración y exige cambios válidos para guardarla", async () => {
  await iniciar(); fireEvent.click(screen.getByRole("button", { name: "Configurar automatización" }));
  const guardar = screen.getByRole("button", { name: "Guardar automatización" }) as HTMLButtonElement;
  expect(guardar.disabled).toBe(true);
  fireEvent.change(screen.getByLabelText("Frecuencia", { exact: false }), { target: { value: "daily" } });
  fireEvent.change(screen.getByLabelText("Máximo de copias", { exact: false }), { target: { value: "5" } });
  fireEvent.click(guardar);
  expect(await screen.findByText("Diaria · Máx. 5 copias")).toBeTruthy();
});

it("bloquea creaciones duplicadas mientras el servidor responde", async () => {
  await iniciar();
  // Retiene la confirmación para comprobar el bloqueo durante la operación.
  let confirmar!: (respuesta: Response) => void;
  vi.mocked(fetch).mockImplementationOnce(() => new Promise<Response>((resolver) => { confirmar = resolver; }));
  const crear = screen.getByRole("button", { name: "Crear copia ahora" });
  const anteriores = vi.mocked(fetch).mock.calls.length;
  fireEvent.click(crear); fireEvent.click(crear);
  expect(vi.mocked(fetch).mock.calls.length).toBe(anteriores + 1);
  expect(screen.queryByText(/Copia creada:/)).toBeNull();
  confirmar(new Response(JSON.stringify({ filename: copia.filename })));
  expect((await screen.findByRole("status")).textContent).toContain("Copia creada");
});

it("sube una copia seleccionada sin restaurarla y actualiza la lista", async () => {
  await iniciar();
  const archivo = new File(["contenido"], "backup-20261116T100000Z.zip", { type: "application/zip" });
  fireEvent.change(screen.getByLabelText("Subir copia"), { target: { files: [archivo] } });
  expect((await screen.findByRole("status")).textContent).toContain("Copia subida");
  expect(llamadas.some((valor) => valor.includes("/backups/upload?filename="))).toBe(true);
  expect(llamadas.some((valor) => valor.includes("/restore"))).toBe(false);
});

it("explica el rechazo del proxy cuando el archivo es demasiado grande", async () => {
  await iniciar();
  vi.mocked(fetch).mockResolvedValueOnce(new Response("Payload Too Large", { status: 413 }));
  const archivo = new File(["contenido"], "backup-20261116T100000Z.zip", { type: "application/zip" });
  fireEvent.change(screen.getByLabelText("Subir copia"), { target: { files: [archivo] } });
  expect((await screen.findByRole("alert")).textContent).toContain("tamaño permitido");
});
