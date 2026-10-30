import { useState, type ReactNode } from "react";
import AppBrand from "./AppBrand";
import AppIcon from "./AppIcon";

export type AppView = "meal-planning" | "food-catalog" | "users";

type Props = {
  view: AppView;
  onViewChange: (view: AppView) => void;
  disabled: boolean;
  mealPlanning: ReactNode;
  userManagement: ReactNode;
  foodCatalog?: ReactNode;
  sessionTools?: ReactNode;
  notifications?: ReactNode;
};

export default function AppWorkspace({ view, onViewChange, disabled, mealPlanning, userManagement, foodCatalog, sessionTools, notifications }: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  return (
    <div className="app-workspace">
      <a className="skip-link" href="#workspace-content">Ir al contenido</a>
      <aside className="app-sidebar">
        <div className="sidebar-header"><AppBrand /><button className="mobile-menu-toggle" type="button" aria-label="Menú principal" aria-expanded={menuOpen} aria-controls="mobile-navigation" onClick={() => setMenuOpen(!menuOpen)}><AppIcon name="menu" /></button></div>
        <div id="mobile-navigation" className={`sidebar-menu${menuOpen ? " is-open" : ""}`}><nav className="app-navigation" aria-label="Menú principal">
        <button
          type="button"
          aria-current={view === "meal-planning" ? "page" : undefined}
          disabled={disabled}
          onClick={() => { onViewChange("meal-planning"); setMenuOpen(false); }}
        >
          <AppIcon name="calendar" /><span>Plan semanal</span>
        </button>
        <button
          type="button"
          aria-current={view === "food-catalog" ? "page" : undefined}
          disabled={disabled}
          onClick={() => { onViewChange("food-catalog"); setMenuOpen(false); }}
        >
          <AppIcon name="utensils" /><span>Comidas</span>
        </button>
        <button
          type="button"
          aria-current={view === "users" ? "page" : undefined}
          disabled={disabled}
          onClick={() => { onViewChange("users"); setMenuOpen(false); }}
        >
          <AppIcon name="users" /><span>Gestión de usuarios</span>
        </button>
        </nav>
        <div className="sidebar-note"><p className="eyebrow">Cada día, juntos</p><p>Un espacio para organizar las comidas de tu familia.</p></div>
        {sessionTools && <div className="sidebar-session">{sessionTools}</div>}</div>
      </aside>
      <div className="workspace-content" id="workspace-content" tabIndex={-1}>
        {notifications}
        {view === "meal-planning" ? mealPlanning : view === "food-catalog" ? foodCatalog : userManagement}
      </div>
    </div>
  );
}
