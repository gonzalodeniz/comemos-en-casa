import { describe, expect, it } from "vitest";
import { persistAppView, restoreAppView } from "./appViewPersistence";

function storageWith(value: string | null = null): Storage {
  const entries = new Map<string, string>();
  if (value !== null) entries.set("comemos-en-casa:workspace-view", value);
  return {
    getItem: (key) => entries.get(key) ?? null,
    setItem: (key, nextValue) => { entries.set(key, nextValue); },
    removeItem: (key) => { entries.delete(key); },
    clear: () => entries.clear(),
    key: (index) => [...entries.keys()][index] ?? null,
    get length() { return entries.size; },
  };
}

describe("workspace view persistence", () => {
  it("restores the saved food catalog view", () => {
    expect(restoreAppView(storageWith("food-catalog"))).toBe("food-catalog");
  });

  it("falls back to meal planning for an invalid stored value", () => {
    expect(restoreAppView(storageWith("unknown-view"))).toBe("meal-planning");
  });

  it("persists a selected view for the next page load", () => {
    const storage = storageWith();

    persistAppView("food-catalog", storage);

    expect(restoreAppView(storage)).toBe("food-catalog");
  });
});
