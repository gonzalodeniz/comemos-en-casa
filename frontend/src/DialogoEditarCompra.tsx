// Permite editar la cantidad o descripción de un producto pendiente.
import { useEffect, useRef, useState, type FormEvent } from "react";
import type { CambioCantidad, ShoppingListItem } from "./mealPlanningApi";

// Define la entrada y las acciones del diálogo de edición.
type Props = { entrada: ShoppingListItem; guardar: (id: string, cambio: CambioCantidad) => Promise<ShoppingListItem>; alGuardar: (entrada: ShoppingListItem) => void; cerrar: () => void };

/** Edita una cantidad sin descartar los datos si falla la petición. */
export default function DialogoEditarCompra({ entrada, guardar, alGuardar, cerrar }: Props) {
  const ventana = useRef<HTMLDialogElement>(null);
  const enviando = useRef(false);
  const [ocupado, setOcupado] = useState(false);
  const [textoLibre, setTextoLibre] = useState(entrada.quantity_text != null);
  const [texto, setTexto] = useState(entrada.quantity_text ?? "");
  const [cantidad, setCantidad] = useState(String(entrada.quantity));
  const [unidad, setUnidad] = useState(entrada.unit);
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
      const cambio = textoLibre ? { quantity_text: texto.trim() } : { quantity: Number(cantidad), unit: unidad };
      if (textoLibre && !texto.trim()) { setError("Introduce una descripción."); return; }
      alGuardar(await guardar(entrada.id, cambio)); cerrar();
    } catch { setError("No se pudo guardar. Comprueba que no exista otra entrada numérica con la misma unidad."); }
    finally { enviando.current = false; setOcupado(false); }
  }
  return <dialog ref={ventana} aria-labelledby="titulo-editar-compra" onCancel={(evento) => { evento.preventDefault(); if (!enviando.current) cerrar(); }}>
    <form onSubmit={(evento) => void enviar(evento)}>
      <h3 id="titulo-editar-compra">Editar {entrada.product_name ?? "producto"}</h3>
      <label>Tipo de cantidad<select value={textoLibre ? "texto" : "numero"} onChange={(evento) => setTextoLibre(evento.target.value === "texto")}><option value="numero">Cantidad y unidad</option><option value="texto">Texto libre</option></select></label>
      {textoLibre ? <label>Texto libre<input required maxLength={255} value={texto} onChange={(evento) => setTexto(evento.target.value)} /></label> : <><label>Cantidad<input type="number" min="0.01" step="any" required value={cantidad} onChange={(evento) => setCantidad(evento.target.value)} /></label><label>Unidad<select value={unidad} onChange={(evento) => setUnidad(evento.target.value)}><option value="unit">unidad</option><option value="g">g</option><option value="kg">kg</option></select></label></>}
      {error && <p role="alert">{error}</p>}
      <button type="button" className="secondary" disabled={ocupado} onClick={cerrar}>Cancelar</button><button type="submit" disabled={ocupado}>Guardar</button>
    </form>
  </dialog>;
}
