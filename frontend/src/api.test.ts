// Verifica el contrato HTTP del cliente de API.
// Comprueba el envío de credenciales y CSRF, la propagación de errores y la aceptación de respuestas vacías.

import { afterEach, describe, expect, it, vi } from "vitest";
import { apiRequest, ApiError } from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("apiRequest", () => {
  it("sends credentials and the CSRF header for authenticated writes", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response('{"user":{"id":"1"}}', { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    await apiRequest("/users", {
      method: "POST",
      csrfToken: "csrf-value",
      body: { name: "Family", email: "family@example.test" },
    });

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toContain("/api/v1/users");
    expect(init.credentials).toBe("include");
    expect(new Headers(init.headers).get("X-CSRF-Token")).toBe("csrf-value");
    expect(init.body).toBe(JSON.stringify({ name: "Family", email: "family@example.test" }));
  });

  it("preserves generic server errors for field and form feedback", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response('{"detail":"Invalid email or password"}', { status: 401 })),
    );

    await expect(apiRequest("/auth/login", { method: "POST", body: {} })).rejects.toMatchObject({
      name: "ApiError",
      status: 401,
      message: "Invalid email or password",
    } satisfies Partial<ApiError>);
  });

  it("accepts empty logout responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
    await expect(apiRequest<null>("/auth/logout", { method: "POST" })).resolves.toBeNull();
  });
});
