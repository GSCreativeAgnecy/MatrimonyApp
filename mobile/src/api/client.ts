import { API_URL, NETWORK_TIMEOUT_MS } from '../config/env';
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '../storage/tokenStorage';
import { ApiError, ApiSuccess } from '../types/api';

/**
 * Core HTTP client for the Matchmaking backend.
 *
 * Responsibilities:
 *  - centralized base URL
 *  - attach access token
 *  - refresh-on-401 (single-flight) and retry
 *  - normalize errors into `ApiError`
 *  - expose an `auth:expired` event so the session can be torn down
 *
 * Screens never call fetch() directly — they use the typed API modules and
 * TanStack Query hooks on top of this client.
 */

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  body?: unknown;
  query?: Record<string, string | number | boolean | null | undefined>;
  auth?: boolean;
  retry?: boolean;
  signal?: AbortSignal;
  /** Skip automatic token refresh on 401 (used by the refresh call itself). */
  skipRefresh?: boolean;
}

export type AuthEventsListener = () => void;

const listeners = new Set<AuthEventsListener>();

export function onAuthExpired(listener: AuthEventsListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

function emitAuthExpired(): void {
  listeners.forEach((listener) => listener());
}

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (refreshPromise) {
    return refreshPromise;
  }
  refreshPromise = (async () => {
    const refreshToken = await getRefreshToken();
    if (!refreshToken) {
      return null;
    }
    try {
      const res = await rawFetch<ApiSuccess<{ access_token: string; refresh_token: string }>>('/auth/refresh', {
        method: 'POST',
        body: { refresh_token: refreshToken },
        auth: false,
        skipRefresh: true,
      });
      if (res.data?.access_token) {
        await saveTokens(res.data.access_token, res.data.refresh_token || refreshToken);
        return res.data.access_token;
      }
      return null;
    } catch {
      return null;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

async function rawFetch<T>(path: string, options: RequestOptions): Promise<T> {
  const { method = 'GET', body, query, auth = true } = options;

  const url = new URL(`${API_URL}${path}`);
  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.set(key, String(value));
      }
    });
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), NETWORK_TIMEOUT_MS);
  const externalSignal = options.signal;
  if (externalSignal?.aborted) {
    controller.abort();
  } else if (externalSignal) {
    externalSignal.addEventListener('abort', () => controller.abort());
  }

  const headers: Record<string, string> = {
    Accept: 'application/json',
    'Content-Type': 'application/json',
  };
  if (auth) {
    const token = await getAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  let response: Response;
  try {
    response = await fetch(url.toString(), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });
  } catch (error) {
    const message = error instanceof Error && error.name === 'AbortError' ? 'Request timed out.' : 'Network error.';
    throw new ApiError(message, 'NETWORK_ERROR', 0);
  } finally {
    clearTimeout(timeout);
  }

  const payload = await response.json().catch(() => null);

  if (!response.ok) {
    throw normalizeError(payload, response.status);
  }

  if (payload && typeof payload === 'object' && 'data' in payload) {
    return payload as T;
  }

  return payload as T;
}

function normalizeError(payload: unknown, status: number): ApiError {
  const error = (payload as { error?: { code?: unknown; message?: unknown; details?: Record<string, unknown> } })
    ?.error;
  const code = typeof error?.code === 'string' ? error.code : 'UNKNOWN_ERROR';
  const message = typeof error?.message === 'string' ? error.message : 'Something went wrong. Please try again.';
  return new ApiError(message, code, status, error?.details);
}

/**
 * Perform an authenticated request, transparently refreshing the access token
 * once on 401. If the refresh fails the session is cleared.
 */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  try {
    return await rawFetch<T>(path, options);
  } catch (error) {
    if (error instanceof ApiError && error.isUnauthorized && options.auth !== false && !options.skipRefresh) {
      const newToken = await refreshAccessToken();
      if (newToken) {
        return rawFetch<T>(path, { ...options, auth: true });
      }
      await clearTokens();
      emitAuthExpired();
    }
    throw error;
  }
}

export async function logoutRemote(): Promise<void> {
  const refreshToken = await getRefreshToken();
  if (refreshToken) {
    try {
      await rawFetch('/auth/logout', {
        method: 'POST',
        body: { refresh_token: refreshToken },
        auth: true,
        skipRefresh: true,
      });
    } catch {
      // Best-effort server-side revoke.
    }
  }
  await clearTokens();
  emitAuthExpired();
}
