import { TextStyle } from 'react-native';

import { defaultColors, DefaultColors } from './colors';

export interface TypographyTokens {
  display: TextStyle;
  h1: TextStyle;
  h2: TextStyle;
  h3: TextStyle;
  body: TextStyle;
  bodyLarge: TextStyle;
  bodySmall: TextStyle;
  caption: TextStyle;
  overline: TextStyle;
  button: TextStyle;
  label: TextStyle;
  pill: TextStyle;
}

export function buildTypography(colors: DefaultColors): TypographyTokens {
  return {
    display: {
      fontSize: 30,
      lineHeight: 36,
      fontWeight: '800',
      color: colors.text,
    },
    h1: {
      fontSize: 24,
      lineHeight: 30,
      fontWeight: '700',
      color: colors.text,
    },
    h2: {
      fontSize: 20,
      lineHeight: 26,
      fontWeight: '700',
      color: colors.text,
    },
    h3: {
      fontSize: 17,
      lineHeight: 22,
      fontWeight: '600',
      color: colors.text,
    },
    body: {
      fontSize: 15,
      lineHeight: 22,
      fontWeight: '400',
      color: colors.text,
    },
    bodyLarge: {
      fontSize: 16,
      lineHeight: 24,
      fontWeight: '400',
      color: colors.text,
    },
    bodySmall: {
      fontSize: 13,
      lineHeight: 18,
      fontWeight: '400',
      color: colors.textSecondary,
    },
    caption: {
      fontSize: 12,
      lineHeight: 16,
      fontWeight: '400',
      color: colors.textSecondary,
    },
    overline: {
      fontSize: 11,
      lineHeight: 14,
      fontWeight: '700',
      letterSpacing: 1.2,
      color: colors.textSecondary,
      textTransform: 'uppercase',
    },
    button: {
      fontSize: 16,
      lineHeight: 20,
      fontWeight: '700',
      color: colors.textInverse,
    },
    label: {
      fontSize: 14,
      lineHeight: 18,
      fontWeight: '600',
      color: colors.text,
    },
    pill: {
      fontSize: 13,
      lineHeight: 18,
      fontWeight: '600',
      color: colors.text,
    },
  };
}
