/**
 * Shared API client boundary.
 *
 * Every backend call goes through `apiFetch` / `apiMutate`. The wrapper:
 * - attaches `Authorization: Bearer <token>` from the shared token store,
 * - generates an `X-Request-Id` for each call,
 * - normalizes every non-2xx response to `ApiError` carrying
 *   `status`, `code`, `message`, `details`, and `requestId`,
 * - treats 204 responses as "no body" instead of failing to parse JSON,
 * - clears the stored token and notifies listeners on 401 so active routes
 *   redirect to `/login` (the backend, not the UI, remains the access check).
 */

import { getToken, setToken, clearToken } from "@/lib/auth-token";
import { env } from "@/lib/env";
import type { ApiErrorBody, TokenResponse } from "@/types";

const API_BASE_URL = env.apiBaseUrl;

const ERROR_CODES = new Set([
  "VALIDATION_ERROR",
  "TOKEN_INVALID",
  "FORBIDDEN",
  "NOT_FOUND",
  "INVALID_TRANSITION",
  "UPLOAD_TOO_LARGE",
  "UNSUPPORTED_MEDIA_TYPE",
  "INTERNAL_ERROR",
  "SERVICE_UNAVAILABLE",
]);

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
    public readonly details?: unknown,
    public readonly requestId?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type JsonBody = Record<string, unknown> | FormData | null | undefined;

export interface ApiRequestOptions extends Omit<RequestInit, "body"> {
  body?: JsonBody;
}

function requestHeaders(init: RequestInit, hasBody: boolean): HeadersInit {
  const headers = new Headers(init.headers);
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  if (!headers.has("X-Request-Id")) {
    headers.set("X-Request-Id", crypto.randomUUID());
  }
  const token = getToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  // Let the browser set the multipart boundary itself.
  if (hasBody && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return headers;
}

function headersRecord(init: RequestInit): Record<string, string> {
  return Object.fromEntries(new Headers(init.headers).entries());
}

async function parseErrorBody(response: Response): Promise<ApiErrorBody | null> {
  try {
    return (await response.json()) as ApiErrorBody;
  } catch {
    return null;
  }
}

function toRequestId(headers: Headers): string | undefined {
  return headers.get("X-Request-Id") ?? undefined;
}

async function apiFetchRaw(path: string, init: RequestInit = {}): Promise<Response> {
  const hasBody = init.body != null;
  const parsedHeaders = requestHeaders(
    { ...init, headers: headersRecord(init) },
    hasBody,
  );
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: parsedHeaders,
  });
  if (response.status === 401) {
    clearToken();
  }
  return response;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await apiFetchRaw(path, init);
  if (response.status === 204 || response.headers.get("content-length") === "0") {
    if (!response.ok) {
      return buildApiError(response, await parseErrorBody(response));
    }
    return undefined as T;
  }
  if (!response.ok) {
    return buildApiError(response, await parseErrorBody(response));
  }
  return (await response.json()) as T;
}

async function buildApiError(
  response: Response,
  body: ApiErrorBody | null,
): Promise<never> {
  const error = body?.error;
  const code = error?.code && ERROR_CODES.has(error.code) ? error.code : "REQUEST_FAILED";
  const message =
    error?.message ?? `Request failed with status ${response.status} (${code}).`;
  const requestId = toRequestId(response.headers) ?? body?.request_id;
  throw new ApiError(response.status, code, message, error?.details, requestId);
}

export async function apiSend<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { body, headers, method = "POST", ...rest } = options;
  const init: RequestInit = { method, headers, ...rest };
  if (body != null) {
    init.body = body instanceof FormData ? body : JSON.stringify(body);
  }
  return apiFetch<T>(path, init);
}

/** Auth endpoints, kept close to the client so welcome pages stay thin. */
export async function login(input: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  return apiSend<TokenResponse>("/auth/login", { body: input });
}

export async function register(input: {
  full_name: string;
  email: string;
  password: string;
  phone?: string;
}): Promise<TokenResponse> {
  return apiSend<TokenResponse>("/auth/register", { body: input });
}

export async function logout(): Promise<void> {
  try {
    await apiSend<void>("/auth/logout", { method: "POST" });
  } catch {
    // The session is discarded client-side regardless (TRD §8.3).
  }
}

export async function getMe() {
  return apiFetch<import("@/types").PublicUser>("/auth/me");
}

export { setToken };
