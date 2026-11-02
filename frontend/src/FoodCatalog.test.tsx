// Verifica los componentes del catálogo de alimentos.
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import { FoodCard, filterAndSortFoods } from "./FoodCatalog";

describe("FoodCard", () => {
  it("exposes edit and delete actions and opens recipes from the food", () => {
    const onOpenRecipes = vi.fn();
    const card = FoodCard({ label: { id: "1", code: "x", name: "Pasta" }, busy: false, onEdit: vi.fn(), onRemove: vi.fn(), onOpenRecipes });
    card.props.children[0].props.onClick();
    const markup = renderToStaticMarkup(<FoodCard label={{ id: "1", code: "x", name: "Pasta" }} busy={false} onEdit={vi.fn()} onRemove={vi.fn()} onOpenRecipes={onOpenRecipes} />);
    expect(markup).toContain('aria-label="Editar Pasta"');
    expect(markup).toContain('aria-label="Eliminar Pasta"');
    expect(markup).toContain('class="food-card-open"');
    expect(markup).toContain('class="dish-image"');
    expect(onOpenRecipes).toHaveBeenCalledWith("1");
  });
});

describe("filterAndSortFoods", () => {
  const food = (id: string, name: string) => ({ id, code: id, name });

  it("sorts without mutating the input, using case-insensitive Spanish ordering", () => {
    const labels = [food("1", "Zanahoria"), food("2", "ñame"), food("3", "Naranja"), food("4", "Árbol"), food("5", "almendra")];
    expect(filterAndSortFoods(labels, "").map((label) => label.name)).toEqual(["almendra", "Árbol", "Naranja", "ñame", "Zanahoria"]);
    expect(labels.map((label) => label.id)).toEqual(["1", "2", "3", "4", "5"]);
  });

  it("keeps results ordered after creation, renaming and case-insensitive filtering", () => {
    const initial = [food("1", "Tomate"), food("2", "Arroz")];
    const created = [...initial, food("3", "Atún")];
    expect(filterAndSortFoods(created, "").map((label) => label.name)).toEqual(["Arroz", "Atún", "Tomate"]);
    const renamed = created.map((label) => label.id === "1" ? { ...label, name: "Aceituna" } : label);
    expect(filterAndSortFoods(renamed, "A").map((label) => label.name)).toEqual(["Aceituna", "Arroz", "Atún"]);
  });
});
