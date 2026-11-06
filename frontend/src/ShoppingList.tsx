// Presenta categorías y productos del catálogo compartido de compra.
import { useEffect, useRef, useState, type FormEvent } from "react";
import Cropper from "react-easy-crop";
import type { ShoppingListItem, ShoppingProduct } from "./mealPlanningApi";
import ToastMessage from "./ToastMessage";

export type ShoppingCategory = { id: string; name: string; image_url?: string | null };

// Unidades aceptadas por la lista de la compra.
type ShoppingUnit = "unit" | "kg" | "g";

// Describe una copia de receta incluida en la compra.
type RecipeSection = { id: string; name: string; ingredients: { id: string; text: string; purchased: boolean }[] };

/** Resuelve una imagen autenticada de la API bajo la ruta configurada. */
function urlImagenApi(url: string): string {
  return `${import.meta.env.VITE_API_BASE_URL || "/comemos"}/api/v1${url}`;
}

type Props = {
  categories: ShoppingCategory[];
  onCreateCategory: (name: string, imageToken?: string) => void | Promise<void>;
  onGetProducts: (categoryId: string) => Promise<ShoppingProduct[]>;
  onCreateProduct: (categoryId: string, name: string, imageToken?: string) => Promise<ShoppingProduct>;
  onPrepareImage?: (dataUrl: string, crop: { x: number; y: number; width: number; height: number }) => Promise<string>;
  onImportImage?: (url: string) => Promise<string>;
  onUpdateProductImage?: (categoryId: string, productId: string, change: { image_token: string } | { remove_image: true }) => Promise<ShoppingProduct>;
  onUpdateCategoryImage?: (categoryId: string, change: { image_token: string } | { remove_image: true }) => Promise<ShoppingCategory>;
  onAddToShoppingList?: (productId: string, quantity: number, unit: ShoppingUnit) => Promise<ShoppingListItem>;
  onGetShoppingList?: () => Promise<{ items: ShoppingListItem[]; purchased_items?: ShoppingListItem[]; recipe_sections?: RecipeSection[] }>;
  onMarkRecipeIngredient?: (ingredientId: string) => Promise<unknown>;
  onUnmarkRecipeIngredient?: (ingredientId: string) => Promise<unknown>;
  onDeleteRecipeIngredient?: (ingredientId: string) => Promise<unknown>;
  onDeleteRecipeSection?: (sectionId: string) => Promise<unknown>;
  onMarkPurchased?: (itemId: string) => Promise<ShoppingListItem>;
  onUnmarkPurchased?: (itemId: string) => Promise<ShoppingListItem>;
  onDeleteItem?: (itemId: string) => Promise<null>;
};

