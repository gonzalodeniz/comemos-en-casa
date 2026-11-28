// Comprueba la presentación del mensaje push por el trabajador de servicio.
import { readFileSync } from "node:fs";
import { runInNewContext } from "node:vm";
import { expect, it, vi } from "vitest";

it("muestra el recordatorio con el icono de la aplicación y la insignia de casa", async () => {
  const eventos = {};
  const mostrar = vi.fn().mockResolvedValue(undefined);
  const self = { addEventListener: (tipo, funcion) => { eventos[tipo] = funcion; }, registration: { scope: "https://example.test/comemos/", showNotification: mostrar } };
  runInNewContext(readFileSync("public/notificaciones-worker.js", "utf8"), { self, URL });
  let promesa;
  eventos.push({ data: { json: () => ({ titulo: "Recordatorio de comida", mensaje: "Sacar pollo" }) }, waitUntil: (valor) => { promesa = valor; } });
  await promesa;
  expect(mostrar).toHaveBeenCalledWith("Recordatorio de comida", {
    body: "Sacar pollo",
    icon: "https://example.test/comemos/icono-192.png",
    badge: "https://example.test/comemos/insignia-casa.png",
  });
});
