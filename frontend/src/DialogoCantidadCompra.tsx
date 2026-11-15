// Solicita la cantidad de un producto antes de incorporarlo a la compra.
import { useEffect, useRef, useState, type FormEvent } from "react";
import AppIcon from "./AppIcon";
import type { ShoppingListItem, ShoppingProduct } from "./mealPlanningApi";

// Define las unidades y acciones admitidas por la operación existente.
type Unidad = "unit" | "kg" | "g";
type Props = { producto: ShoppingProduct; agregar: (id: string, cantidad: number, unidad: Unidad, texto?: string) => Promise<ShoppingListItem>; alAgregar: (entrada: ShoppingListItem) => void; cerrar: () => void };

/** Presenta un diálogo modal y conserva los valores si falla el envío. */
export default function DialogoCantidadCompra({ producto, agregar, alAgregar, cerrar }: Props) {
  const ventana = useRef<HTMLDialogElement>(null);
  const enviando = useRef(false);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const [cantidad, setCantidad] = useState("1");
  const [modo, setModo] = useState<"texto" | "unit" | "g" | "kg">("unit");
  const textoLibre = modo === "texto";
  const [texto, setTexto] = useState("");

  useEffect(() => {
    const origen = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const dialogo = ventana.current;
    dialogo?.showModal();
    dialogo?.querySelector<HTMLInputElement>("input")?.focus();
    return () => { if (dialogo?.open) dialogo.close(); origen?.focus(); };
  }, []);

  /** Envía una única operación y devuelve la respuesta del servidor. */
  async function enviar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (enviando.current) return;
    enviando.current = true;
    setOcupado(true);
    setError("");
    try {
      if (textoLibre && !texto.trim()) { setError("Introduce una descripción."); return; }
      const medida: Unidad = modo === "texto" ? "unit" : modo === "unit" ? "unit" : modo;
      const entrada = textoLibre ? await agregar(producto.id, 0, "unit", texto.trim()) : await agregar(producto.id, Number(cantidad), medida);
      alAgregar(entrada);
      cerrar();
    } catch {
      setError("No se pudo añadir el producto. Inténtalo de nuevo.");
    } finally {
      enviando.current = false;
      setOcupado(false);
    }
  }

  return <dialog ref={ventana} aria-labelledby="titulo-dialogo-compra" onCancel={(evento) => { evento.preventDefault(); if (!enviando.current) cerrar(); }}>
    <form onSubmit={(evento) => void enviar(evento)}>
      <h3 id="titulo-dialogo-compra">{producto.name}</h3>
      <div className="compra-modos" role="group" aria-label="Tipo de cantidad">{([['texto','T','Texto libre'],['unit','U','Unidades'],['g','gr','Gramos'],['kg','kg','Kilogramos']] as const).map(([valor, etiqueta, ayuda]) => <button key={valor} type="button" className={modo === valor ? "seleccionado" : ""} aria-pressed={modo === valor} aria-label={ayuda} data-tooltip={ayuda} onClick={() => setModo(valor)}>{etiqueta}</button>)}</div>
      {textoLibre ? <label>Texto libre<input required maxLength={255} value={texto} onChange={(evento) => setTexto(evento.target.value)} /></label> : <label>{modo === "unit" ? "Unidades" : modo === "g" ? "Gramos" : "Kilogramos"}<input type="number" required min="0.01" step="any" value={cantidad} onChange={(evento) => setCantidad(evento.target.value)} /></label>}
      {error && <p role="alert">{error}</p>}
      <div className="compra-modal-acciones"><button type="button" className="compra-accion modal-cancelar" aria-label="Cancelar" data-tooltip="Cancelar" disabled={ocupado} onClick={cerrar}><AppIcon name="close" /></button><button type="submit" className="compra-accion modal-aceptar" aria-label="Añadir" data-tooltip="Añadir" disabled={ocupado}><AppIcon name="check" /></button></div>
    </form>
  </dialog>;
}
