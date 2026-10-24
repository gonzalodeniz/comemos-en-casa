// Proporciona el cliente HTTP tipado de la aplicación.
// Centraliza credenciales, encabezado CSRF, serialización JSON y conversión de respuestas y errores.

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/comemos";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  csrfToken?: string;
};

export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  // Todas las llamadas comparten cookies de sesión y traducen errores del servidor a ApiError.
  const headers = new Headers();
  if (options.body !== undefined) headers.set("Content-Type", "application/json");
  if (options.csrfToken) headers.set("X-CSRF-Token", options.csrfToken);

  const response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
    method: options.method ?? "GET",
    credentials: "include",
    headers,
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
  });

  if (response.status === 204) return null as T;
  const payload = (await response.json().catch(() => ({}))) as {
    detail?: string;
    message?: string;
  };
  if (!response.ok) {
    throw new ApiError(response.status, payload.detail ?? payload.message ?? "Request failed");
  }
  return payload as T;
}

export type User = {
  id: string;
  name: string;
  email: string;
  is_active: boolean;
};

export type UserResponse = { user: Omit<User, "is_active"> & { is_active?: boolean } };
