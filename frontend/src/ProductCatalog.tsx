// Presenta y gestiona el catálogo compartido mediante las operaciones existentes.
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { ApiError } from "./api";
import ImagenCatalogo, { type RecorteCatalogo } from "./ImagenCatalogo";
import AppIcon from "./AppIcon";
import type { ShoppingCategory, ShoppingProduct } from "./mealPlanningApi";

// Describe una actualización de la imagen de un elemento existente.
type CambioImagen = { image_token: string } | { remove_image: true };
// Describe una modificación del nombre y, opcionalmente, de la imagen del producto.
type CambioProducto = { name?: string; image_token?: string; remove_image?: true };
// Define los servicios existentes y el estado de carga del catálogo.
type Props = {
  categories: ShoppingCategory[];
  cargandoCategorias?: boolean;
  errorCategorias?: string;
  onReintentarCategorias?: () => void;
  onSessionExpired: () => void;
  onCreateCategory: (name: string, token?: string) => Promise<void>;
  onCreateProduct: (categoryId: string, name: string, token?: string) => Promise<ShoppingProduct>;
  onGetProducts: (categoryId: string) => Promise<ShoppingProduct[]>;
  onUpdateCategoryImage: (id: string, cambio: CambioImagen) => Promise<ShoppingCategory>;
  onUpdateProductImage: (categoriaId: string, id: string, cambio: CambioProducto) => Promise<ShoppingProduct>;
  onImportImage: (url: string) => Promise<string>;
  onPrepareImage: (imagen: string, recorte: RecorteCatalogo) => Promise<string>;
};

// Identifica el formulario activo sin presentar acciones no admitidas.
type Editor = { tipo: "categoria" | "producto"; id: string; nombre: string; imagen: boolean } | null;

/** Presenta el editor de producto como diálogo modal y devuelve el foco al cerrarlo. */
function ModalProducto({ titulo, cerrar, ocupado, children }: { titulo: string; cerrar: () => void; ocupado: boolean; children: ReactNode }) {
  const dialogo = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const origen = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const ventana = dialogo.current;
    ventana?.showModal();
    return () => { if (ventana?.open) ventana.close(); origen?.focus(); };
  }, []);
  return <dialog ref={dialogo} className="catalogo-modal" aria-labelledby="titulo-modal-producto" onCancel={(evento) => { evento.preventDefault(); if (!ocupado) cerrar(); }}><h3 id="titulo-modal-producto">{titulo}</h3>{children}</dialog>;
}

/** Construye la ruta autenticada de una imagen del catálogo. */
function urlImagen(url: string): string {
  return (import.meta.env.VITE_API_BASE_URL || "/comemos") + "/api/v1" + url;
}

