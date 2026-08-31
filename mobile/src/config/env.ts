import { Platform } from 'react-native';
import Constants from 'expo-constants';

/**
 * Environment / runtime configuration.
 *
 * All public, non-secret configuration is centralized here. Values are read
 * from `EXPO_PUBLIC_*` environment variables (inlined by Expo at build time),
 * falling back to the `extra` block in app.json, and finally to per-env
 * defaults.
 *
 * Never put backend secrets here. The backend app-config endpoint is the only
 * source of remote branding/pricing/feature configuration.
 */

export type AppEnv = 'development' | 'staging' | 'production';

const APP_ENV = (process.env.EXPO_PUBLIC_APP_ENV ??
  Constants.expoConfig?.extra?.appEnv ??
  'development') as AppEnv;

/** Android emulators reach the host machine via 10.0.2.2; everywhere else localhost. */
const DEFAULT_DEV_HOST = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

const DEFAULT_BASE_URLS: Record<AppEnv, string> = {
  development: DEFAULT_DEV_HOST,
  staging: 'https://staging-api.ardhang.in',
  production: 'https://api.ardhang.in',
};

function resolveApiBaseUrl(): string {
  const explicit = process.env.EXPO_PUBLIC_API_BASE_URL;
  if (explicit && explicit.trim().length > 0) {
    return explicit.replace(/\/+$/, '');
  }
  const extra = Constants.expoConfig?.extra as { apiBaseUrl?: string } | undefined;
  if (extra?.apiBaseUrl) {
    return extra.apiBaseUrl.replace(/\/+$/, '');
  }
  return (DEFAULT_BASE_URLS[APP_ENV] ?? DEFAULT_BASE_URLS.development).replace(/\/+$/, '');
}

export const API_BASE_URL = resolveApiBaseUrl();
export const API_V1_PREFIX = '/api/v1';

export const API_URL = `${API_BASE_URL}${API_V1_PREFIX}`;

export const APP_ENV_VALUE = APP_ENV;

export const isProduction = APP_ENV === 'production';

/** Timeouts (ms). Network timeouts let the UI fail gracefully on poor networks. */
export const NETWORK_TIMEOUT_MS = 20_000;
