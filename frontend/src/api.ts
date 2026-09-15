import type {
  ApiProblem,
  AssignmentWritePayload,
  CalendarAssignment,
  CalendarContext,
  CalendarWeek,
  RecipeDetail,
  RecipeSearchResult,
} from "./types";

const API_ROOT = "/api/v1/meal-calendar";

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
  method?: "DELETE" | "GET" | "PATCH" | "POST";
  body?: unknown;
  signal?: AbortSignal;
};

async function request<T>(path: string, { method = "GET", body, signal }: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_ROOT}${path}`, {
    method,
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
      message: payload?.error?.message ?? `Request failed with status ${response.status}.`,
      retryable: payload?.error?.retryable ?? response.status >= 500,
    });
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export function getCalendarContext(signal?: AbortSignal): Promise<CalendarContext> {
  return request<CalendarContext>("/context", { signal });
}

export function getCalendarWeek(weekStart: string, signal?: AbortSignal): Promise<CalendarWeek> {
  return request<CalendarWeek>(`/weeks/${encodeURIComponent(weekStart)}`, { signal });
}

export function searchPublicRecipes(query: string, signal?: AbortSignal): Promise<RecipeSearchResult> {
  const params = new URLSearchParams({ q: query, limit: "20" });
  return request<RecipeSearchResult>(`/recipes?${params.toString()}`, { signal });
}

export function getPublicRecipe(recipeId: string, signal?: AbortSignal): Promise<RecipeDetail> {
  return request<RecipeDetail>(`/recipes/${encodeURIComponent(recipeId)}`, { signal });
}

export function createAssignment(payload: AssignmentWritePayload): Promise<CalendarAssignment> {
  return request<CalendarAssignment>("/assignments", { method: "POST", body: payload });
}

export function updateAssignment(assignmentId: string, payload: AssignmentWritePayload): Promise<CalendarAssignment> {
  return request<CalendarAssignment>(`/assignments/${encodeURIComponent(assignmentId)}`, { method: "PATCH", body: payload });
}

export async function deleteAssignment(assignmentId: string): Promise<void> {
  await request<void>(`/assignments/${encodeURIComponent(assignmentId)}`, { method: "DELETE" });
}
