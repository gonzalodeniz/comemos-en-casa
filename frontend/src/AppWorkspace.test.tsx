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
  }} />;
}

describe("AppWorkspace", () => {
  it("lists weekly planning first and renders only the selected planning view", () => {
    const markup = renderToStaticMarkup(workspace("meal-planning"));

    expect(markup).toContain('aria-label="Menú principal"');
    expect(markup.indexOf("Plan semanal")).toBeLessThan(markup.indexOf("Gestión de usuarios"));
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

  it("disables navigation while an account operation is pending", () => {
    const markup = renderToStaticMarkup(workspace("users", true));

    expect(markup.match(/disabled=""/g)).toHaveLength(2);
  });

  it("provides branded navigation, a working skip-link target and only supported views", () => {
    const markup = renderToStaticMarkup(workspace("meal-planning"));

    expect(markup).toContain("Comemos en casa");
    expect(markup).toContain('href="#workspace-content"');
    expect(markup).toContain('id="workspace-content" tabindex="-1"');
    expect(markup.match(/<button/g)).toHaveLength(3);
    expect(markup).toContain('aria-expanded="false"');
    expect(markup).not.toContain("Recetas");
    expect(markup).not.toContain("Lista de la compra");
  });
});
