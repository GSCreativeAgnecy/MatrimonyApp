export const API_BASE = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "https://api.ardhangmatrimony.com"
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

type TokenStore = {
  get: () => { access: string | null; refresh: string | null };
  set: (access: string, refresh: string) => void;
  clear: () => void;
};

// Backed by localStorage on the browser (safe enough for v1 web client which
// primarily uses JWT bearer tokens server-side).
export const tokenStore: TokenStore = {
  get: () => {
    if (typeof window === "undefined") return { access: null, refresh: null };
    return { access: localStorage.getItem("ardhang.access"), refresh: localStorage.getItem("ardhang.refresh") };
  },
  set: (access, refresh) => {
    if (typeof window === "undefined") return;
    localStorage.setItem("ardhang.access", access);
    localStorage.setItem("ardhang.refresh", refresh);
  },
  clear: () => {
    if (typeof window === "undefined") return;
    localStorage.removeItem("ardhang.access");
    localStorage.removeItem("ardhang.refresh");
  },
};

export async function apiFetch<T>(path: string, options: RequestInit = {}, _retried = false): Promise<T> {
  const { access } = tokenStore.get();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (access) headers.Authorization = `Bearer ${access}`;

  const res = await fetch(`${API_V1}${path}`, { ...options, headers, credentials: "include" });

  // Refresh once on 401 and retry.
  if (res.status === 401 && !_retried) {
    const refreshed = await tryRefresh();
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

async function tryRefresh(): Promise<boolean> {
  const { refresh } = tokenStore.get();
  if (!refresh) return false;
  try {
    const res = await fetch(`${API_V1}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    const body = await res.json();
    if (!res.ok) {
      tokenStore.clear();
      return false;
    }
    const d = body?.data;
    tokenStore.set(d.access_token, d.refresh_token);
    return true;
  } catch {
    tokenStore.clear();
    return false;
  }
}

// Swipe action types
export type SwipeAction = "like" | "pass" | "super_like";