// @vitest-environment jsdom
// Verifica la navegación y composición del espacio de trabajo.
import { fireEvent, render, within } from "@testing-library/react";
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
  // Comprueba la navegación directa desde los cuatro accesos de la barra inferior.
  it("abre las cuatro vistas desde la barra inferior", () => {
    const cambiarVista = vi.fn();
    const { container, unmount } = render(workspace("users", false, cambiarVista));
    try {
      const barra = within(container).getByRole("navigation", { name: "Accesos rápidos" });
      const accesos = within(barra);
      expect(barra.textContent?.trim()).toBe("");
      expect(accesos.getAllByRole("button")).toHaveLength(4);
      for (const [nombre, vista] of [
        [/Plan semanal/, "meal-planning"], [/Recetas/, "recipes"],
        [/Lista de la compra/, "shopping-list"], [/Catálogo de productos/, "product-catalog"],
      ] as const) {
        fireEvent.click(accesos.getByRole("button", { name: nombre }));
        expect(cambiarVista).toHaveBeenLastCalledWith(vista);
      }
    } finally {
      unmount();
    }
  });

  // Comprueba que el menú desplegable conserva los cuatro destinos tras añadir la barra.
  it("abre las cuatro vistas desde el menú desplegable", () => {
    const cambiarVista = vi.fn();
    const { container, unmount } = render(workspace("users", false, cambiarVista));
    try {
      const espacio = within(container);
      const interruptor = espacio.getByRole("button", { name: "Menú principal" });
      for (const [nombre, vista] of [
        ["Plan semanal", "meal-planning"], ["Recetas", "recipes"],
        ["Lista de la compra", "shopping-list"], ["Catálogo de productos", "product-catalog"],
      ] as const) {
        fireEvent.click(interruptor);
        expect(interruptor.getAttribute("aria-expanded")).toBe("true");
        const menu = espacio.getByRole("navigation", { name: "Menú principal" });
        fireEvent.click(within(menu).getByRole("button", { name: nombre }));
        expect(cambiarVista).toHaveBeenLastCalledWith(vista);
        expect(interruptor.getAttribute("aria-expanded")).toBe("false");
      }
    } finally {
      unmount();
    }
  });

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

  it("shows the backup view in the sidebar and renders its selected content", () => {
    const markup = renderToStaticMarkup(<AppWorkspace {...{
      view: "backups",
      onViewChange: vi.fn(),
      disabled: false,
      mealPlanning: <section>Weekly calendar content</section>,
      userManagement: <section>User management content</section>,
      backups: <section>Backup management content</section>,
    }} />);

    expect(markup).toMatch(/aria-current="page"[\s\S]*?<span>Copias de seguridad<\/span>/);
    expect(markup).toContain("Backup management content");
  });

  it("shows the kitchen tips view in the sidebar and renders its selected content", () => {
    const markup = renderToStaticMarkup(<AppWorkspace {...{
      view: "kitchen-tips",
      onViewChange: vi.fn(),
      disabled: false,
      mealPlanning: <section>Weekly calendar content</section>,
      userManagement: <section>User management content</section>,
      kitchenTips: <section>Kitchen tips content</section>,
    }} />);

    expect(markup).toMatch(/aria-current="page"[\s\S]*?<span>Trucos de cocina<\/span>/);
    expect(markup).toContain("Kitchen tips content");
  });

  it("disables navigation while an account operation is pending", () => {
    const markup = renderToStaticMarkup(workspace("users", true));

    expect(markup.match(/<nav[^>]*aria-label="Menú principal"[\s\S]*?<\/nav>/)?.[0].match(/disabled=""/g)).toHaveLength(8);
    expect(markup.match(/<nav[^>]*aria-label="Accesos rápidos"[\s\S]*?<\/nav>/)?.[0].match(/disabled=""/g)).toHaveLength(4);
  });

  it("provides branded navigation, a working skip-link target and only supported views", () => {
    const markup = renderToStaticMarkup(workspace("meal-planning"));

    expect(markup).toContain("Comemos en casa");
    expect(markup).toContain('href="#workspace-content"');
    expect(markup).toContain('id="workspace-content" tabindex="-1"');
    expect(markup.match(/<aside[\s\S]*?<\/aside>/)?.[0].match(/<button/g)).toHaveLength(9);
    expect(markup).toContain('aria-expanded="false"');
    expect(markup).toContain("Recetas");
    expect(markup).toContain("Lista de la compra");
  });
});
