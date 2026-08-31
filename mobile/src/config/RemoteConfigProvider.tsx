import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { appConfigApi } from '../api/appConfig';
import { loadCachedRemoteConfig, normalizeConfig, saveCachedRemoteConfig } from '../storage/configCache';
import { DEFAULT_REMOTE_CONFIG, RemoteConfig } from '../types/remoteConfig';

/**
 * Remote configuration startup flow:
 *
 *   Load local defaults
 *     -> Load cached remote configuration (if available)
 *     -> Request GET /api/v1/app/config
 *     -> Validate + normalize
 *     -> Apply branding / theme / features
 *
 * A failure never blocks app launch — the app falls back to local defaults and
 * the UI still renders. `ready` becomes true as soon as defaults/cache are in.
 */

interface RemoteConfigState {
  config: RemoteConfig;
  /** True once a usable config is in place (defaults or cached). */
  ready: boolean;
  isRefreshing: boolean;
  refresh: () => Promise<void>;
}

const RemoteConfigContext = createContext<RemoteConfigState | null>(null);

export function RemoteConfigProvider({ children }: { children: React.ReactNode }) {
  const [config, setConfig] = useState<RemoteConfig>(DEFAULT_REMOTE_CONFIG);
  const [ready, setReady] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const didFetch = useRef(false);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const remote = await appConfigApi.getPublic();
      const normalized = normalizeConfig(remote as unknown as Record<string, unknown>);
      setConfig(normalized);
      await saveCachedRemoteConfig(normalized);
    } catch {
      // Fail-open: keep current (cached/default) config.
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const cached = await loadCachedRemoteConfig();
      if (!cancelled && cached) {
        setConfig(cached);
      }
      setReady(true);

      if (didFetch.current) {
        return;
      }
      didFetch.current = true;
      await refresh();
    })();

    return () => {
      cancelled = true;
    };
  }, [refresh]);

  const value = useMemo(() => ({ config, ready, isRefreshing, refresh }), [config, ready, isRefreshing, refresh]);

  return <RemoteConfigContext.Provider value={value}>{children}</RemoteConfigContext.Provider>;
}

export function useRemoteConfig(): RemoteConfigState {
  const ctx = useContext(RemoteConfigContext);
  if (!ctx) {
    throw new Error('useRemoteConfig must be used within RemoteConfigProvider');
  }
  return ctx;
}
