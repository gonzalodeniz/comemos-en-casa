// Permite editar la cantidad o descripción de un producto pendiente.
import { useEffect, useRef, useState, type FormEvent } from "react";
import AppIcon from "./AppIcon";
import type { CambioCantidad, ShoppingListItem } from "./mealPlanningApi";

// Define la entrada y las acciones del diálogo de edición.
type Props = { entrada: ShoppingListItem; guardar: (id: string, cambio: CambioCantidad) => Promise<ShoppingListItem>; alGuardar: (entrada: ShoppingListItem) => void; cerrar: () => void };

/** Edita una cantidad sin descartar los datos si falla la petición. */
export default function DialogoEditarCompra({ entrada, guardar, alGuardar, cerrar }: Props) {
  const ventana = useRef<HTMLDialogElement>(null);
  const enviando = useRef(false);
  const [ocupado, setOcupado] = useState(false);
  const [modo, setModo] = useState<"texto" | "unit" | "g" | "kg">(entrada.quantity_text != null ? "texto" : entrada.unit === "g" ? "g" : entrada.unit === "kg" ? "kg" : "unit");
  const textoLibre = modo === "texto";
  const [texto, setTexto] = useState(entrada.quantity_text ?? "");
  const [cantidad, setCantidad] = useState(String(entrada.quantity));
  const [observacion, setObservacion] = useState(entrada.observation ?? "");
  const [error, setError] = useState("");
  useEffect(() => {
    const origen = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialogo = ventana.current;
    dialogo?.showModal();
    return () => { if (dialogo?.open) dialogo.close(); origen?.focus(); };
  }, []);
  /** Persiste el valor seleccionado y evita envíos simultáneos. */
  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!entrada.id || enviando.current) return;
    enviando.current = true; setOcupado(true); setError("");
    try {
      const cambio = textoLibre ? { quantity_text: texto.trim(), observation: observacion.trim() } : { quantity: Number(cantidad), unit: modo, observation: observacion.trim() };
      if (textoLibre && !texto.trim()) { setError("Introduce una descripción."); return; }
      alGuardar(await guardar(entrada.id, cambio)); cerrar();
    } catch { setError("No se pudo guardar. Comprueba que no exista otra entrada numérica con la misma unidad."); }
    finally { enviando.current = false; setOcupado(false); }
  }
  return <dialog ref={ventana} aria-labelledby="titulo-editar-compra" onCancel={(evento) => { evento.preventDefault(); if (!enviando.current) cerrar(); }}>
    <form onSubmit={(evento) => void enviar(evento)}>
      <h3 id="titulo-editar-compra">Editar {entrada.product_name ?? "producto"}</h3>
      <div className="compra-modos" role="group" aria-label="Tipo de cantidad">{([['texto','T','Texto libre'],['unit','U','Unidades'],['g','gr','Gramos'],['kg','kg','Kilogramos']] as const).map(([valor, etiqueta, ayuda]) => <button key={valor} type="button" className={modo === valor ? "seleccionado" : ""} aria-pressed={modo === valor} aria-label={ayuda} data-tooltip={ayuda} onClick={() => setModo(valor)}>{etiqueta}</button>)}</div>
      {textoLibre ? <label>Texto libre<input required maxLength={255} value={texto} onChange={(evento) => setTexto(evento.target.value)} /></label> : <label>{modo === "unit" ? "Unidades" : modo === "g" ? "Gramos" : "Kilogramos"}<input type="number" min="0.01" step="any" required value={cantidad} onChange={(evento) => setCantidad(evento.target.value)} /></label>}
      <label>Observación<input type="text" maxLength={255} value={observacion} onChange={(evento) => setObservacion(evento.target.value)} /></label>
      {error && <p role="alert">{error}</p>}
      <div className="compra-modal-acciones"><button type="button" className="compra-accion modal-cancelar" aria-label="Cancelar" data-tooltip="Cancelar" disabled={ocupado} onClick={cerrar}><AppIcon name="close" /></button><button type="submit" className="compra-accion modal-aceptar" aria-label="Guardar" data-tooltip="Guardar" disabled={ocupado}><AppIcon name="check" /></button></div>
    </form>
  </dialog>;
}
