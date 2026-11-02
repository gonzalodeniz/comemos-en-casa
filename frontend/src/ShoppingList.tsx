import { useState, type FormEvent } from "react";

export type ShoppingCategory = { id: string; name: string };

type Props = {
  categories: ShoppingCategory[];
  onCreateCategory: (name: string) => void;
};

export default function ShoppingList({ categories, onCreateCategory }: Props) {
  const [name, setName] = useState("");

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onCreateCategory(name.trim());
  }

  return <section className="panel">
    <h2>Lista de la compra</h2>
    <form onSubmit={submit}>
      <label>Nombre de la categoría<input aria-label="Nombre de la categoría" value={name} onChange={(event) => setName(event.target.value)} required /></label>
      <button type="submit">Crear categoría</button>
    </form>
    <ul>{categories.map((category) => <li key={category.id}>{category.name}</li>)}</ul>
  </section>;
}
