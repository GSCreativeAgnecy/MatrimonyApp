import * as SecureStore from 'expo-secure-store';

/**
 * Secure storage for auth tokens. Uses the OS keychain/keystore via
 * `expo-secure-store` — never plain AsyncStorage for secrets.
 */

const ACCESS_TOKEN_KEY = 'ardhang_access_token';
const REFRESH_TOKEN_KEY = 'ardhang_refresh_token';

export async function saveTokens(accessToken: string, refreshToken: string): Promise<void> {
  await SecureStore.setItemAsync(ACCESS_TOKEN_KEY, accessToken);
  await SecureStore.setItemAsync(REFRESH_TOKEN_KEY, refreshToken);
}

export async function getAccessToken(): Promise<string | null> {
  return SecureStore.getItemAsync(ACCESS_TOKEN_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return SecureStore.getItemAsync(REFRESH_TOKEN_KEY);
}

export async function clearTokens(): Promise<void> {
  await SecureStore.deleteItemAsync(ACCESS_TOKEN_KEY).catch(() => undefined);
  await SecureStore.deleteItemAsync(REFRESH_TOKEN_KEY).catch(() => undefined);
}
