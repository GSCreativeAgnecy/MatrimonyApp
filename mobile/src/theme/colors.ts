/**
 * Default visual palette (deep burgundy / warm cream / muted gold).
 *
 * These are the LOCAL DEFAULTS. A subset of these values can be overridden at
 * runtime by the backend remote app-config (`branding.*` keys) through the
 * ThemeProvider. Components should always read from `useTheme()` — never hard
 * code hex values in components.
 */
export interface DefaultColors {
  primary: string;
  primaryDark: string;
  secondary: string;
  accent: string;
  background: string;
  surface: string;
  surfaceMuted: string;
  text: string;
  textSecondary: string;
  textInverse: string;
  border: string;
  success: string;
  error: string;
  warning: string;
  info: string;
  verified: string;
  gold: string;
  overlay: string;
}

export const defaultColors: DefaultColors = {
  primary: '#7A1730',
  primaryDark: '#5A1023',
  secondary: '#F5EAD9',
  accent: '#C9A24B',
  background: '#FAF6EF',
  surface: '#FFFFFF',
  surfaceMuted: '#FBF7F0',
  text: '#2B2220',
  textSecondary: '#8A7F78',
  textInverse: '#FFFFFF',
  border: '#EADFCE',
  success: '#2E7D32',
  error: '#C62828',
  warning: '#B26A00',
  info: '#1F6FEB',
  verified: '#2E7D32',
  gold: '#C9A24B',
  overlay: 'rgba(43, 34, 32, 0.55)',
};
