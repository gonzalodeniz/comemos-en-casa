// Permite elegir progresivamente una categoría y un producto de compra.
import { useEffect, useRef, useState } from "react";
import AppIcon from "./AppIcon";
import type { ShoppingCategory } from "./ShoppingList";
import type { ShoppingProduct } from "./mealPlanningApi";

// Define los datos y servicios necesarios para seleccionar un producto.
type Props = {
  categorias: ShoppingCategory[];
  consultar: (id: string) => Promise<ShoppingProduct[]>;
  buscar?: (texto: string) => Promise<ShoppingProduct[]>;
  seleccionar: (producto: ShoppingProduct) => void;
  errorSesion?: (error: unknown) => void;
};

/** Presenta categorías o productos y descarta consultas obsoletas. */
export default function SelectorCompra({ categorias, consultar, buscar, seleccionar, errorSesion }: Props) {
  const [categoria, setCategoria] = useState<ShoppingCategory | null>(null);
  const [productos, setProductos] = useState<ShoppingProduct[]>([]);
  const [estado, setEstado] = useState<"espera" | "cargando" | "listo" | "error">("espera");
  const [revision, setRevision] = useState(0);
  const [recogido, setRecogido] = useState(false);
  const [busqueda, setBusqueda] = useState("");
  const [resultadosBusqueda, setResultadosBusqueda] = useState<ShoppingProduct[]>([]);
  const consultarRef = useRef(consultar);
  const buscarRef = useRef(buscar);
  buscarRef.current = buscar;
  const errorRef = useRef(errorSesion);
  consultarRef.current = consultar;
  errorRef.current = errorSesion;

  useEffect(() => {
    const texto = busqueda.trim();
    if (texto.length < 3 || !buscarRef.current) { setResultadosBusqueda([]); return; }
    let vigente = true;
    setResultadosBusqueda([]);
    void buscarRef.current(texto).then((resultado) => { if (vigente) setResultadosBusqueda(resultado); }).catch((error: unknown) => { if (vigente) errorRef.current?.(error); });
    return () => { vigente = false; };
  }, [busqueda]);

  useEffect(() => {
    if (!categoria) return;
    let vigente = true;
    setEstado("cargando");
    setProductos([]);
    void consultarRef.current(categoria.id).then((resultado) => {
      if (vigente) { setProductos(resultado); setEstado("listo"); }
    }).catch((error: unknown) => {
      if (vigente) { errorRef.current?.(error); setEstado("error"); }
    });
    return () => { vigente = false; };
  }, [categoria, revision]);

  return <section className="selector-compra" aria-label="Añadir productos">
    <div className="selector-compra-cabecera"><h3>Añadir productos</h3><span className="selector-compra-acciones">
      <input aria-label="Buscar productos" value={busqueda} onChange={(evento) => setBusqueda(evento.target.value)} />
      {categoria && <button type="button" className="compra-accion" aria-label="Volver a categorías" data-tooltip="Volver a categorías" onClick={() => setCategoria(null)}><AppIcon name="arrow-left" /></button>}
      <button type="button" className="compra-accion" aria-expanded={!recogido} aria-label={recogido ? "Mostrar" : "Recoger"} data-tooltip={recogido ? "Mostrar" : "Recoger"} onClick={() => setRecogido(!recogido)}><AppIcon name={recogido ? "chevron-down" : "chevron-up"} /></button></span>
    </div>
    {!recogido && <div className="selector-compra-contenido">
      {busqueda.trim().length >= 3 ? <div className="selector-compra-cuadricula">{resultadosBusqueda.map((producto) => <button type="button" className="selector-compra-tarjeta" key={producto.id} onClick={() => seleccionar(producto)}>{producto.name}</button>)}</div> : categoria ? <>
        <h4>{categoria.name}</h4>
        {estado === "cargando" && <p role="status">Cargando productos…</p>}
        {estado === "error" && <div role="alert">No se pudieron cargar los productos. <button type="button" onClick={() => setRevision((actual) => actual + 1)}>Reintentar</button></div>}
        {estado === "listo" && productos.length === 0 && <p>No hay productos en esta categoría.</p>}
        {estado === "listo" && <div className="selector-compra-cuadricula">{productos.map((producto) => <button type="button" className="selector-compra-tarjeta" key={producto.id} onClick={() => seleccionar(producto)}>{producto.image_url && <img alt="" src={`${import.meta.env.VITE_API_BASE_URL || "/comemos"}/api/v1${producto.image_url}`} />}<span>{producto.name}</span></button>)}</div>}
      </> : <>{categorias.length === 0 && <p>No hay categorías disponibles.</p>}<div className="selector-compra-cuadricula">{categorias.map((item) => <button type="button" className="selector-compra-tarjeta" key={item.id} onClick={() => setCategoria(item)}>{item.image_url && <img alt="" src={`${import.meta.env.VITE_API_BASE_URL || "/comemos"}/api/v1${item.image_url}`} />}<span>{item.name}</span></button>)}</div></>}
    </div>}
  </section>;
}
