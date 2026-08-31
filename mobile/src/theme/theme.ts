import { defaultColors, DefaultColors } from './colors';
import { radius } from './radius';
import { shadows } from './shadows';
import { spacing } from './spacing';
import { buildTypography, TypographyTokens } from './typography';

export interface RemoteBrandingOverrides {
  primary_color?: string | null;
  secondary_color?: string | null;
  background_color?: string | null;
  text_color?: string | null;
  accent_color?: string | null;
}

export interface Theme {
  colors: DefaultColors;
  typography: TypographyTokens;
  spacing: typeof spacing;
  radius: typeof radius;
  shadows: typeof shadows;
}

const hexPattern = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/;

function safeHex(value: string | null | undefined, fallback: string): string {
  if (typeof value === 'string' && hexPattern.test(value.trim())) {
    return value.trim();
  }
  return fallback;
}

/** Build the app theme, applying backend remote-config brand overrides. */
export function buildTheme(overrides?: RemoteBrandingOverrides): Theme {
  const colors: DefaultColors = {
    ...defaultColors,
    primary: safeHex(overrides?.primary_color, defaultColors.primary),
    secondary: safeHex(overrides?.secondary_color, defaultColors.secondary),
    background: safeHex(overrides?.background_color, defaultColors.background),
    text: safeHex(overrides?.text_color, defaultColors.text),
    accent: safeHex(overrides?.accent_color, defaultColors.accent),
  };

  return {
    colors,
    typography: buildTypography(colors),
    spacing,
    radius,
    shadows,
  };
}

export const defaultTheme: Theme = buildTheme(undefined);
