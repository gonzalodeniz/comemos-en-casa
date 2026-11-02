// Verifica la navegación y composición del espacio de trabajo.
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import AppWorkspace, { type AppView } from "./AppWorkspace";

function workspace(view: AppView, disabled = false, onViewChange = vi.fn()) {
  return <AppWorkspace {...{
    view,
    onViewChange,
    disabled,
    mealPlanning: <section>Weekly calendar content</section>,
    userManagement: <section>User management content</section>,
    shoppingList: <section>Shopping list content</section>,
  }} />;
}

describe("AppWorkspace", () => {
  it("lists weekly planning first and renders only the selected planning view", () => {
    const markup = renderToStaticMarkup(workspace("meal-planning"));

    expect(markup).toContain('aria-label="Menú principal"');
    const navigation = markup.match(/<nav[\s\S]*?<\/nav>/)?.[0] ?? "";
    expect(navigation.indexOf("Plan semanal")).toBeLessThan(navigation.indexOf("Comidas"));
    expect(navigation.indexOf("Comidas")).toBeLessThan(navigation.indexOf("Lista de la compra"));
    expect(navigation.indexOf("Lista de la compra")).toBeLessThan(navigation.indexOf("Gestión de usuarios"));
    expect(markup).toMatch(/aria-current="page"[\s\S]*?<span>Plan semanal<\/span>/);
    expect(markup).toContain("Weekly calendar content");
    expect(markup).not.toContain("User management content");
  });

  it("renders user management separately and marks its menu item as current", () => {
    const markup = renderToStaticMarkup(workspace("users"));

    expect(markup).toMatch(/aria-current="page"[\s\S]*?<span>Gestión de usuarios<\/span>/);
    expect(markup).toContain("User management content");
    expect(markup).not.toContain("Weekly calendar content");
  });

  it("shows the shopping list as its own sidebar view", () => {
    const markup = renderToStaticMarkup(workspace("shopping-list"));

    expect(markup).toMatch(/aria-current="page"[\s\S]*?<span>Lista de la compra<\/span>/);
    expect(markup).toContain("Shopping list content");
    expect(markup).not.toContain("Food catalog content");
  });

  it("disables navigation while an account operation is pending", () => {
    const markup = renderToStaticMarkup(workspace("users", true));

    expect(markup.match(/disabled=""/g)).toHaveLength(5);
  });

  it("provides branded navigation, a working skip-link target and only supported views", () => {
    const markup = renderToStaticMarkup(workspace("meal-planning"));

    expect(markup).toContain("Comemos en casa");
    expect(markup).toContain('href="#workspace-content"');
    expect(markup).toContain('id="workspace-content" tabindex="-1"');
    expect(markup.match(/<button/g)).toHaveLength(6);
    expect(markup).toContain('aria-expanded="false"');
    expect(markup).toContain("Recetas");
    expect(markup).toContain("Lista de la compra");
  });
});
