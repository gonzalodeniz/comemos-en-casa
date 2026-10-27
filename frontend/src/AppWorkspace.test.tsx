import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";
import AppWorkspace, { type AppView } from "./AppWorkspace";

function workspace(view: AppView, disabled = false, onViewChange = vi.fn()) {
  return AppWorkspace({
    view,
    onViewChange,
    disabled,
    mealPlanning: <section>Weekly calendar content</section>,
    userManagement: <section>User management content</section>,
  });
}

describe("AppWorkspace", () => {
  it("lists weekly planning first and renders only the selected planning view", () => {
    const markup = renderToStaticMarkup(workspace("meal-planning"));

    expect(markup).toContain('aria-label="Menú principal"');
    expect(markup.indexOf("Plan semanal")).toBeLessThan(markup.indexOf("Gestión de usuarios"));
    expect(markup).toContain('aria-current="page">Plan semanal</button>');
    expect(markup).toContain("Weekly calendar content");
    expect(markup).not.toContain("User management content");
  });

  it("renders user management separately and marks its menu item as current", () => {
    const markup = renderToStaticMarkup(workspace("users"));

    expect(markup).toContain('aria-current="page">Gestión de usuarios</button>');
    expect(markup).toContain("User management content");
    expect(markup).not.toContain("Weekly calendar content");
  });

  it("requests the matching view from each navigation button", () => {
    const onViewChange = vi.fn();
    const navigation = workspace("meal-planning", false, onViewChange).props.children[0];
    const buttons = navigation.props.children;

    buttons[1].props.onClick();
    buttons[0].props.onClick();

    expect(onViewChange.mock.calls).toEqual([["users"], ["meal-planning"]]);
  });

  it("disables navigation while an account operation is pending", () => {
    const markup = renderToStaticMarkup(workspace("users", true));

    expect(markup.match(/disabled=""/g)).toHaveLength(2);
  });
});
