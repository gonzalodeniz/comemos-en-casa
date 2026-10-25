import { afterEach, describe, expect, it, vi } from "vitest";
import {
  applyMealPlanning,
  getFoodLabels,
  getMealPlanning,
  previewMealPlanning,
  type MealPlanningOperation,
} from "./mealPlanningApi";

afterEach(() => vi.unstubAllGlobals());

const operation: MealPlanningOperation = {
  action: "assign",
  start_date: "2026-11-02",
  slot: "dinner",
  label_id: "label-1",
  repeat: { interval_weeks: 2, end_date: "2026-11-30" },
};

describe("meal planning API client", () => {
  it("loads the food-label catalog using the shared authenticated client", async () => {
    const response = { labels: [{ id: "label-1", code: "fish", name: "Fish" }] };
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(response), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(getFoodLabels()).resolves.toEqual(response);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/food-labels");
    expect(init.method).toBe("GET");
    expect(init.credentials).toBe("include");
  });

  it("requests an inclusive planning range with encoded calendar-date parameters", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ assignments: [] }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await getMealPlanning("2026-11-02", "2026-11-08");

    const [url] = fetchMock.mock.calls[0] as [string, RequestInit];
    const parsed = new URL(url, "http://localhost");
    expect(parsed.pathname).toContain("/api/v1/meal-planning");
    expect(parsed.searchParams.get("start_date")).toBe("2026-11-02");
    expect(parsed.searchParams.get("end_date")).toBe("2026-11-08");
  });

  it("sends the preview operation and CSRF token without a confirmation flag", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ preview_token: "preview-1" }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(previewMealPlanning(operation, "csrf-1")).resolves.toMatchObject({
      preview_token: "preview-1",
    });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/meal-planning/preview");
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init.body))).toEqual(operation);
  });

  it("applies only the operation bound to its preview token", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ changed_count: 2 }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(applyMealPlanning(operation, "preview-1", "csrf-1")).resolves.toMatchObject({
      changed_count: 2,
    });

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-1");
    expect(JSON.parse(String(init.body))).toEqual({
      ...operation,
      confirmed: true,
      preview_token: "preview-1",
    });
  });
});
