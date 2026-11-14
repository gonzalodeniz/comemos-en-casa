// Solicita la cantidad de un producto antes de incorporarlo a la compra.
import { useEffect, useRef, useState, type FormEvent } from "react";
import type { ShoppingListItem, ShoppingProduct } from "./mealPlanningApi";

// Define las unidades y acciones admitidas por la operación existente.
type Unidad = "unit" | "kg" | "g";
type Props = { producto: ShoppingProduct; agregar: (id: string, cantidad: number, unidad: Unidad) => Promise<ShoppingListItem>; alAgregar: (entrada: ShoppingListItem) => void; cerrar: () => void };

/** Presenta un diálogo modal y conserva los valores si falla el envío. */
export default function DialogoCantidadCompra({ producto, agregar, alAgregar, cerrar }: Props) {
  const ventana = useRef<HTMLDialogElement>(null);
  const enviando = useRef(false);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState("");
  const [cantidad, setCantidad] = useState("1");
  const [unidad, setUnidad] = useState<Unidad>("unit");

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
      const entrada = await agregar(producto.id, Number(cantidad), unidad);
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
      <label>Cantidad<input type="number" required min="0.01" step="any" value={cantidad} onChange={(evento) => setCantidad(evento.target.value)} /></label>
      <label>Unidad<select value={unidad} onChange={(evento) => setUnidad(evento.target.value as Unidad)}><option value="unit">unidad</option><option value="kg">kg</option><option value="g">g</option></select></label>
      {error && <p role="alert">{error}</p>}
      <button type="button" className="secondary" disabled={ocupado} onClick={cerrar}>Cancelar</button>
      <button type="submit" disabled={ocupado}>Añadir</button>
    </form>
  </dialog>;
}
