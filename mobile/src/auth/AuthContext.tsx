import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { authApi } from '../api/auth';
import { onAuthExpired, logoutRemote } from '../api/client';
import { clearTokens, getAccessToken, getRefreshToken, saveTokens } from '../storage/tokenStorage';
import { AuthTokens, UserAccount } from '../types/models';

type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated';

interface AuthContextValue {
  status: AuthStatus;
  user: UserAccount | null;
  isRestoring: boolean;
  signIn: (tokens: AuthTokens) => Promise<void>;
  signOut: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('loading');
  const [user, setUser] = useState<UserAccount | null>(null);
  const [isRestoring, setIsRestoring] = useState(true);
  const listenerRegistered = useRef(false);

  const refreshUser = useCallback(async () => {
    try {
      const me = await authApi.me();
      setUser(me);
      setStatus('authenticated');
    } catch {
      setUser(null);
      setStatus('unauthenticated');
    }
  }, []);

  const signIn = useCallback(
    async (tokens: AuthTokens) => {
      await saveTokens(tokens.access_token, tokens.refresh_token);
      try {
        const me = await authApi.me();
        setUser(me);
      } catch {
        setUser(null);
      }
      setStatus('authenticated');
    },
    [],
  );

  const signOut = useCallback(async () => {
    try {
      await logoutRemote();
    } catch {
      await clearTokens();
    }
    setUser(null);
    setStatus('unauthenticated');
  }, []);

  const restore = useCallback(async () => {
    setIsRestoring(true);
    const [access, refresh] = await Promise.all([getAccessToken(), getRefreshToken()]);
    if (!access || !refresh) {
      await clearTokens();
      setStatus('unauthenticated');
      setIsRestoring(false);
      return;
    }
    await refreshUser();
    setIsRestoring(false);
  }, [refreshUser]);

  useEffect(() => {
    restore();
  }, [restore]);

  // When the API client fails to refresh an expired session, sign out.
  useEffect(() => {
    if (listenerRegistered.current) {
      return;
    }
    listenerRegistered.current = true;
    const unsubscribe = onAuthExpired(() => {
      setUser(null);
      setStatus('unauthenticated');
    });
    return unsubscribe;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ status, user, isRestoring, signIn, signOut, refreshUser }),
    [status, user, isRestoring, signIn, signOut, refreshUser],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
