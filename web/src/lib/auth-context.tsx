"use client";

import { createContext, useCallback, useContext, useMemo, useState, ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import { ApiError, apiFetch, tokenStore } from "@/lib/api";
import type { ApiEnvelope, TokenResponse, UserAccount } from "@/lib/types";

interface AuthContextValue {
  user: UserAccount | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserAccount | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Restore session on mount.
  useEffect(() => {
    (async () => {
      const { access } = tokenStore.get();
      if (!access) {
        setLoading(false);
        return;
      }
      try {
        const res = await apiFetch<ApiEnvelope<UserAccount>>("/auth/me");
        setUser(res.data);
      } catch (e) {
        if (e instanceof ApiError && e.status === 401) tokenStore.clear();
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const res = await apiFetch<ApiEnvelope<TokenResponse | { requires_2fa: boolean; mfa_token: string }>>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    const d = res.data as TokenResponse;
    tokenStore.set(d.access_token, d.refresh_token);
    const me = await apiFetch<ApiEnvelope<UserAccount>>("/auth/me");
    setUser(me.data);
    router.replace("/discover");
  }, [router]);

  const register = useCallback(async (email: string, password: string) => {
    const res = await apiFetch<ApiEnvelope<TokenResponse>>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    tokenStore.set(res.data.access_token, res.data.refresh_token);
    router.replace("/onboarding");
  }, [router]);

  const logout = useCallback(async () => {
    tokenStore.clear();
    setUser(null);
    router.replace("/login");
  }, [router]);

  const value = useMemo(
    () => ({ user, loading, login, register, logout }),
    [user, loading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}