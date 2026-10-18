"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiFetch, setAccessToken } from "@/lib/api";
import type { ApiEnvelope, UserAccount } from "@/lib/types";

export interface LoginResult {
  requires_2fa?: boolean;
  mfa_token?: string;
}

interface AuthContextValue {
  user: UserAccount | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<LoginResult>;
  completeMfa: (mfaToken: string, code: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

async function postBff(path: string, body: unknown): Promise<Record<string, any>> {
  const res = await fetch(path, {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await res.json().catch(() => null);
  if (!res.ok) {
    throw new ApiError(res.status, payload?.error?.code, payload?.error?.message || "Request failed");
  }
  return payload?.data ?? {};
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const loadMe = useCallback(async () => {
    const me = await apiFetch<ApiEnvelope<UserAccount>>("/auth/me");
    setUser(me.data);
  }, []);

  // Restore session on mount: the HttpOnly refresh cookie is exchanged for an
  // in-memory access token via the same-origin BFF route.
  useEffect(() => {
    (async () => {
      try {
        const data = await postBff("/api/auth/refresh", {});
        if (data.access_token) {
          setAccessToken(data.access_token);
          await loadMe();
        }
      } catch {
        // no session
      } finally {
        setLoading(false);
      }
    })();
  }, [loadMe]);

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      const data = await postBff("/api/auth/login", { email, password });
      if (data.requires_2fa) {
        return { requires_2fa: true, mfa_token: data.mfa_token };
      }
      setAccessToken(data.access_token);
      await loadMe();
      router.replace("/discover");
      return {};
    },
    [loadMe, router],
  );

  const completeMfa = useCallback(
    async (mfaToken: string, code: string) => {
      const data = await postBff("/api/auth/totp", { mfa_token: mfaToken, code });
      setAccessToken(data.access_token);
      await loadMe();
      router.replace("/discover");
    },
    [loadMe, router],
  );

  const register = useCallback(
    async (email: string, password: string) => {
      const data = await postBff("/api/auth/register", { email, password });
      setAccessToken(data.access_token);
      router.replace("/onboarding");
    },
    [router],
  );

  const logout = useCallback(async () => {
    setAccessToken(null);
    setUser(null);
    try {
      await postBff("/api/auth/logout", {});
    } catch {
      // cookie cleared best-effort
    }
    router.replace("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, loading, login, completeMfa, register, logout }),
    [user, loading, login, completeMfa, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
