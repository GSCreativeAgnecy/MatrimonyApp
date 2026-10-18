import type { ApiError } from "@/lib/types";

// In-memory token holder. The access token is intentionally NOT persisted to
// localStorage; it lives in memory and is refreshed via the HttpOnly-cookie
// BFF route when it expires.
let accessToken: string | null = null;
let refreshInFlight: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";

export class ApiClientError extends Error {
  status: number;
  code: string;
  details?: Record<string, unknown> | null;

  constructor(status: number, payload: ApiError) {
    super(payload.error?.message ?? "Request failed");
    this.name = "ApiClientError";
    this.status = status;
    this.code = payload.error?.code ?? "UNKNOWN_ERROR";
    this.details = payload.error?.details ?? null;
  }
}

async function parseError(response: Response): Promise<ApiClientError> {
  let payload: ApiError = { error: { code: "UNKNOWN_ERROR", message: response.statusText || "Request failed" } };
  try {
    payload = (await response.json()) as ApiError;
  } catch {
    // non-JSON error body
  }
  return new ApiClientError(response.status, payload);
}

/**
 * Call the Next.js BFF route to rotate the refresh cookie and return a fresh
 * access token. Returns null when the session is gone.
 */
async function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = fetch("/api/auth/refresh", { method: "POST", credentials: "same-origin" })
      .then(async (res) => {
        if (!res.ok) return null;
        const body = (await res.json()) as { data?: { access_token?: string } };
        return body.data?.access_token ?? null;
      })
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

interface RequestOptions extends Omit<RequestInit, "body"> {
  body?: unknown;
  /** Do not attempt a token refresh + retry on 401. */
  skipAuthRetry?: boolean;
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { body, skipAuthRetry = false, headers, ...rest } = options;

  const perform = async (token: string | null): Promise<T> => {
    const response = await fetch(`${API_URL}${API_PREFIX}${path}`, {
      ...rest,
      credentials: "omit",
      headers: {
        ...(body !== undefined ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (response.ok) {
      if (response.status === 204) return undefined as T;
      return (await response.json()) as T;
    }
    throw await parseError(response);
  };

  try {
    return await perform(accessToken);
  } catch (err) {
    if (err instanceof ApiClientError && err.status === 401 && !skipAuthRetry) {
      const fresh = await refreshAccessToken();
      if (fresh) {
        accessToken = fresh;
        return perform(fresh);
      }
    }
    throw err;
  }
}

export const apiGet = <T>(path: string, options: RequestOptions = {}) =>
  api<T>(path, { ...options, method: "GET" });

export const apiPost = <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
  api<T>(path, { ...options, method: "POST", body });

export const apiPatch = <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
  api<T>(path, { ...options, method: "PATCH", body });

export const apiPut = <T>(path: string, body?: unknown, options: RequestOptions = {}) =>
  api<T>(path, { ...options, method: "PUT", body });

export const apiDelete = <T>(path: string, options: RequestOptions = {}) =>
  api<T>(path, { ...options, method: "DELETE" });

export function buildQuery(params: Record<string, string | number | boolean | null | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, String(value));
    }
  }
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}
