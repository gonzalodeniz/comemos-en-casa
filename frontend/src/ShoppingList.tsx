// Presenta categorías y productos del catálogo compartido de compra.
import { useEffect, useState, type FormEvent } from "react";
import type { ShoppingProduct } from "./mealPlanningApi";

export type ShoppingCategory = { id: string; name: string };

type Props = {
  categories: ShoppingCategory[];
  onCreateCategory: (name: string) => void;
  onGetProducts: (categoryId: string) => Promise<ShoppingProduct[]>;
  onCreateProduct: (categoryId: string, name: string) => Promise<ShoppingProduct>;
};

/** Presenta las categorías y permite consultar y crear sus productos. */
export default function ShoppingList({ categories, onCreateCategory, onGetProducts, onCreateProduct }: Props) {
  const [name, setName] = useState("");
  const [products, setProducts] = useState<Record<string, ShoppingProduct[]>>({});
  const [productNames, setProductNames] = useState<Record<string, string>>({});
  const [productErrors, setProductErrors] = useState<Record<string, string>>({});

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

  return <section className="panel">
    <h2>Lista de la compra</h2>
    <form onSubmit={submit}>
      <label>Nombre de la categoría<input aria-label="Nombre de la categoría" value={name} onChange={(event) => setName(event.target.value)} required /></label>
      <button type="submit">Crear categoría</button>
    </form>
    <ul>{categories.map((category) => <li key={category.id}>{category.name}
      {productErrors[category.id] && <p role="alert">{productErrors[category.id]}</p>}
      <ul>{(products[category.id] ?? []).map((product) => <li key={product.id}>{product.name}</li>)}</ul>
      <form onSubmit={(event) => void submitProduct(event, category)}>
        <label>Nombre del producto en {category.name}<input value={productNames[category.id] ?? ""} onChange={(event) => setProductNames((current) => ({ ...current, [category.id]: event.target.value }))} required /></label>
        <button type="submit">Crear producto</button>
      </form>
    </li>)}</ul>
  </section>;
}
