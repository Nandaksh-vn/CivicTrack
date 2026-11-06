/** API client: bearer header, request ids, envelope normalization, 204s, 401s. */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiFetch, apiSend, login } from "@/api/client";
import { clearToken, getToken, setToken } from "@/lib/auth-token";

function jsonResponse(
  body: unknown,
  init: { status?: number; headers?: Record<string, string> } = {},
): Response {
  return new Response(JSON.stringify(body), {
    status: init.status ?? 200,
    headers: { "Content-Type": "application/json", ...(init.headers ?? {}) },
  });
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  window.sessionStorage.clear();
  vi.stubGlobal("fetch", fetchMock);
});

afterEach(() => {
  vi.unstubAllGlobals();
  fetchMock.mockReset();
  window.sessionStorage.clear();
});

describe("apiFetch", () => {
  it("attaches the bearer token and a request id", async () => {
    setToken("token-123");
    fetchMock.mockResolvedValue(jsonResponse({ ok: true }));

    await apiFetch("/auth/me");

    const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const headers = new Headers(init.headers);
    expect(url).toBe("/api/v1/auth/me");
    expect(headers.get("Authorization")).toBe("Bearer token-123");
    expect(headers.get("X-Request-Id")).toBeTruthy();
    expect(headers.get("Accept")).toBe("application/json");
  });

  it("normalizes the 422 envelope to an ApiError with the server code", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { error: { code: "VALIDATION_ERROR", message: "Title is too short.", details: { fields: [] } } },
        { status: 422, headers: { "X-Request-Id": "req-42" } },
      ),
    );

    const error = (await apiFetch("/complaints").catch((caught) => caught)) as ApiError;

    expect(error).toBeInstanceOf(ApiError);
    expect(error.status).toBe(422);
    expect(error.code).toBe("VALIDATION_ERROR");
    expect(error.message).toBe("Title is too short.");
    expect(error.requestId).toBe("req-42");
  });

  it("maps unknown error codes to REQUEST_FAILED without leaking internals", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { error: { code: "SOME_UNMAPPED_CODE", message: "nope" } },
        { status: 500 },
      ),
    );

    const error = (await apiFetch("/admin/users").catch((caught) => caught)) as ApiError;
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe("REQUEST_FAILED");
  });

  it("clears the stored token when the API returns 401", async () => {
    setToken("stale-token");
    fetchMock.mockResolvedValue(
      jsonResponse(
        { error: { code: "TOKEN_INVALID", message: "expired" } },
        { status: 401 },
      ),
    );

    await expect(apiFetch("/auth/me")).rejects.toMatchObject({
      status: 401,
      code: "TOKEN_INVALID",
    });
    expect(getToken()).toBeNull();
  });

  it("returns undefined for a 204 response without parsing a body", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));
    await expect(apiFetch("/auth/logout", { method: "POST" })).resolves.toBeUndefined();
  });

  it("treats form posts as multipart and leaves Content-Type to the browser", async () => {
    setToken("t");
    fetchMock.mockResolvedValue(jsonResponse({ ok: true }));
    const form = new FormData();
    form.set("title", "hello");

    await apiSend("/complaints", { method: "POST", body: form });

    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    const headers = new Headers(init.headers);
    expect(init.body).toBeInstanceOf(FormData);
    expect(headers.get("Content-Type")).toBeNull();
  });

  it("login posts credentials and returns the token payload", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({
        token: "jwt-1",
        token_type: "bearer",
        expires_in: 3600,
        user: { id: 1, role: "CITIZEN" },
      }),
    );

    const response = await login({ email: "a@b.com", password: "pw" });
    expect(response.token).toBe("jwt-1");
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    expect(init.method).toBe("POST");
    expect(init.body).toBe(JSON.stringify({ email: "a@b.com", password: "pw" }));
  });

  it("clearToken semantics: apiSend with 403 surfaces the server code", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse(
        { error: { code: "FORBIDDEN", message: "Not for officers" } },
        { status: 403 },
      ),
    );

    await expect(
      apiSend("/complaints", { method: "POST", body: { title: "x" } }),
    ).rejects.toMatchObject({ status: 403, code: "FORBIDDEN" });
    clearToken();
  });
});
