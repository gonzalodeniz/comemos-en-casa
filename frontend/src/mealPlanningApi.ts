import { apiRequest } from "./api";

export type FoodLabel = { id: string; code: string; name: string };
export type MealSlot = "lunch" | "dinner";
export type MealAssignment = {
  id: string;
  date: string;
  slot: MealSlot;
  label: FoodLabel;
};
export type MealPlanningResponse = {
  start_date: string;
  end_date: string;
  today: string;
  timezone: "Atlantic/Canary";
  assignments: MealAssignment[];
};
export type MealPlanningOperation = {
  action: "assign" | "delete";
  start_date: string;
  slot: MealSlot;
  label_id: string;
  repeat: null | { interval_weeks: number; end_date: string };
};
export type MealPlanningPreviewEntry = {
  date: string;
  slot: MealSlot;
  change: "assign" | "replace" | "unchanged" | "delete" | "no_op";
  current_label: FoodLabel | null;
  resulting_label: FoodLabel | null;
};
export type MealPlanningPreview = {
  operation: MealPlanningOperation;
  dates: MealPlanningPreviewEntry[];
  changed_dates: string[];
  change_count: number;
  changed_count: number;
  requires_confirmation: boolean;
  preview_token: string;
};
export type MealPlanningOperationResult = {
  operation: MealPlanningOperation;
  changed_dates: string[];
  changed_count: number;
};

export function getFoodLabels(): Promise<{ labels: FoodLabel[] }> {
  return apiRequest("/food-labels");
}

export function getMealPlanning(
  startDate: string,
  endDate: string,
): Promise<MealPlanningResponse> {
  const query = new URLSearchParams({ start_date: startDate, end_date: endDate });
  return apiRequest(`/meal-planning?${query.toString()}`);
}

export function previewMealPlanning(
  operation: MealPlanningOperation,
  csrfToken: string,
): Promise<MealPlanningPreview> {
  return apiRequest("/meal-planning/preview", {
    method: "POST",
    csrfToken,
    body: operation,
  });
}

export function applyMealPlanning(
  operation: MealPlanningOperation,
  previewToken: string,
  csrfToken: string,
): Promise<MealPlanningOperationResult> {
  return apiRequest("/meal-planning/operations", {
    method: "POST",
    csrfToken,
    body: { ...operation, confirmed: true, preview_token: previewToken },
  });
}
