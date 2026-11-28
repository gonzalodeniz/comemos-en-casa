// Presenta y gestiona el catálogo compartido mediante las operaciones existentes.
import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { ApiError } from "./api";
import ImagenCatalogo, { type RecorteCatalogo } from "./ImagenCatalogo";
import AppIcon from "./AppIcon";
import type { ShoppingCategory, ShoppingProduct, ResultadoBusquedaProducto } from "./mealPlanningApi";

// Describe una actualización de la imagen de un elemento existente.
type CambioImagen = { name?: string; image_token?: string; remove_image?: true };
// Describe una modificación del nombre y, opcionalmente, de la imagen del producto.
type CambioProducto = { name?: string; image_token?: string; remove_image?: true };
// Define los servicios existentes y el estado de carga del catálogo.
type Props = {
  onConsultarUso?: (id: string) => Promise<boolean>;
  onBorrarProducto?: (categoriaId: string, id: string) => Promise<void>;
  categories: ShoppingCategory[];
  cargandoCategorias?: boolean;
  errorCategorias?: string;
  onReintentarCategorias?: () => void;
  onSessionExpired: () => void;
  onCreateCategory: (name: string, token?: string) => Promise<void>;
  onCreateProduct: (categoryId: string, name: string, token?: string) => Promise<ShoppingProduct>;
  onSearchProducts?: (consulta: string) => Promise<{ products: ResultadoBusquedaProducto[] }>;
  onGetProducts: (categoryId: string) => Promise<ShoppingProduct[]>;
  onUpdateCategoryImage: (id: string, cambio: CambioImagen) => Promise<ShoppingCategory>;
  onUpdateProductImage: (categoriaId: string, id: string, cambio: CambioProducto) => Promise<ShoppingProduct>;
  onImportImage: (url: string) => Promise<string>;
  onPrepareImage: (imagen: string, recorte: RecorteCatalogo) => Promise<string>;
};

// Identifica el formulario activo sin presentar acciones no admitidas.
type Editor = { tipo: "categoria" | "producto"; id: string; nombre: string; imagen: boolean; categoriaId?: string } | null;

/** Presenta un editor del catálogo como diálogo modal y devuelve el foco al cerrarlo. */
function ModalCatalogo({ titulo, cerrar, ocupado, children }: { titulo: string; cerrar: () => void; ocupado: boolean; children: ReactNode }) {
  const dialogo = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const origen = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const ventana = dialogo.current;
    ventana?.showModal();
    return () => { if (ventana?.open) ventana.close(); origen?.focus(); };
  }, []);
  return <dialog ref={dialogo} className="catalogo-modal" aria-labelledby="titulo-modal-catalogo" onCancel={(evento) => { evento.preventDefault(); if (!ocupado) cerrar(); }}><h3 id="titulo-modal-catalogo">{titulo}</h3>{children}</dialog>;
}

/** Construye la ruta autenticada de una imagen del catálogo. */
function urlImagen(url: string): string {
  return (import.meta.env.VITE_API_BASE_URL || "/comemos") + "/api/v1" + url;
}