/** Muestra y gestiona categorías, productos y sus imágenes opcionales. */
export default function ProductCatalog({ categories, cargandoCategorias, errorCategorias, onReintentarCategorias, onGetProducts, onCreateCategory, onCreateProduct, onUpdateCategoryImage, onUpdateProductImage, onImportImage, onPrepareImage, onSessionExpired }: Props) {
  const [categoria, setCategoria] = useState<ShoppingCategory | null>(null);
  const [productos, setProductos] = useState<ShoppingProduct[]>([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [nombre, setNombre] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [editor, setEditor] = useState<Editor>(null);
  const [imagen, setImagen] = useState("");
  const [recorte, setRecorte] = useState<RecorteCatalogo | null>(null);
  const [leyendo, setLeyendo] = useState(false);
  const [quitar, setQuitar] = useState(false);
  const [versionEditor, setVersionEditor] = useState(0);
  const revision = useRef(0);

  /** Notifica el vencimiento de sesión o presenta un error operativo. */
  function informar(causa: unknown, mensaje: string) {
    if (causa instanceof ApiError && causa.status === 401) onSessionExpired();
    else setError(mensaje);
  }

  /** Abre un editor nuevo sin conservar imágenes de otro formulario. */
  function abrirEditor(valor: Editor) {
    setEditor(valor); setImagen(""); setRecorte(null); setLeyendo(false);
    setQuitar(false); setError(""); setNombre(valor?.id && valor.tipo === "producto" ? valor.nombre : ""); setVersionEditor((actual) => actual + 1);
  }

  /** Importa una imagen y propaga los errores de sesión. */
  async function importar(url: string) {
    try { return await onImportImage(url); }
    catch (causa) { if (causa instanceof ApiError && causa.status === 401) onSessionExpired(); throw causa; }
  }

  /** Guarda una creación o un cambio de imagen con la API existente. */
  async function guardar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    if (!editor || guardando) return;
    if (((!editor.id || editor.tipo === "producto") && !nombre.trim()) || leyendo || (imagen && !recorte)) {
      setError(leyendo || imagen ? "Espera a que la imagen esté lista antes de guardar." : "Indica un nombre.");
      return;
    }
    if (editor.id && editor.tipo === "categoria" && !imagen && !quitar) { setError("Selecciona una imagen o indica que deseas quitarla."); return; }
    setGuardando(true); setError("");
    try {
      const token = imagen && recorte ? await onPrepareImage(imagen, recorte) : undefined;
      if (!editor.id && editor.tipo === "categoria") await onCreateCategory(nombre.trim(), token);
      else if (!editor.id && categoria) {
        const creado = await onCreateProduct(categoria.id, nombre.trim(), token);
        setProductos((actuales) => [...actuales, creado]);
        // La respuesta de creación omite la URL: un fallo de recarga no debe repetir la creación.
        try { setProductos(await onGetProducts(categoria.id)); }
        catch (causa) { informar(causa, "Producto creado; no se pudo actualizar su imagen."); }
      } else if (editor.tipo === "categoria") {
        await onUpdateCategoryImage(editor.id, token ? { image_token: token } : { remove_image: true });
      } else if (categoria) {
        const actualizado = await onUpdateProductImage(categoria.id, editor.id, { name: nombre.trim(), ...(token ? { image_token: token } : quitar ? { remove_image: true as const } : {}) });
        setProductos((actuales) => actuales.map((item) => item.id === editor.id ? actualizado : item));
      }
      setEditor(null); setImagen(""); setRecorte(null); setNombre("");
    } catch (causa) { informar(causa, causa instanceof ApiError && causa.status === 409 ? "Ya existe un producto con ese nombre." : "No se pudo guardar. Inténtalo de nuevo."); }
    finally { setGuardando(false); }
  }

  /** Abre una categoría y descarta respuestas obsoletas de consultas anteriores. */
  async function abrirCategoria(seleccionada: ShoppingCategory) {
    const solicitud = ++revision.current;
    abrirEditor(null); setCategoria(seleccionada); setProductos([]); setError(""); setCargando(true);
    try {
      const resultado = await onGetProducts(seleccionada.id);
      if (solicitud === revision.current) setProductos(resultado);
    } catch (causa) {
      if (solicitud === revision.current) informar(causa, "No se pudieron cargar los productos.");
    } finally { if (solicitud === revision.current) setCargando(false); }
  }

  return <section className="catalogo-productos">
    {categoria ? <>
      <button className="catalogo-volver" type="button" disabled={guardando} onClick={() => { revision.current++; setCategoria(null); setError(""); abrirEditor(null); }}><AppIcon name="chevron-left" />Volver a categorías</button>
      <div className="catalogo-cabecera"><div><h2>{categoria.name}</h2><p>Productos de esta categoría</p></div>
      <button className="catalogo-crear" type="button" disabled={guardando || cargando} onClick={() => abrirEditor({ tipo: "producto", id: "", nombre: "", imagen: false })}><AppIcon name="plus" />Nuevo producto</button></div>
      {cargando ? <p role="status">Cargando productos…</p> : productos.length === 0 ? <p>No hay productos en esta categoría.</p> : <div className="catalogo-productos-grid">{productos.map((producto) => <article className="catalogo-productos-tarjeta" key={producto.id}>
        <button className="catalogo-tarjeta-contenido catalogo-producto-activar" type="button" aria-label={"Gestionar imagen de " + producto.name} disabled={guardando} onClick={() => abrirEditor({ tipo: "producto", id: producto.id, nombre: producto.name, imagen: !!producto.image_url })}>{producto.image_url ? <img src={urlImagen(producto.image_url)} alt="" /> : <span className="catalogo-productos-imagen" aria-hidden="true"><AppIcon name="utensils" /></span>}<strong>{producto.name}</strong></button>
      </article>)}</div>}
    </> : <>
      <div className="catalogo-cabecera"><div><h2>Catálogo de categorías</h2><p>Organiza tus categorías de productos</p></div>
      <button className="catalogo-crear" type="button" disabled={guardando || cargandoCategorias || !!errorCategorias} onClick={() => abrirEditor({ tipo: "categoria", id: "", nombre: "", imagen: false })}><AppIcon name="plus" />Nueva categoría</button></div>
      {cargandoCategorias ? <p role="status">Cargando categorías…</p> : errorCategorias ? <div role="alert">{errorCategorias} <button type="button" onClick={onReintentarCategorias}>Reintentar</button></div> : categories.length === 0 ? <p>No hay categorías disponibles.</p> : <div className="catalogo-productos-grid">{[...categories].sort((a, b) => a.name.localeCompare(b.name, "es")).map((elemento) => <article className="catalogo-productos-tarjeta" key={elemento.id}>
        <button className="catalogo-tarjeta-contenido" type="button" disabled={guardando} onClick={() => void abrirCategoria(elemento)}>{elemento.image_url ? <img src={urlImagen(elemento.image_url)} alt="" /> : <span className="catalogo-productos-imagen" aria-hidden="true"><AppIcon name="utensils" /></span>}<strong>{elemento.name}</strong></button>
        <button className="catalogo-accion" type="button" aria-label={"Gestionar imagen de " + elemento.name} title="Gestionar imagen" disabled={guardando} onClick={() => abrirEditor({ tipo: "categoria", id: elemento.id, nombre: elemento.name, imagen: !!elemento.image_url })}><span aria-hidden="true">⋮</span></button>
      </article>)}</div>}
    </>}
    {error && !(editor?.tipo === "producto" && editor.id) && <p role="alert">{error}</p>}
    {editor && (() => { const formulario = <form className="catalogo-editor" onSubmit={(evento) => void guardar(evento)} aria-label={editor.id && editor.tipo === "producto" ? "Producto " + editor.nombre : editor.id ? "Imagen de " + editor.nombre : editor.tipo === "categoria" ? "Nueva categoría" : "Nuevo producto"}>
      {!(editor.id && editor.tipo === "producto") && <h3>{editor.id ? "Imagen de " + editor.nombre : editor.tipo === "categoria" ? "Nueva categoría" : "Nuevo producto"}</h3>}
      {editor.id && editor.tipo === "producto" && error && <p role="alert">{error}</p>}
      {(!editor.id || editor.tipo === "producto") && <label>{editor.tipo === "categoria" ? "Nombre de la categoría" : "Nombre del producto"}<input value={nombre} onChange={(evento) => setNombre(evento.target.value)} maxLength={100} required /></label>}
      <ImagenCatalogo key={versionEditor} importar={importar} cambiar={(datos, area, ocupado) => { setImagen(datos); setRecorte(area); setLeyendo(ocupado); if (datos || ocupado) setQuitar(false); }} />
      {editor.imagen && <label><input type="checkbox" checked={quitar} onChange={(evento) => { setQuitar(evento.target.checked); if (evento.target.checked) { setImagen(""); setRecorte(null); setLeyendo(false); setVersionEditor((actual) => actual + 1); } }} />Quitar imagen actual</label>}
      <button type="submit" disabled={guardando || leyendo}>{guardando ? "Guardando…" : "Guardar"}</button><button type="button" disabled={guardando} onClick={() => abrirEditor(null)}>Cancelar</button>
    </form>; return editor.id && editor.tipo === "producto" ? <ModalProducto titulo={"Producto " + editor.nombre} cerrar={() => abrirEditor(null)} ocupado={guardando}>{formulario}</ModalProducto> : formulario; })()}
  </section>;
}
