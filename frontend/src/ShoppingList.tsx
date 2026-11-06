// Presenta categorías y productos del catálogo compartido de compra.
import { useEffect, useState, type FormEvent } from "react";
import type { ShoppingListItem, ShoppingProduct } from "./mealPlanningApi";

export type ShoppingCategory = { id: string; name: string };

// Unidades aceptadas por la lista de la compra.
type ShoppingUnit = "unit" | "kg" | "g";

// Describe una copia de receta incluida en la compra.
type RecipeSection = { id: string; name: string; ingredients: { id: string; text: string; purchased: boolean }[] };

type Props = {
  categories: ShoppingCategory[];
  onCreateCategory: (name: string) => void;
  onGetProducts: (categoryId: string) => Promise<ShoppingProduct[]>;
  onCreateProduct: (categoryId: string, name: string) => Promise<ShoppingProduct>;
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
export default function ShoppingList({ categories, onCreateCategory, onGetProducts, onCreateProduct, onAddToShoppingList, onGetShoppingList, onMarkPurchased, onUnmarkPurchased, onDeleteItem, onMarkRecipeIngredient, onUnmarkRecipeIngredient, onDeleteRecipeIngredient, onDeleteRecipeSection }: Props) {
  const [name, setName] = useState("");
  const [products, setProducts] = useState<Record<string, ShoppingProduct[]>>({});
  const [productNames, setProductNames] = useState<Record<string, string>>({});
  const [productErrors, setProductErrors] = useState<Record<string, string>>({});
  const [listaCompra, setListaCompra] = useState<Record<string, ShoppingListItem>>({});
  const [comprados, setComprados] = useState<Record<string, ShoppingListItem>>({});
  const [seccionesRecetas, setSeccionesRecetas] = useState<RecipeSection[]>([]);
  const [errorListaCompra, setErrorListaCompra] = useState("");

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

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onCreateCategory(name.trim());
  }

  /** Crea un producto y lo incorpora a la categoría visible. */
  async function submitProduct(event: FormEvent<HTMLFormElement>, category: ShoppingCategory) {
    event.preventDefault();
    try {
      const product = await onCreateProduct(category.id, (productNames[category.id] ?? "").trim());
      setProducts((current) => ({ ...current, [category.id]: [...(current[category.id] ?? []), product] }));
      setProductNames((current) => ({ ...current, [category.id]: "" }));
      setProductErrors((current) => ({ ...current, [category.id]: "" }));
    } catch {
      setProductErrors((current) => ({ ...current, [category.id]: "No se pudo crear el producto. Inténtalo de nuevo." }));
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
    await onMarkRecipeIngredient?.(ingredientId);
    setSeccionesRecetas((actuales) => actuales.map((seccion) => ({
      ...seccion,
      ingredients: seccion.ingredients.map((ingrediente) =>
        ingrediente.id === ingredientId ? { ...ingrediente, purchased: true } : ingrediente),
    })));
  }

  /** Devuelve a pendiente un ingrediente comprado de receta. */
  async function desmarcarIngredienteReceta(ingredientId: string) {
    await onUnmarkRecipeIngredient?.(ingredientId);
    setSeccionesRecetas((actuales) => actuales.map((seccion) => ({
      ...seccion,
      ingredients: seccion.ingredients.map((ingrediente) =>
        ingrediente.id === ingredientId ? { ...ingrediente, purchased: false } : ingrediente),
    })));
  }

  /** Elimina una línea concreta de ingredientes de receta. */
  async function eliminarIngredienteReceta(ingredientId: string) {
    await onDeleteRecipeIngredient?.(ingredientId);
    setSeccionesRecetas((actuales) => actuales.map((seccion) => ({
      ...seccion,
      ingredients: seccion.ingredients.filter((ingrediente) => ingrediente.id !== ingredientId),
    })));
  }

  /** Elimina una sección completa de receta. */
  async function eliminarSeccionReceta(sectionId: string) {
    await onDeleteRecipeSection?.(sectionId);
    setSeccionesRecetas((actuales) => actuales.filter((seccion) => seccion.id !== sectionId));
  }

  return <section className="panel">
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
      <label>Nombre de la categoría<input aria-label="Nombre de la categoría" value={name} onChange={(event) => setName(event.target.value)} required /></label>
      <button type="submit">Crear categoría</button>
    </form>
    <ul>{categories.map((category) => <li key={category.id}>{category.name}
      {productErrors[category.id] && <p role="alert">{productErrors[category.id]}</p>}
      <ul>{(products[category.id] ?? []).map((product) => <li key={product.id}>{product.name}
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
        <button type="submit">Crear producto</button>
      </form>
    </li>)}</ul>
    <section aria-label="Lista de la compra"><h3>Lista de la compra</h3>
      {errorListaCompra && <p role="alert">{errorListaCompra}</p>}
      <h4>Pendientes</h4><ul>{Object.values(listaCompra).map((item) => <li key={`${item.product_id}:${item.unit}`}>
        {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id}: {item.quantity} {item.unit === "unit" ? "unidad" : item.unit}
        {item.id && <button type="button" onClick={() => void markPurchased(item)}>Marcar {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} como comprado</button>}
        {item.id && onDeleteItem && <button type="button" onClick={() => void deleteItem(item, false)}>Eliminar {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} de Pendientes</button>}
      </li>)}</ul>
      <h4>Comprados</h4><ul>{Object.values(comprados).map((item) => <li key={`${item.product_id}:${item.unit}`}>
        {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id}: {item.quantity} {item.unit === "unit" ? "unidad" : item.unit}
        {item.id && onUnmarkPurchased && <button type="button" onClick={() => void unmarkPurchased(item)}>Desmarcar {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} como pendiente</button>}
        {item.id && onDeleteItem && <button type="button" onClick={() => void deleteItem(item, true)}>Eliminar {Object.values(products).flat().find((producto) => producto.id === item.product_id)?.name ?? item.product_id} de Comprados</button>}
      </li>)}</ul>
    </section>
  </section>;
}
