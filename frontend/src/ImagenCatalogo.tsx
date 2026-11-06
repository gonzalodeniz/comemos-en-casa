// Permite seleccionar, importar y recortar la imagen opcional del catálogo.
import { useEffect, useRef, useState } from "react";
import Cropper from "react-easy-crop";

// Describe el recorte expresado en píxeles de la imagen original.
export type RecorteCatalogo = { x: number; y: number; width: number; height: number };

// Define los servicios y el estado comunicado al formulario propietario.
type Props = {
  importar: (url: string) => Promise<string>;
  cambiar: (imagen: string, recorte: RecorteCatalogo | null, ocupado: boolean) => void;
};

/** Ofrece selección local, pegado, arrastre, importación y recorte. */
export default function ImagenCatalogo({ importar, cambiar }: Props) {
  const [imagen, setImagen] = useState("");
  const [url, setUrl] = useState("");
  const [posicion, setPosicion] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [error, setError] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const revision = useRef(0);

  // Impide aplicar una lectura o importación al cerrar el editor.
  useEffect(() => () => { revision.current++; }, []);

  /** Inicia una selección y anula cualquier resultado anterior pendiente. */
  function iniciar() {
    const actual = ++revision.current;
    setImagen(""); setError(""); setOcupado(true); cambiar("", null, true);
    return actual;
  }

  /** Lee la imagen local seleccionada, pegada o arrastrada. */
  function leer(archivo?: File) {
    if (!archivo) return;
    const actual = iniciar();
    const lector = new FileReader();
    lector.onload = () => {
      if (revision.current !== actual) return;
      const resultado = String(lector.result);
      setImagen(resultado); setOcupado(false); cambiar(resultado, null, false);
    };
    lector.onerror = () => {
      if (revision.current !== actual) return;
      setError("No se pudo leer la imagen."); setOcupado(false); cambiar("", null, false);
    };
    lector.readAsDataURL(archivo);
  }

  /** Obtiene una imagen remota mediante el servicio existente. */
  async function importarUrl() {
    const actual = iniciar();
    try {
      const resultado = await importar(url);
      if (revision.current !== actual) return;
      setImagen(resultado); cambiar(resultado, null, false);
    } catch {
      if (revision.current !== actual) return;
      setError("No se pudo importar la imagen."); cambiar("", null, false);
    } finally {
      if (revision.current === actual) setOcupado(false);
    }
  }

  return <fieldset><legend>Imagen opcional</legend>
    <label tabIndex={0} onPaste={(evento) => leer(Array.from(evento.clipboardData.files).find((archivo) => archivo.type.startsWith("image/")))} onDragOver={(evento) => evento.preventDefault()} onDrop={(evento) => { evento.preventDefault(); leer(evento.dataTransfer.files[0]); }}>
      Seleccionar, pegar o arrastrar imagen<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(evento) => leer(evento.target.files?.[0])} />
    </label>
    <label>URL de imagen<input type="url" value={url} onChange={(evento) => setUrl(evento.target.value)} /></label>
    <button type="button" disabled={!url || ocupado} onClick={() => void importarUrl()}>Importar imagen</button>
    {imagen && <><div className="crop-area" aria-label="Recortar imagen"><Cropper image={imagen} crop={posicion} zoom={zoom} aspect={1} onCropChange={(valor) => { setPosicion(valor); cambiar(imagen, null, false); }} onZoomChange={(valor) => { setZoom(valor); cambiar(imagen, null, false); }} onCropComplete={(_area, pixels) => cambiar(imagen, pixels, false)} /></div><label>Zoom<input type="range" min="1" max="3" step="0.05" value={zoom} onChange={(evento) => { setZoom(Number(evento.target.value)); cambiar(imagen, null, false); }} /></label></>}
    {ocupado && <p role="status">Procesando imagen…</p>}{error && <p role="alert">{error}</p>}
  </fieldset>;
}
