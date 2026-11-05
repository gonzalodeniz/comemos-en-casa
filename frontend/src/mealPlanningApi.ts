// Define las peticiones HTTP de planificación, recetas y catálogos.
import { apiRequest } from "./api";

export type FoodLabel = { id: string; code: string; name: string; image_url?: string | null; recipe_count?: number };
export type ShoppingCategory = { id: string; name: string };
export type ShoppingProduct = { id: string; name: string };
// Representa un producto agregado a la lista de la compra.
export type ShoppingListItem = { id?: string; product_id: string; quantity: number; unit: string };

/** Consulta los productos y cantidades de la lista de la compra. */
export function obtenerListaCompra(): Promise<{ items: ShoppingListItem[]; purchased_items?: ShoppingListItem[] }> {
  return apiRequest("/shopping-list");
}

/** Marca un elemento de la lista como comprado usando la protección CSRF. */
export function marcarProductoComprado(itemId: string, csrfToken: string): Promise<ShoppingListItem> {
  return apiRequest(`/shopping-list/${itemId}/purchase`, { method: "POST", csrfToken });
}

/** Devuelve un elemento comprado a la lista pendiente con protección CSRF. */
export function desmarcarProductoComprado(itemId: string, csrfToken: string): Promise<ShoppingListItem> {
  return apiRequest(`/shopping-list/${itemId}/unpurchase`, { method: "POST", csrfToken });
}

/** Elimina una entrada concreta de la lista compartida con protección CSRF. */
export function eliminarEntradaListaCompra(itemId: string, csrfToken: string): Promise<null> {
  return apiRequest<null>(`/shopping-list/${itemId}`, { method: "DELETE", csrfToken });
}

export function getShoppingCategories(): Promise<{ categories: ShoppingCategory[] }> {
  return apiRequest("/shopping-categories");
}

export function createShoppingCategory(name: string, csrfToken: string): Promise<ShoppingCategory> {
  return apiRequest("/shopping-categories", { method: "POST", csrfToken, body: { name } });
}

/** Consulta los productos compartidos de una categoría. */
export function getShoppingProducts(categoryId: string): Promise<{ products: ShoppingProduct[] }> {
  return apiRequest(`/shopping-categories/${categoryId}/products`);
}

/** Crea un producto en la categoría usando la protección CSRF de la sesión. */
export function createShoppingProduct(categoryId: string, name: string, csrfToken: string): Promise<ShoppingProduct> {
  return apiRequest(`/shopping-categories/${categoryId}/products`, { method: "POST", csrfToken, body: { name } });
}

/** Añade un producto a la lista y devuelve su cantidad agregada. */
export function agregarProductoListaCompra(productId: string, quantity: number, unit: string, csrfToken: string): Promise<ShoppingListItem> {
  return apiRequest("/shopping-list", { method: "POST", csrfToken, body: { product_id: productId, quantity, unit } });
}

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

export function createFoodLabel(name: string, csrfToken: string, imageToken?: string): Promise<FoodLabel> {
  return apiRequest("/food-labels", { method: "POST", csrfToken, body: { name, ...(imageToken ? { image_token: imageToken } : {}) } });
}

export function updateFoodLabel(id: string, name: string, csrfToken: string, imageToken?: string, removeImage = false): Promise<FoodLabel> {
  return apiRequest(`/food-labels/${id}`, { method: "PATCH", csrfToken, body: { name, ...(imageToken ? { image_token: imageToken } : {}), ...(removeImage ? { remove_image: true } : {}) } });
}

export function prepareFoodImage(dataUrl: string, crop: { x: number; y: number; width: number; height: number }, csrfToken: string): Promise<{ image_token: string; expires_in_seconds: number }> {
  return apiRequest("/food-labels/images/prepare", { method: "POST", csrfToken, body: { data_url: dataUrl, crop } });
}

export function importFoodImageUrl(url: string, csrfToken: string): Promise<{ data_url: string }> {
  return apiRequest("/food-labels/images/import-url", { method: "POST", csrfToken, body: { url } });
}

export function getFoodLabelImpact(id: string): Promise<{ assignment_count: number; recipe_count: number }> {
  return apiRequest(`/food-labels/${id}/deletion-impact`);
}

export function deleteFoodLabel(id: string, csrfToken: string): Promise<void> {
  return apiRequest(`/food-labels/${id}`, { method: "DELETE", csrfToken });
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
