// Comprueba la presentación del mensaje push por el trabajador de servicio.
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { expect, it, vi } from "vitest";

it("muestra el recordatorio recibido en una notificación", async () => {
  const eventos = {};
  const mostrar = vi.fn().mockResolvedValue(undefined);
  const self = { addEventListener: (tipo, funcion) => { eventos[tipo] = funcion; }, registration: { showNotification: mostrar } };
  runInNewContext(readFileSync("public/notificaciones-worker.js", "utf8"), { self });
  let promesa;
  eventos.push({ data: { json: () => ({ titulo: "Recordatorio de comida", mensaje: "Sacar pollo" }) }, waitUntil: (valor) => { promesa = valor; } });
  await promesa;
  expect(mostrar).toHaveBeenCalledWith("Recordatorio de comida", expect.objectContaining({ body: "Sacar pollo" }));
});
