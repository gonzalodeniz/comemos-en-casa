import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("instalación de la aplicación", () => {
  // Comprueba los datos de instalación que recibe el navegador en producción.
  it("publica el nombre de instalación bajo la ruta de la aplicación", () => {
    execFileSync("npm", ["run", "build"], { stdio: "pipe" });
    const html = readFileSync("dist/index.html", "utf8");
    expect(html).toMatch(/<link\s+rel="manifest"\s+href="\/comemos\/manifest\.webmanifest"/);
    const manifiesto = JSON.parse(readFileSync("dist/manifest.webmanifest", "utf8"));
    expect(manifiesto.name).toBe("Comemos en casa");
  }, 30000);

  // Comprueba que los iconos declarados existen y tienen las dimensiones indicadas.
  it("publica los iconos de instalación en los tamaños declarados", () => {
    execFileSync("npm", ["run", "build"], { stdio: "pipe" });
    const manifiesto = JSON.parse(readFileSync("dist/manifest.webmanifest", "utf8"));
    for (const tamaño of [192, 512]) {
      const icono = manifiesto.icons.find((elemento) => elemento.sizes === `${tamaño}x${tamaño}`);
      expect(icono).toEqual({ src: `/comemos/icono-${tamaño}.png`, sizes: `${tamaño}x${tamaño}`, type: "image/png" });
      const imagen = readFileSync(`dist/icono-${tamaño}.png`);
      expect(imagen.subarray(0, 8)).toEqual(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]));
      expect(imagen.readUInt32BE(16)).toBe(tamaño);
      expect(imagen.readUInt32BE(20)).toBe(tamaño);
    }
  }, 30000);

  // Comprueba el inicio y el modo de presentación de la aplicación instalada.
  it("abre la aplicación instalada en su ruta sin la barra del navegador", () => {
    execFileSync("npm", ["run", "build"], { stdio: "pipe" });
    const manifiesto = JSON.parse(readFileSync("dist/manifest.webmanifest", "utf8"));
    expect(manifiesto.start_url).toBe("/comemos/");
    expect(manifiesto.scope).toBe("/comemos/");
    expect(manifiesto.display).toBe("standalone");
  }, 30000);
});
