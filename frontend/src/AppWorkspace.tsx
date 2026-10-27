import type { ReactNode } from "react";

export type AppView = "meal-planning" | "users";

type Props = {
  view: AppView;
  onViewChange: (view: AppView) => void;
  disabled: boolean;
  mealPlanning: ReactNode;
  userManagement: ReactNode;
};

export default function AppWorkspace({ view, onViewChange, disabled, mealPlanning, userManagement }: Props) {
  return (
    <div className="app-workspace">
      <nav className="app-navigation panel" aria-label="Menú principal">
        <button
          type="button"
          aria-current={view === "meal-planning" ? "page" : undefined}
          disabled={disabled}
          onClick={() => onViewChange("meal-planning")}
        >
          Plan semanal
        </button>
        <button
          type="button"
          aria-current={view === "users" ? "page" : undefined}
          disabled={disabled}
          onClick={() => onViewChange("users")}
        >
          Gestión de usuarios
        </button>
      </nav>
      <div className="workspace-content">
        {view === "meal-planning" ? mealPlanning : userManagement}
      </div>
    </div>
  );
}
