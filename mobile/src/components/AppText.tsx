import React from 'react';
import { StyleProp, Text, TextProps, TextStyle } from 'react-native';

import { useTheme } from '../theme/ThemeProvider';

type TextVariant =
  | 'display'
  | 'h1'
  | 'h2'
  | 'h3'
  | 'body'
  | 'bodyLarge'
  | 'bodySmall'
  | 'caption'
  | 'overline'
  | 'button'
  | 'label'
  | 'pill';

interface AppTextProps extends TextProps {
  variant?: TextVariant;
  color?: string;
  center?: boolean;
  numberOfLines?: number;
  style?: StyleProp<TextStyle>;
}

/** Single text primitive — all typography flows through here. */
export function AppText({
  variant = 'body',
  color,
  center,
  style,
  children,
  ...rest
}: AppTextProps) {
  const { typography } = useTheme();
  const base = typography[variant] as TextStyle;

  const merged: TextStyle = {
    ...base,
    ...(color ? { color } : {}),
    ...(center ? { textAlign: 'center' as const } : {}),
  };

  return (
    <Text {...rest} style={[merged, style]}>
      {children}
    </Text>
  );
}
