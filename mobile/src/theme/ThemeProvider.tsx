import React, { createContext, useContext, useMemo } from 'react';

import { useRemoteConfig } from '../config/RemoteConfigProvider';
import { buildTheme, Theme } from './theme';

const ThemeContext = createContext<Theme | null>(null);

/**
 * Builds the app theme from remote branding config. Components must read colors
 * via `useTheme()` — never hard-code hex values in components.
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const { config } = useRemoteConfig();

  const theme = useMemo(
    () =>
      buildTheme({
        primary_color: config.branding.primary_color,
        secondary_color: config.branding.secondary_color,
        background_color: config.branding.background_color,
        text_color: config.branding.text_color,
        accent_color: config.branding.accent_color,
      }),
    [
      config.branding.primary_color,
      config.branding.secondary_color,
      config.branding.background_color,
      config.branding.text_color,
      config.branding.accent_color,
    ],
  );

  return <ThemeContext.Provider value={theme}>{children}</ThemeContext.Provider>;
}

export function useTheme(): Theme {
  const theme = useContext(ThemeContext);
  if (!theme) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return theme;
}
