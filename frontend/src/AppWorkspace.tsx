// Organiza la navegación y las vistas del espacio de trabajo.
import { useState, type ReactNode } from "react";
import AppBrand from "./AppBrand";
import AppIcon from "./AppIcon";

export type AppView = "meal-planning" | "food-catalog" | "recipes" | "shopping-list" | "product-catalog" | "backups" | "users" | "kitchen-tips";

type Props = {
  view: AppView;
  onViewChange: (view: AppView) => void;
  disabled: boolean;
  mealPlanning: ReactNode;
  userManagement: ReactNode;
  foodCatalog?: ReactNode;
  recipes?: ReactNode;
  shoppingList?: ReactNode;
  productCatalog?: ReactNode;
  backups?: ReactNode;
  kitchenTips?: ReactNode;
  sessionTools?: ReactNode;
  notifications?: ReactNode;
};

// Define los destinos disponibles en la barra inferior móvil.
const accesosRapidos = [
  ["meal-planning", "calendar", "Plan semanal"],
  ["recipes", "book", "Recetas"],
  ["shopping-list", "shopping-cart", "Lista de la compra"],
  ["product-catalog", "store", "Catálogo de productos"],
] as const;

export default function AppWorkspace({ view, onViewChange, disabled, mealPlanning, userManagement, foodCatalog, recipes, shoppingList, productCatalog, backups, kitchenTips, sessionTools, notifications }: Props) {
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
        <button type="button" aria-current={view === "recipes" ? "page" : undefined} disabled={disabled} onClick={() => { onViewChange("recipes"); setMenuOpen(false); }}>
          <AppIcon name="book" /><span>Recetas</span>
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
          aria-current={view === "shopping-list" ? "page" : undefined}
          disabled={disabled}
          onClick={() => { onViewChange("shopping-list"); setMenuOpen(false); }}
        >
          <AppIcon name="shopping-cart" /><span>Lista de la compra</span>
        </button>
        <button type="button" aria-current={view === "product-catalog" ? "page" : undefined} disabled={disabled} onClick={() => { onViewChange("product-catalog"); setMenuOpen(false); }}>
          <AppIcon name="store" /><span>Catálogo de productos</span>
        </button>
        <button type="button" aria-current={view === "backups" ? "page" : undefined} disabled={disabled} onClick={() => { onViewChange("backups"); setMenuOpen(false); }}>
          <AppIcon name="archive" /><span>Copias de seguridad</span>
        </button>
        <button type="button" aria-current={view === "kitchen-tips" ? "page" : undefined} disabled={disabled} onClick={() => { onViewChange("kitchen-tips"); setMenuOpen(false); }}>
          <AppIcon name="bulb" /><span>Trucos de cocina</span>
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
        {view === "meal-planning" ? mealPlanning : view === "food-catalog" ? foodCatalog : view === "recipes" ? recipes : view === "shopping-list" ? shoppingList : view === "product-catalog" ? productCatalog : view === "backups" ? backups : view === "kitchen-tips" ? kitchenTips : userManagement}
      </div>
      <nav className="accesos-rapidos" aria-label="Accesos rápidos">
        {accesosRapidos.map(([destino, icono, etiqueta]) => (
          <button key={destino} type="button" disabled={disabled} aria-label={etiqueta} aria-current={view === destino ? "page" : undefined}
            onClick={() => { onViewChange(destino); setMenuOpen(false); }}>
            <AppIcon name={icono} />
          </button>
        ))}
      </nav>
    </div>
  );
}
