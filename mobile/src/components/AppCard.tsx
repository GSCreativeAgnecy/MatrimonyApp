import React from 'react';
import { Pressable, StyleProp, StyleSheet, View, ViewStyle } from 'react-native';

import { AppText } from './AppText';
import { useTheme } from '../theme/ThemeProvider';

interface AppCardProps {
  children: React.ReactNode;
  onPress?: () => void;
  style?: StyleProp<ViewStyle>;
  padded?: boolean;
  elevated?: boolean;
}

/** Rounded cream/white card with a subtle shadow. */
export function AppCard({ children, onPress, style, padded = true, elevated = false }: AppCardProps) {
  const { colors, radius, spacing, shadows } = useTheme();

  const cardStyle: ViewStyle = {
    backgroundColor: colors.surface,
    borderRadius: radius.xl,
    padding: padded ? spacing.lg : 0,
    ...(elevated ? shadows.elevated : shadows.card),
  };

  if (onPress) {
    return (
      <Pressable
        accessibilityRole="button"
        onPress={onPress}
        style={({ pressed }) => [
          cardStyle,
          { opacity: pressed ? 0.92 : 1 },
          style,
        ]}
      >
        {children}
      </Pressable>
    );
  }
  return <View style={[cardStyle, style]}>{children}</View>;
}