/** Presenta las categorías y permite consultar y crear sus productos. */
export default function ShoppingList({ categories, onCreateCategory, onGetProducts, onCreateProduct, onPrepareImage, onImportImage, onUpdateProductImage, onUpdateCategoryImage, onAddToShoppingList, onGetShoppingList, onMarkPurchased, onUnmarkPurchased, onDeleteItem, onMarkRecipeIngredient, onUnmarkRecipeIngredient, onDeleteRecipeIngredient, onDeleteRecipeSection }: Props) {
  const [name, setName] = useState("");
  const [products, setProducts] = useState<Record<string, ShoppingProduct[]>>({});
  const [productNames, setProductNames] = useState<Record<string, string>>({});
  const [productErrors, setProductErrors] = useState<Record<string, string>>({});
  const [listaCompra, setListaCompra] = useState<Record<string, ShoppingListItem>>({});
  const [comprados, setComprados] = useState<Record<string, ShoppingListItem>>({});
  const [seccionesRecetas, setSeccionesRecetas] = useState<RecipeSection[]>([]);
  const [errorListaCompra, setErrorListaCompra] = useState("");
  const [errorReceta, setErrorReceta] = useState("");
  const [imagenProducto, setImagenProducto] = useState("");
  const [productoEditado, setProductoEditado] = useState<string | null>(null);
  const [productoImagenParaQuitar, setProductoImagenParaQuitar] = useState<string | null>(null);
  const [categoriaEditada, setCategoriaEditada] = useState<string | null>(null);
  const [categoriaImagenParaQuitar, setCategoriaImagenParaQuitar] = useState<string | null>(null);
  const [categoriaImagen, setCategoriaImagen] = useState<string | null>(null);
  const [leyendoImagen, setLeyendoImagen] = useState(false);
  const revisionLectura = useRef(0);
  const [urlImagen, setUrlImagen] = useState("");
  const [recorte, setRecorte] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [cropArea, setCropArea] = useState<{ x: number; y: number; width: number; height: number } | null>(null);

  /** Sincroniza la imagen del producto en las secciones compartidas de compra. */
  function sincronizarImagenLista(productId: string, imageUrl?: string | null) {
    const actualizar = (items: Record<string, ShoppingListItem>) => Object.fromEntries(Object.entries(items).map(([key, item]) => [key, item.product_id === productId ? { ...item, image_url: imageUrl } : item]));
    setListaCompra(actualizar);
    setComprados(actualizar);
  }

  /** Lee el archivo seleccionado para previsualizarlo y recortarlo. */
  function leerImagenProducto(categoryId: string, file?: File) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setProductErrors((current) => ({ ...current, [categoryId]: "Selecciona una imagen válida." }));
      return;
    }
    const revision = ++revisionLectura.current;
    if (categoryId.startsWith("producto:")) setProductoImagenParaQuitar(null);
    if (categoryId.startsWith("categoria:")) setCategoriaImagenParaQuitar(null);
    setCategoriaImagen(categoryId);
    setImagenProducto("");
    setLeyendoImagen(true);
    setCropArea(null);
    const reader = new FileReader();
    reader.onload = () => { if (revision === revisionLectura.current) { setImagenProducto(String(reader.result)); setLeyendoImagen(false); } };
    reader.onerror = () => {
      if (revision !== revisionLectura.current) return;
      setLeyendoImagen(false);
      setProductErrors((current) => ({ ...current, [categoryId]: "No se pudo leer la imagen." }));
    };
    reader.readAsDataURL(file);
  }

  /** Importa una imagen usando el servicio seguro de la aplicación. */
  async function importarImagenProducto(categoryId: string) {
    if (!onImportImage) return;
    const revision = ++revisionLectura.current;
    setCategoriaImagen(categoryId);
    setLeyendoImagen(true);
    try {
      const imagen = await onImportImage(urlImagen);
      if (revision !== revisionLectura.current) return;
      if (categoryId.startsWith("producto:")) setProductoImagenParaQuitar(null);
      if (categoryId.startsWith("categoria:")) setCategoriaImagenParaQuitar(null);
      setCategoriaImagen(categoryId);
      setCropArea(null);
      setImagenProducto(imagen);
    } catch {
      if (revision !== revisionLectura.current) return;
      setProductErrors((current) => ({ ...current, [categoryId]: "No se pudo importar la imagen." }));
    } finally {
      if (revision === revisionLectura.current) setLeyendoImagen(false);
    }
  }

  // Carga los elementos compartidos al entrar en la vista.
  useEffect(() => {
    if (!onGetShoppingList) return;
    void onGetShoppingList().then(({ items, purchased_items = [], recipe_sections = [] }) => {
      setListaCompra(Object.fromEntries(items.map((item) => [`${item.product_id}:${item.unit}`, item])));
      setComprados(Object.fromEntries(purchased_items.map((item) => [`${item.product_id}:${item.unit}`, item])));
      setSeccionesRecetas(recipe_sections);
    }).catch(() => setErrorListaCompra("No se pudo cargar la lista de la compra."));
  }, [onGetShoppingList]);

  // Carga el catálogo de productos cuando cambia la lista de categorías.
  useEffect(() => {
    categories.forEach((category) => {
      void onGetProducts(category.id).then((items) => {
        setProducts((current) => ({ ...current, [category.id]: items }));
        setProductErrors((current) => ({ ...current, [category.id]: "" }));
      }).catch(() => {
        setProductErrors((current) => ({ ...current, [category.id]: "No se pudieron cargar los productos." }));
      });
    });
  }, [categories]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (categoriaImagen === "nueva-categoria" && (leyendoImagen || (imagenProducto && !cropArea))) {
      setProductErrors((current) => ({ ...current, "nueva-categoria": "Espera a que la imagen esté lista antes de guardar." }));
      return;
    }
    let token: string | undefined;
    try {
      token = categoriaImagen === "nueva-categoria" && imagenProducto && cropArea && onPrepareImage ? await onPrepareImage(imagenProducto, cropArea) : undefined;
    } catch {
      setProductErrors((current) => ({ ...current, "nueva-categoria": "No se pudo preparar la imagen. Inténtalo de nuevo." }));
      return;
    }
    try {
      if (token) await onCreateCategory(name.trim(), token);
      else await onCreateCategory(name.trim());
      if (categoriaImagen === "nueva-categoria") {
        setImagenProducto("");
        setCropArea(null);
        setCategoriaImagen(null);
      }
    } catch {
      setProductErrors((current) => ({ ...current, "nueva-categoria": "No se pudo crear la categoría." }));
    }
  }

  /** Crea un producto y lo incorpora a la categoría visible. */
  async function submitProduct(event: FormEvent<HTMLFormElement>, category: ShoppingCategory) {
    event.preventDefault();
    if (categoriaImagen === category.id && (leyendoImagen || (imagenProducto && !cropArea))) {
      setProductErrors((current) => ({ ...current, [category.id]: "Espera a que la imagen esté lista antes de guardar." }));
      return;
    }
    try {
      let imageToken: string | undefined;
      if (categoriaImagen === category.id && imagenProducto && cropArea && onPrepareImage) {
        try {
          imageToken = await onPrepareImage(imagenProducto, cropArea);
        } catch {
          setProductErrors((current) => ({ ...current, [category.id]: "No se pudo preparar la imagen. Inténtalo de nuevo." }));
          return;
        }
      }
      const nombre = (productNames[category.id] ?? "").trim();
      const product = imageToken ? await onCreateProduct(category.id, nombre, imageToken) : await onCreateProduct(category.id, nombre);
      if (categoriaImagen === category.id) {
        setImagenProducto("");
        setCropArea(null);
        setCategoriaImagen(null);
      }
      setProducts((current) => ({ ...current, [category.id]: [...(current[category.id] ?? []), product] }));
      setProductNames((current) => ({ ...current, [category.id]: "" }));
      setProductErrors((current) => ({ ...current, [category.id]: "" }));
    } catch {
      setProductErrors((current) => ({ ...current, [category.id]: "No se pudo crear el producto. Inténtalo de nuevo." }));
    }
  }

  /** Guarda el recorte preparado como imagen de un producto existente. */
  async function guardarImagenProducto(categoryId: string, product: ShoppingProduct) {
    if (categoriaImagen === `producto:${product.id}` && leyendoImagen) {
      setProductErrors((current) => ({ ...current, [`producto:${product.id}`]: "Espera a que la imagen esté lista antes de guardar." }));
      return;
    }
    if (productoImagenParaQuitar === product.id) {
      await quitarImagenProducto(categoryId, product);
      setProductoImagenParaQuitar(null);
      return;
    }
    if (!onPrepareImage || !onUpdateProductImage || categoriaImagen !== `producto:${product.id}` || !imagenProducto || !cropArea || leyendoImagen) return;
    try {
      const token = await onPrepareImage(imagenProducto, cropArea);
      const actualizado = await onUpdateProductImage(categoryId, product.id, { image_token: token });
      setProducts((current) => ({ ...current, [categoryId]: (current[categoryId] ?? []).map((item) => item.id === product.id ? actualizado : item) }));
      sincronizarImagenLista(product.id, actualizado.image_url);
    } catch {
      setProductErrors((current) => ({ ...current, [categoryId]: "No se pudo guardar la imagen." }));
    }
  }

  /** Quita la imagen guardada de un producto existente. */
  async function quitarImagenProducto(categoryId: string, product: ShoppingProduct) {
    if (!onUpdateProductImage) return;
    try {
      const actualizado = await onUpdateProductImage(categoryId, product.id, { remove_image: true });
      setProducts((current) => ({ ...current, [categoryId]: (current[categoryId] ?? []).map((item) => item.id === product.id ? actualizado : item) }));
      sincronizarImagenLista(product.id, actualizado.image_url);
    } catch {
      setProductErrors((current) => ({ ...current, [categoryId]: "No se pudo quitar la imagen." }));
    }
  }

  /** Guarda el recorte preparado como imagen de una categoría existente. */
  async function guardarImagenCategoria(category: ShoppingCategory) {
    if (categoriaImagen === `categoria:${category.id}` && leyendoImagen) {
      setProductErrors((current) => ({ ...current, [`categoria:${category.id}`]: "Espera a que la imagen esté lista antes de guardar." }));
      return;
    }
    if (categoriaImagenParaQuitar === category.id) {
      await quitarImagenCategoria(category);
      setCategoriaImagenParaQuitar(null);
      return;
    }
    if (!onPrepareImage || !onUpdateCategoryImage || categoriaImagen !== `categoria:${category.id}` || !imagenProducto || !cropArea || leyendoImagen) return;
    try {
      const token = await onPrepareImage(imagenProducto, cropArea);
      await onUpdateCategoryImage(category.id, { image_token: token });
    } catch {
      setProductErrors((current) => ({ ...current, [category.id]: "No se pudo guardar la imagen." }));
    }
  }

  /** Quita la imagen guardada de una categoría existente. */
  async function quitarImagenCategoria(category: ShoppingCategory) {
    if (!onUpdateCategoryImage) return;
    try {
      await onUpdateCategoryImage(category.id, { remove_image: true });
    } catch {
      setProductErrors((current) => ({ ...current, [category.id]: "No se pudo quitar la imagen." }));
    }
  }

  /** Envía al callback la cantidad y unidad elegidas para un producto existente. */
  async function submitShoppingListItem(event: FormEvent<HTMLFormElement>, product: ShoppingProduct) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const item = await onAddToShoppingList?.(product.id, Number(formData.get("quantity")), formData.get("unit") as ShoppingUnit);
    if (item) setListaCompra((actual) => ({ ...actual, [`${item.product_id}:${item.unit}`]: item }));
  }

  /** Marca una entrada pendiente como comprada y la conserva en la sección inferior. */
  async function markPurchased(item: ShoppingListItem) {
    if (!item.id || !onMarkPurchased) return;
    const updated = await onMarkPurchased(item.id);
    const key = `${item.product_id}:${item.unit}`;
    setListaCompra((current) => { const next = { ...current }; delete next[key]; return next; });
    setComprados((current) => ({ ...current, [key]: updated }));
  }

  /** Desmarca un producto comprado y lo devuelve a la sección de pendientes. */
  async function unmarkPurchased(item: ShoppingListItem) {
    if (!item.id || !onUnmarkPurchased) return;
    const updated = await onUnmarkPurchased(item.id);
    const key = `${item.product_id}:${item.unit}`;
    setComprados((current) => { const next = { ...current }; delete next[key]; return next; });
    setListaCompra((current) => ({ ...current, [key]: updated }));
  }

  /** Elimina una entrada de la sección correspondiente tras confirmarla en la API. */
  async function deleteItem(item: ShoppingListItem, purchased: boolean) {
    if (!item.id || !onDeleteItem) return;
    await onDeleteItem(item.id);
    const key = `${item.product_id}:${item.unit}`;
    if (purchased) setComprados((current) => { const next = { ...current }; delete next[key]; return next; });
    else setListaCompra((current) => { const next = { ...current }; delete next[key]; return next; });
  }

  /** Marca como comprado un ingrediente de receta concreto. */
  async function marcarIngredienteReceta(ingredientId: string) {
    try { await onMarkRecipeIngredient?.(ingredientId); } catch (error) { setErrorReceta(error instanceof Error ? error.message : "No se pudo actualizar el ingrediente."); return; }
    setSeccionesRecetas((actuales) => actuales.map((seccion) => ({
      ...seccion,
      ingredients: seccion.ingredients.map((ingrediente) =>
        ingrediente.id === ingredientId ? { ...ingrediente, purchased: true } : ingrediente),
    })));
  }

  /** Devuelve a pendiente un ingrediente comprado de receta. */
  async function desmarcarIngredienteReceta(ingredientId: string) {
    try { await onUnmarkRecipeIngredient?.(ingredientId); } catch (error) { setErrorReceta(error instanceof Error ? error.message : "No se pudo actualizar el ingrediente."); return; }
    setSeccionesRecetas((actuales) => actuales.map((seccion) => ({
      ...seccion,
      ingredients: seccion.ingredients.map((ingrediente) =>
        ingrediente.id === ingredientId ? { ...ingrediente, purchased: false } : ingrediente),
    })));
  }

  /** Elimina una línea concreta de ingredientes de receta. */
  async function eliminarIngredienteReceta(ingredientId: string) {
    try { await onDeleteRecipeIngredient?.(ingredientId); } catch (error) { setErrorReceta(error instanceof Error ? error.message : "No se pudo eliminar el ingrediente."); return; }
    setSeccionesRecetas((actuales) => actuales.map((seccion) => ({
      ...seccion,
      ingredients: seccion.ingredients.filter((ingrediente) => ingrediente.id !== ingredientId),
    })));
  }

  /** Elimina una sección completa de receta. */
  async function eliminarSeccionReceta(sectionId: string) {
    try { await onDeleteRecipeSection?.(sectionId); } catch (error) { setErrorReceta(error instanceof Error ? error.message : "No se pudo eliminar la sección."); return; }
    setSeccionesRecetas((actuales) => actuales.filter((seccion) => seccion.id !== sectionId));
  }

  return <section className="panel">
    {errorReceta && <ToastMessage kind="error" onClose={() => setErrorReceta("")}>{errorReceta}</ToastMessage>}
    <h2>Lista de la compra</h2>
    {seccionesRecetas.map((seccion) => <section key={seccion.id} aria-label={seccion.name}>
      <h3>{seccion.name}</h3>
      <button type="button" onClick={() => void eliminarSeccionReceta(seccion.id)}>Eliminar sección {seccion.name}</button>
      <ul>{seccion.ingredients.map((ingrediente) => <li key={ingrediente.id}>{ingrediente.text}
        {ingrediente.purchased
          ? <button type="button" onClick={() => void desmarcarIngredienteReceta(ingrediente.id)}>Desmarcar {ingrediente.text} como comprado</button>
          : <button type="button" onClick={() => void marcarIngredienteReceta(ingrediente.id)}>Marcar {ingrediente.text} como comprado</button>}
        <button type="button" onClick={() => void eliminarIngredienteReceta(ingrediente.id)}>Eliminar {ingrediente.text}</button>
      </li>)}</ul>
    </section>)}
    <form onSubmit={submit}>
      {productErrors["nueva-categoria"] && <p role="alert">{productErrors["nueva-categoria"]}</p>}
      <label>Nombre de la categoría<input aria-label="Nombre de la categoría" value={name} onChange={(event) => setName(event.target.value)} required /></label>
      <label tabIndex={0} onPaste={(event) => leerImagenProducto("nueva-categoria", Array.from(event.clipboardData.files).find((file) => file.type.startsWith("image/")))} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); leerImagenProducto("nueva-categoria", event.dataTransfer.files[0]); }}>Imagen de la categoría<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => leerImagenProducto("nueva-categoria", event.target.files?.[0])} /></label>
      <label>URL de imagen de la categoría<input type="url" value={urlImagen} onChange={(event) => setUrlImagen(event.target.value)} /></label><button type="button" onClick={() => void importarImagenProducto("nueva-categoria")}>Importar imagen de categoría</button>
      {categoriaImagen === "nueva-categoria" && imagenProducto && <><img src={imagenProducto} alt="Vista previa de la categoría" /><div className="crop-area" aria-label="Recortar imagen"><Cropper image={imagenProducto} crop={recorte} zoom={zoom} aspect={1} onCropChange={setRecorte} onZoomChange={setZoom} onCropComplete={(_area, pixels) => setCropArea(pixels)} /></div><label>Zoom<input type="range" min={1} max={3} step={0.05} value={zoom} onChange={(event) => setZoom(Number(event.target.value))} /></label></>}
      <button type="submit">Crear categoría</button>
    </form>
    <ul>{categories.map((category) => <li key={category.id}>{category.image_url && <img src={urlImagenApi(category.image_url)} alt={category.name} />}{category.name}
      {productErrors[`categoria:${category.id}`] && <p role="alert">{productErrors[`categoria:${category.id}`]}</p>}
      <button type="button" onClick={() => setCategoriaEditada(category.id)}>Gestionar imagen de {category.name}</button>
      {categoriaEditada === category.id && <><label tabIndex={0} onPaste={(event) => leerImagenProducto(`categoria:${category.id}`, Array.from(event.clipboardData.files).find((file) => file.type.startsWith("image/")))} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); leerImagenProducto(`categoria:${category.id}`, event.dataTransfer.files[0]); }}>Imagen de {category.name}<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => leerImagenProducto(`categoria:${category.id}`, event.target.files?.[0])} /></label>{categoriaImagen === `categoria:${category.id}` && imagenProducto && <><img src={imagenProducto} alt={`Vista previa de ${category.name}`} /><div className="crop-area"><Cropper image={imagenProducto} crop={recorte} zoom={zoom} aspect={1} onCropChange={setRecorte} onZoomChange={setZoom} onCropComplete={(_area, pixels) => setCropArea(pixels)} /></div><label>Zoom de {category.name}<input type="range" min={1} max={3} step={0.05} value={zoom} onChange={(event) => setZoom(Number(event.target.value))} /></label></>}</>}
      {categoriaEditada === category.id && <button type="button" onClick={() => void guardarImagenCategoria(category)}>Guardar imagen de {category.name}</button>}
      {categoriaEditada === category.id && <><label>URL de imagen de {category.name}<input type="url" value={urlImagen} onChange={(event) => setUrlImagen(event.target.value)} /></label><button type="button" onClick={() => void importarImagenProducto(`categoria:${category.id}`)}>Importar imagen de {category.name}</button></>}
      {categoriaEditada === category.id && category.image_url && <button type="button" onClick={() => setCategoriaImagenParaQuitar(category.id)}>Quitar imagen de {category.name}</button>}
      {categoriaEditada === category.id && categoriaImagenParaQuitar === category.id && <p>La imagen se quitará al guardar.</p>}
      {productErrors[category.id] && <p role="alert">{productErrors[category.id]}</p>}
      <ul>{(products[category.id] ?? []).map((product) => <li key={product.id}>{product.image_url && <img src={urlImagenApi(product.image_url)} alt={product.name} />}{product.name}
          {productErrors[`producto:${product.id}`] && <p role="alert">{productErrors[`producto:${product.id}`]}</p>}
          <button type="button" onClick={() => setProductoEditado(product.id)}>Gestionar imagen de {product.name}</button>
          {productoEditado === product.id && <><label tabIndex={0} onPaste={(event) => leerImagenProducto(`producto:${product.id}`, Array.from(event.clipboardData.files).find((file) => file.type.startsWith("image/")))} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); leerImagenProducto(`producto:${product.id}`, event.dataTransfer.files[0]); }}>Imagen de {product.name}<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => leerImagenProducto(`producto:${product.id}`, event.target.files?.[0])} /></label>{categoriaImagen === `producto:${product.id}` && imagenProducto && <><img src={imagenProducto} alt={`Vista previa de ${product.name}`} /><div className="crop-area"><Cropper image={imagenProducto} crop={recorte} zoom={zoom} aspect={1} onCropChange={setRecorte} onZoomChange={setZoom} onCropComplete={(_area, pixels) => setCropArea(pixels)} /></div><label>Zoom de {product.name}<input type="range" min={1} max={3} step={0.05} value={zoom} onChange={(event) => setZoom(Number(event.target.value))} /></label></>}</>}
          {productoEditado === product.id && <button type="button" onClick={() => void guardarImagenProducto(category.id, product)}>Guardar imagen de {product.name}</button>}
          {productoEditado === product.id && <><label>URL de imagen de {product.name}<input type="url" value={urlImagen} onChange={(event) => setUrlImagen(event.target.value)} /></label><button type="button" onClick={() => void importarImagenProducto(`producto:${product.id}`)}>Importar imagen de {product.name}</button></>}
          {productoEditado === product.id && product.image_url && <button type="button" onClick={() => setProductoImagenParaQuitar(product.id)}>Quitar imagen de {product.name}</button>}
          {productoEditado === product.id && productoImagenParaQuitar === product.id && <p>La imagen se quitará al guardar.</p>}
          <form onSubmit={(event) => void submitShoppingListItem(event, product)}>
          <label>Cantidad de {product.name}<input aria-label={`Cantidad de ${product.name}`} name="quantity" type="number" step="any" required /></label>
          <label>Unidad de {product.name}<select aria-label={`Unidad de ${product.name}`} name="unit" defaultValue="unit">
            <option value="unit">unidad</option><option value="kg">kg</option><option value="g">g</option>
          </select></label>
          <button type="submit">Añadir {product.name} a la lista</button>
        </form>
      </li>)}</ul>
      <form onSubmit={(event) => void submitProduct(event, category)}>
        <label>Nombre del producto en {category.name}<input value={productNames[category.id] ?? ""} onChange={(event) => setProductNames((current) => ({ ...current, [category.id]: event.target.value }))} required /></label>
        <label tabIndex={0} onPaste={(event) => leerImagenProducto(category.id, Array.from(event.clipboardData.files).find((file) => file.type.startsWith("image/")))} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); leerImagenProducto(category.id, event.dataTransfer.files[0]); }}>Imagen del producto<input type="file" accept="image/png,image/jpeg,image/webp" onChange={(event) => leerImagenProducto(category.id, event.target.files?.[0])} /></label>
        <label>URL de imagen del producto<input type="url" value={urlImagen} onChange={(event) => setUrlImagen(event.target.value)} /></label><button type="button" onClick={() => void importarImagenProducto(category.id)}>Importar imagen</button>
        {categoriaImagen === category.id && imagenProducto && <><img src={imagenProducto} alt="Vista previa del producto" /><div className="crop-area" aria-label="Recortar imagen"><Cropper image={imagenProducto} crop={recorte} zoom={zoom} aspect={1} onCropChange={setRecorte} onZoomChange={setZoom} onCropComplete={(_area, pixels) => setCropArea(pixels)} /></div><label>Zoom<input aria-label="Zoom" type="range" min={1} max={3} step={0.05} value={zoom} onChange={(event) => setZoom(Number(event.target.value))} /></label></>}
        <button type="submit">Crear producto</button>
      </form>
    </li>)}</ul>
    <section aria-label="Lista de la compra"><h3>Lista de la compra</h3>
      {errorListaCompra && <p role="alert">{errorListaCompra}</p>}
      <h4>Pendientes</h4><ul>{Object.values(listaCompra).map((item) => <li key={`${item.product_id}:${item.unit}`}>
        {item.image_url && <img src={urlImagenApi(item.image_url)} alt={item.product_name ?? Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} />}
        {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id}: {item.quantity} {item.unit === "unit" ? "unidad" : item.unit}
        {item.id && <button type="button" onClick={() => void markPurchased(item)}>Marcar {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} como comprado</button>}
        {item.id && onDeleteItem && <button type="button" onClick={() => void deleteItem(item, false)}>Eliminar {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} de Pendientes</button>}
      </li>)}</ul>
      <h4>Comprados</h4><ul>{Object.values(comprados).map((item) => <li key={`${item.product_id}:${item.unit}`}>
        {item.image_url && <img src={urlImagenApi(item.image_url)} alt={item.product_name ?? Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} />}
        {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id}: {item.quantity} {item.unit === "unit" ? "unidad" : item.unit}
        {item.id && onUnmarkPurchased && <button type="button" onClick={() => void unmarkPurchased(item)}>Desmarcar {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} como pendiente</button>}
        {item.id && onDeleteItem && <button type="button" onClick={() => void deleteItem(item, true)}>Eliminar {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} de Comprados</button>}
      </li>)}</ul>
    </section>
  </section>;
}
