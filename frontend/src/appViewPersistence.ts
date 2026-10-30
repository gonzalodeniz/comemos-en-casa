import type { AppView } from "./AppWorkspace";

const STORAGE_KEY = "comemos-en-casa:workspace-view";
const APP_VIEWS: readonly AppView[] = ["meal-planning", "food-catalog", "users"];

function getSessionStorage(): Storage | undefined {
  try {
    return globalThis.sessionStorage;
  } catch {
    return undefined;
  }
}

function isAppView(value: string | null): value is AppView {
  return value !== null && APP_VIEWS.includes(value as AppView);
}

export function restoreAppView(storage = getSessionStorage()): AppView {
  try {
    const value = storage?.getItem(STORAGE_KEY) ?? null;
    return isAppView(value) ? value : "meal-planning";
  } catch {
    return "meal-planning";
  }
}

export function persistAppView(view: AppView, storage = getSessionStorage()): void {
  try {
    storage?.setItem(STORAGE_KEY, view);
  } catch {
    // Workspace navigation should remain usable when browser storage is unavailable.
  }
}
