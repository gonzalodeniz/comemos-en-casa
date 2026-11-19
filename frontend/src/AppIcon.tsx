// Presenta los iconos utilizados por las vistas de la aplicación.
type IconName = "database" | "download" | "settings" | "calendar" | "repeat" | "users" | "chevron-left" | "chevron-right" | "chevron-up" | "chevron-down" | "plus" | "logout" | "utensils" | "menu" | "edit" | "trash" | "eye" | "shopping-cart" | "check" | "undo" | "clear-list" | "store" | "arrow-left" | "close" | "diana" | "filtros";

const paths: Record<IconName, string> = {
  database: "M4 6c0-4 16-4 16 0s-16 4-16 0Zm0 0v12c0 4 16 4 16 0V6M4 12c0 4 16 4 16 0",
  download: "M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5",
  settings: "M12 8a4 4 0 1 0 0 8 4 4 0 0 0 0-8ZM9 3h6l1 3 3 1 2 5-2 5-3 1-1 3H9l-1-3-3-1-2-5 2-5 3-1 1-3Z",
  check: "M5 12l4 4L19 6",
  undo: "M9 14 4 9l5-5M4 9h10a6 6 0 0 1 0 12h-2",
  "shopping-cart": "M3 3h2l2 11h10l3-8H6M9 20a1 1 0 1 0 0-2 1 1 0 0 0 0 2Zm8 0a1 1 0 1 0 0-2 1 1 0 0 0 0 2Z",
  utensils: "M4 3v6a3 3 0 0 0 6 0V3M7 3v18M16 21V3c-3 2-3 7-3 9h3",
  menu: "M4 6h16M4 12h16M4 18h16",
  calendar: "M8 2v4m8-4v4M3 10h18M5 4h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Zm3 10h2m4 0h2m-8 4h2",
  repeat: "M17 2l4 4-4 4M3 11V9a3 3 0 0 1 3-3h15M7 22l-4-4 4-4m14-1v2a3 3 0 0 1-3 3H3",
  users: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2m20 0v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75M13 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z",
  "chevron-left": "m15 18-6-6 6-6",
  "chevron-right": "m9 18 6-6-6-6",
  "chevron-up": "m6 15 6-6 6 6",
  "chevron-down": "m6 9 6 6 6-6",
  "arrow-left": "M19 12H5m7 7-7-7 7-7",
  // Representa los ajustes disponibles para filtrar el calendario.
  filtros: "M3 7h6m6 0h6M3 17h2m6 0h10M9 7a3 3 0 1 0 6 0 3 3 0 0 0-6 0Zm-4 10a3 3 0 1 0 6 0 3 3 0 0 0-6 0Z",
  // Identifica el acceso a la fecha actual.
  diana: "M12 2v4m0 12v4M2 12h4m12 0h4M20 12a8 8 0 1 0-16 0 8 8 0 0 0 16 0Zm-5 0a3 3 0 1 0-6 0 3 3 0 0 0 6 0Z",
  close: "M6 6l12 12M18 6 6 18",
  plus: "M12 5v14M5 12h14",
  logout: "M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4m7 14 5-5-5-5m5 5H9",
  edit: "M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L8 18l-4 1 1-4Z",
  trash: "M3 6h18m-2 0-.9 14H5.9L5 6m4 0V4h6v2m-5 4v6m4-6v6",
  store: "M3 10h18l-2-6H5l-2 6Zm1 0v10h16V10M9 20v-6h6v6M3 10a2 2 0 0 0 4 0 2 2 0 0 0 4 0 2 2 0 0 0 4 0 2 2 0 0 0 3 1.7A2 2 0 0 0 21 10",
  "clear-list": "M4 5h10M4 10h10M4 15h6M4 20h6m7-7 6 6m0-6-6 6",
  eye: "M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Zm10-2a2 2 0 1 0 0 4 2 2 0 0 0 0-4Z",
};

export default function AppIcon({ name, className = "" }: { name: IconName; className?: string }) {
  return <svg className={`app-icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false"><path d={paths[name]} /></svg>;
}