/** Muestra y gestiona categorías, productos y sus imágenes opcionales. */
export default function ProductCatalog({ categories, cargandoCategorias, errorCategorias, onReintentarCategorias, onGetProducts, onSearchProducts, onCreateCategory, onCreateProduct, onUpdateCategoryImage, onUpdateProductImage, onImportImage, onPrepareImage, onSessionExpired, onConsultarUso, onBorrarProducto }: Props) {
  const [categoria, setCategoria] = useState<ShoppingCategory | null>(null);
  const [productos, setProductos] = useState<ShoppingProduct[]>([]);
  const [error, setError] = useState("");
  const [cargando, setCargando] = useState(false);
  const [nombre, setNombre] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [uso, setUso] = useState<boolean | null>(null);
  const [editor, setEditor] = useState<Editor>(null);
  const [imagen, setImagen] = useState("");
  const [recorte, setRecorte] = useState<RecorteCatalogo | null>(null);
  const [leyendo, setLeyendo] = useState(false);
  const [quitar, setQuitar] = useState(false);
  const [versionEditor, setVersionEditor] = useState(0);
  const revision = useRef(0);
  const [busqueda, setBusqueda] = useState("");
  const [revisionBusqueda, setRevisionBusqueda] = useState(0);
  const [respuestaBusqueda, setRespuestaBusqueda] = useState<{ consulta: string; revision: number; productos: ResultadoBusquedaProducto[] | null }>();
  const consulta = busqueda.trim();
  const buscando = !!onSearchProducts && consulta.length >= 3;
  const respuestaVigente = respuestaBusqueda?.consulta === consulta && respuestaBusqueda.revision === revisionBusqueda ? respuestaBusqueda : undefined;

  useEffect(() => {
    if (!buscando || !onSearchProducts) return;
    let vigente = true;
    setRespuestaBusqueda(undefined);
    void onSearchProducts(consulta).then(({ products }) => {
      if (vigente) setRespuestaBusqueda({ consulta, revision: revisionBusqueda, productos: products });
    }).catch((causa: unknown) => {
      if (!vigente) return;
      if (causa instanceof ApiError && causa.status === 401) onSessionExpired();
      setRespuestaBusqueda({ consulta, revision: revisionBusqueda, productos: null });
    });
    return () => { vigente = false; };
  }, [buscando, consulta, onSearchProducts, onSessionExpired, revisionBusqueda]);

  /** Notifica el vencimiento de sesión o presenta un error operativo. */
  function informar(causa: unknown, mensaje: string) {
    if (causa instanceof ApiError && causa.status === 401) onSessionExpired();
    else setError(mensaje);
  }

  /** Abre un editor nuevo sin conservar imágenes de otro formulario. */
  function abrirEditor(valor: Editor) {
    setUso(null);
    setEditor(valor); setImagen(""); setRecorte(null); setLeyendo(false);
    setQuitar(false); setError(""); setNombre(valor?.id ? valor.nombre : ""); setVersionEditor((actual) => actual + 1);
  }

  /** Elimina el producto confirmado sin cerrar el editor si ocurre un error. */
  async function borrarProducto() {
    if (!editor?.categoriaId || !onBorrarProducto || guardando) return;
    setGuardando(true);
    try {
      await onBorrarProducto(editor.categoriaId, editor.id);
      setRevisionBusqueda((actual) => actual + 1);
      setProductos((actuales) => actuales.filter((producto) => producto.id !== editor.id));
      abrirEditor(null);
    } catch (causa) { informar(causa, "No se pudo borrar el producto. Inténtalo de nuevo."); }
    finally { setGuardando(false); }
  }

  /** Consulta el impacto antes de permitir la confirmación del borrado. */
  async function consultarBorrado(id: string) {
    if (!onConsultarUso || guardando) return;
    setGuardando(true); setError("");
    try { setUso(await onConsultarUso(id)); }
    catch (causa) { informar(causa, "No se pudo consultar la lista de la compra. Inténtalo de nuevo."); }
    finally { setGuardando(false); }
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
    if (!nombre.trim() || leyendo || (imagen && !recorte)) {
      setError(leyendo || imagen ? "Espera a que la imagen esté lista antes de guardar." : "Indica un nombre.");
      return;
    }
    if (editor.id && editor.tipo === "categoria" && nombre.trim() === editor.nombre && !imagen && !quitar) { abrirEditor(null); return; }
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
        await onUpdateCategoryImage(editor.id, { ...(nombre.trim() !== editor.nombre ? { name: nombre.trim() } : {}), ...(token ? { image_token: token } : quitar ? { remove_image: true as const } : {}) });
      } else if (editor.categoriaId) {
        const actualizado = await onUpdateProductImage(editor.categoriaId, editor.id, { name: nombre.trim(), ...(token ? { image_token: token } : quitar ? { remove_image: true as const } : {}) });
        setProductos((actuales) => actuales.map((item) => item.id === editor.id ? actualizado : item));
        setRevisionBusqueda((actual) => actual + 1);
      }
      setEditor(null); setImagen(""); setRecorte(null); setNombre("");
    } catch (causa) { informar(causa, causa instanceof ApiError && causa.status === 409 ? (editor.tipo === "categoria" ? "Ya existe una categoría con ese nombre." : "Ya existe un producto con ese nombre.") : "No se pudo guardar. Inténtalo de nuevo."); }
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

  /** Presenta las mismas acciones para productos de una categoría o de una búsqueda. */
  function tarjetasProducto(elementos: (ShoppingProduct & { category_id?: string })[]) {
    return <div className="catalogo-productos-grid">{elementos.map((producto) => <article className="catalogo-productos-tarjeta" key={producto.id}>
        <button className="catalogo-tarjeta-contenido catalogo-producto-activar" type="button" aria-label={"Gestionar imagen de " + producto.name} disabled={guardando} onClick={() => abrirEditor({ tipo: "producto", id: producto.id, nombre: producto.name, imagen: !!producto.image_url, categoriaId: producto.category_id ?? categoria?.id })}>{producto.image_url ? <img src={urlImagen(producto.image_url)} alt="" /> : <span className="catalogo-productos-imagen" aria-hidden="true"><AppIcon name="utensils" /></span>}<strong>{producto.name}</strong></button>
      </article>)}</div>;
  }

  const campoBusqueda = onSearchProducts && <div className="selector-compra-busqueda catalogo-busqueda">
    <input aria-label="Buscar productos" placeholder="Busca tus productos" value={busqueda} onChange={(evento) => setBusqueda(evento.target.value)} />
    {busqueda && <button type="button" className="compra-accion" aria-label="Limpiar búsqueda" onClick={() => { setRespuestaBusqueda(undefined); setBusqueda(""); }}><AppIcon name="close" /></button>}
  </div>;

  // Solo la creación de productos conserva el formulario en línea.
  const editorModal = !!editor && (editor.tipo === "categoria" || !!editor.id);

  return <section className="catalogo-productos">
    {categoria ? <>
      <button className="catalogo-volver" type="button" disabled={guardando} onClick={() => { revision.current++; setCategoria(null); setError(""); abrirEditor(null); }}><AppIcon name="chevron-left" />Volver a categorías</button>
      <div className="catalogo-cabecera"><div><h2>{categoria.name}</h2><p>Productos de esta categoría</p></div>
      {campoBusqueda}<button className="catalogo-crear" type="button" disabled={guardando || cargando} onClick={() => abrirEditor({ tipo: "producto", id: "", nombre: "", imagen: false })}><AppIcon name="plus" />Nuevo producto</button></div>
      {!buscando && (cargando ? <p role="status">Cargando productos…</p> : productos.length === 0 ? <p>No hay productos en esta categoría.</p> : tarjetasProducto(productos))}
    </> : <>
      <div className="catalogo-cabecera"><div className="catalogo-cabecera-contenido"><h2>Catálogo de categorías</h2><p>Organiza tus categorías de productos</p>{campoBusqueda}</div>
      <button className="catalogo-crear" type="button" disabled={guardando || cargandoCategorias || !!errorCategorias} onClick={() => abrirEditor({ tipo: "categoria", id: "", nombre: "", imagen: false })}><AppIcon name="plus" />Nueva categoría</button></div>
      {!buscando && (cargandoCategorias ? <p role="status">Cargando categorías…</p> : errorCategorias ? <div role="alert">{errorCategorias} <button type="button" onClick={onReintentarCategorias}>Reintentar</button></div> : categories.length === 0 ? <p>No hay categorías disponibles.</p> : <div className="catalogo-productos-grid">{[...categories].sort((a, b) => a.name.localeCompare(b.name, "es")).map((elemento) => <article className="catalogo-productos-tarjeta" key={elemento.id}>
        <button className="catalogo-tarjeta-contenido" type="button" disabled={guardando} onClick={() => void abrirCategoria(elemento)}>{elemento.image_url ? <img src={urlImagen(elemento.image_url)} alt="" /> : <span className="catalogo-productos-imagen" aria-hidden="true"><AppIcon name="utensils" /></span>}<strong>{elemento.name}</strong></button>
        <button className="catalogo-accion" type="button" aria-label={"Editar categoría " + elemento.name} title="Editar categoría" disabled={guardando} onClick={() => abrirEditor({ tipo: "categoria", id: elemento.id, nombre: elemento.name, imagen: !!elemento.image_url })}><span aria-hidden="true">⋮</span></button>
      </article>)}</div>)}
    </>}
    {buscando && (!respuestaVigente ? <p role="status">Buscando productos…</p> : respuestaVigente.productos === null ? <p role="alert">No se pudieron buscar los productos. <button type="button" onClick={() => setRevisionBusqueda((actual) => actual + 1)}>Reintentar</button></p> : respuestaVigente.productos.length ? tarjetasProducto(respuestaVigente.productos) : <p role="status">No se encontraron productos.</p>)}
    {error && !editorModal && <p role="alert">{error}</p>}
    {editor && (() => {
      // Comparte el título visible con el nombre accesible del formulario.
      const titulo = editor.tipo === "categoria" ? (editor.id ? "Categoría " + editor.nombre : "Nueva categoría") : (editor.id ? "Producto " + editor.nombre : "Nuevo producto");
      // Mantiene las mismas acciones y campos en el modal y en el editor en línea.
      const formulario = <form className="catalogo-editor" onSubmit={(evento) => void guardar(evento)} aria-label={titulo}>
      {!editorModal && <h3>{titulo}</h3>}
      {editorModal && error && <p role="alert">{error}</p>}
      <label>{editor.tipo === "categoria" ? "Nombre de la categoría" : "Nombre del producto"}<input value={nombre} onChange={(evento) => setNombre(evento.target.value)} maxLength={100} required /></label>
      <ImagenCatalogo key={versionEditor} importar={importar} cambiar={(datos, area, ocupado) => { setImagen(datos); setRecorte(area); setLeyendo(ocupado); if (datos || ocupado) setQuitar(false); }} />
      {editor.imagen && <label><input type="checkbox" checked={quitar} onChange={(evento) => { setQuitar(evento.target.checked); if (evento.target.checked) { setImagen(""); setRecorte(null); setLeyendo(false); setVersionEditor((actual) => actual + 1); } }} />Quitar imagen actual</label>}
      {uso !== null && <div role="group" aria-label="Confirmar borrado"><p>¿Quieres borrar {editor.nombre}?</p><p>{uso ? "El producto está en la lista de la compra. Sus entradas también se borrarán." : "El producto no está en la lista de la compra."}</p></div>}
      {editor.tipo === "producto" && editor.id && uso !== null ? <div className="catalogo-acciones-producto catalogo-confirmar-borrado">
        <button type="button" aria-label="Confirmar borrado" title="Confirmar borrado" disabled={guardando} onClick={() => void borrarProducto()}><AppIcon name="check" /></button>
        <button type="button" aria-label="No borrar" title="No borrar" disabled={guardando} onClick={() => setUso(null)}><AppIcon name="close" /></button>
      </div> : editor.tipo === "producto" && editor.id ? <div className="catalogo-acciones-producto">
        <button type="submit" aria-label="Guardar" title="Guardar" disabled={guardando || leyendo}><AppIcon name="check" /></button>
        <button type="button" aria-label="Cancelar" title="Cancelar" disabled={guardando} onClick={() => abrirEditor(null)}><AppIcon name="close" /></button>
        <button className="catalogo-borrar-producto" type="button" aria-label="Borrar producto" title="Borrar producto" disabled={guardando} onClick={() => void consultarBorrado(editor.id)}><AppIcon name="trash" /></button>
      </div> : <><button type="submit" disabled={guardando || leyendo}>{guardando ? "Guardando…" : "Guardar"}</button><button type="button" disabled={guardando} onClick={() => abrirEditor(null)}>Cancelar</button></>}
    </form>;
      return editorModal ? <ModalCatalogo titulo={titulo} cerrar={() => abrirEditor(null)} ocupado={guardando}>{formulario}</ModalCatalogo> : formulario;
    })()}
  </section>;
}
