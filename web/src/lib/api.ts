export const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
).replace(/\/+$/, "");
export const API_V1 = `${API_BASE}/api/v1`;

export class ApiError extends Error {
  status: number;
  code?: string;
  constructor(status: number, code: string | undefined, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

// The access token is intentionally kept in memory only. The refresh token
// lives in an HttpOnly cookie owned by the same-origin BFF routes under
// /api/auth/* — nothing sensitive is ever persisted to localStorage.
let accessToken: string | null = null;
let refreshInFlight: Promise<string | null> | null = null;

export function setAccessToken(token: string | null) {
  accessToken = token;
}

export function getAccessToken(): string | null {
  return accessToken;
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshInFlight) {
    refreshInFlight = fetch("/api/auth/refresh", { method: "POST", credentials: "same-origin" })
      .then(async (res) => {
        if (!res.ok) return null;
        const body = await res.json().catch(() => null);
        const token = body?.data?.access_token ?? null;
        if (token) accessToken = token;
        return token as string | null;
      })
      .catch(() => null)
      .finally(() => {
        refreshInFlight = null;
      });
  }
  return refreshInFlight;
}

export async function apiFetch<T>(path: string, options: RequestInit = {}, _retried = false): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;

  const res = await fetch(`${API_V1}${path}`, { ...options, headers });

  // Refresh once on 401 and retry.
  if (res.status === 401 && !_retried) {
    const refreshed = await refreshAccessToken();
    if (refreshed) return apiFetch<T>(path, options, true);
    throw new ApiError(401, "UNAUTHORIZED", "Session expired. Please sign in again.");
  }

  let body: any = null;
  try {
    body = await res.json();
  } catch {
    /* no body */
  }

  if (!res.ok) {
    const err = body?.error;
    throw new ApiError(res.status, err?.code, err?.message || `Request failed (${res.status})`);
  }
  return body as T;
}

// Swipe action types
export type SwipeAction = "like" | "pass" | "super_like";

/** Resolve a possibly-relative /static/<...> image URL to a full URL on the API host. */
export function photoUrl(url: string | null | undefined): string | undefined {
  if (!url) return undefined;
  if (url.startsWith("http")) return url;
  if (url.startsWith("/static/")) return `${API_BASE}${url}`;
  // bare storage key -> served under /static
  return `${API_BASE}/static/${url.replace(/^\/+/, "")}`;
}

/** Upload a photo file directly (multipart) to the backend's /upload endpoint. */
export async function uploadPhotoFile(file: File): Promise<any> {
  const headers: Record<string, string> = {};
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_V1}/profile/photos/upload`, {
    method: "POST",
    headers,
    body: form,
  });
  if (!res.ok) {
    let code: string | undefined;
    let message = `Upload failed (${res.status})`;
    try {
      const body = await res.json();
      code = body?.error?.code;
      message = body?.error?.message || message;
    } catch {}
    throw new ApiError(res.status, code, message);
  }
  return res.json();
}
