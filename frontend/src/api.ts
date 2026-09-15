import type {
  ApiProblem,
  AssignmentWritePayload,
  AuthenticatedUser,
  CalendarAssignment,
  CalendarContext,
  CalendarWeek,
  RecipeCollection,
  RecipeDetail,
  RecipeSearchResult,
  RecipeStatus,
  RecipeSummary,
} from "./types";

const CALENDAR_API_ROOT = "/api/v1/meal-calendar";
const API_ROOT = "/api/v1";

export class ApiError extends Error {
  readonly problem: ApiProblem;
  readonly status: number;

  constructor(status: number, problem: ApiProblem) {
    super(problem.message);
    this.name = "ApiError";
    this.status = status;
    this.problem = problem;
  }
}

type ErrorPayload = {
  error?: {
    code?: string;
    message?: string;
    retryable?: boolean;
  };
};

type RequestOptions = {
  method?: "DELETE" | "GET" | "PATCH" | "POST" | "PUT";
  body?: unknown;
  signal?: AbortSignal;
};

type ApiRecipe = {
  id: string;
  titulo: string;
  imagenUrl: string;
  estado: RecipeStatus;
};

type ApiRecipeDetail = ApiRecipe & {
  detalle: string;
  ingredientes: Array<{ nombre: string; cantidad?: string | null }>;
  pasos: Array<{ instruccion: string }>;
};

type ApiCollection = {
  id: string;
  nombre: string;
  recetas: ApiRecipe[];
};

async function request<T>(root: string, path: string, { method = "GET", body, signal }: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${root}${path}`, {
    method,
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
      ...(body === undefined ? {} : { "Content-Type": "application/json" }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
    signal,
  });

  if (!response.ok) {
    let payload: ErrorPayload | undefined;
    try {
      payload = (await response.json()) as ErrorPayload;
    } catch {
      // A proxy or unavailable backend may return a non-JSON error page.
    }
    throw new ApiError(response.status, {
      code: payload?.error?.code ?? "request_failed",
      message: payload?.error?.message ?? `La solicitud no se pudo completar (estado ${response.status}).`,
      retryable: payload?.error?.retryable ?? response.status >= 500,
    });
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

const calendarRequest = <T>(path: string, options?: RequestOptions) => request<T>(CALENDAR_API_ROOT, path, options);
const apiRequest = <T>(path: string, options?: RequestOptions) => request<T>(API_ROOT, path, options);

function toRecipeSummary(recipe: ApiRecipe): RecipeSummary {
  return { id: recipe.id, title: recipe.titulo, coverImageUrl: recipe.imagenUrl, status: recipe.estado };
}

function toCollection(collection: ApiCollection): RecipeCollection {
  return { id: collection.id, name: collection.nombre, recipes: collection.recetas.map(toRecipeSummary) };
}

export function getCalendarContext(signal?: AbortSignal): Promise<CalendarContext> {
  return calendarRequest<CalendarContext>("/context", { signal });
}

export function getCalendarWeek(weekStart: string, signal?: AbortSignal): Promise<CalendarWeek> {
  return calendarRequest<CalendarWeek>(`/weeks/${encodeURIComponent(weekStart)}`, { signal });
}

export function searchPublicRecipes(query: string, signal?: AbortSignal): Promise<RecipeSearchResult> {
  const params = new URLSearchParams({ q: query, limit: "20" });
  return calendarRequest<RecipeSearchResult>(`/recipes?${params.toString()}`, { signal });
}

export async function getRecipeCatalogue(query = "", signal?: AbortSignal): Promise<RecipeSummary[]> {
  const params = new URLSearchParams({ q: query, limit: "50" });
  const response = await apiRequest<{ recetas: ApiRecipe[] }>(`/recipes?${params.toString()}`, { signal });
  return response.recetas.map(toRecipeSummary);
}

export async function getPublicRecipe(recipeId: string, signal?: AbortSignal): Promise<RecipeDetail> {
  const recipe = await apiRequest<ApiRecipeDetail>(`/recipes/${encodeURIComponent(recipeId)}`, { signal });
  return {
    ...toRecipeSummary(recipe),
    detail: recipe.detalle,
    ingredients: recipe.ingredientes.map((ingredient) => ({ name: ingredient.nombre, quantity: ingredient.cantidad ?? null })),
    steps: recipe.pasos.map((step) => ({ instruction: step.instruccion })),
  };
}

export async function getCurrentUser(signal?: AbortSignal): Promise<AuthenticatedUser | null> {
  try {
    return await apiRequest<AuthenticatedUser>("/auth/me", { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status === 401) return null;
    throw error;
  }
}

export async function getFavorites(signal?: AbortSignal): Promise<RecipeSummary[]> {
  const response = await apiRequest<{ favoritos: ApiRecipe[] }>("/me/favorites", { signal });
  return response.favoritos.map(toRecipeSummary);
}

export async function setFavorite(recipeId: string, isFavorite: boolean): Promise<void> {
  await apiRequest<void>(`/recipes/${encodeURIComponent(recipeId)}/favorite`, { method: isFavorite ? "PUT" : "DELETE" });
}

export async function getCollections(signal?: AbortSignal): Promise<RecipeCollection[]> {
  const response = await apiRequest<{ colecciones: ApiCollection[] }>("/me/collections", { signal });
  return response.colecciones.map(toCollection);
}

export async function createCollection(name: string): Promise<RecipeCollection> {
  const collection = await apiRequest<ApiCollection>("/me/collections", { method: "POST", body: { nombre: name } });
  return toCollection(collection);
}

export async function addRecipeToCollection(collectionId: string, recipeId: string): Promise<void> {
  await apiRequest<void>(`/me/collections/${encodeURIComponent(collectionId)}/recipes/${encodeURIComponent(recipeId)}`, { method: "POST" });
}

export function createAssignment(payload: AssignmentWritePayload): Promise<CalendarAssignment> {
  return calendarRequest<CalendarAssignment>("/assignments", { method: "POST", body: payload });
}

export function updateAssignment(assignmentId: string, payload: AssignmentWritePayload): Promise<CalendarAssignment> {
  return calendarRequest<CalendarAssignment>(`/assignments/${encodeURIComponent(assignmentId)}`, { method: "PATCH", body: payload });
}

export async function deleteAssignment(assignmentId: string): Promise<void> {
  await calendarRequest<void>(`/assignments/${encodeURIComponent(assignmentId)}`, { method: "DELETE" });
}
