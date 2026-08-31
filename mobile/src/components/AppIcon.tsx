import { Ionicons } from '@expo/vector-icons';
import React from 'react';

import { useTheme } from '../theme/ThemeProvider';

export type IconName = React.ComponentProps<typeof Ionicons>['name'];

interface AppIconProps {
  name: IconName;
  size?: number;
  color?: string;
}

/** Icons come from Ionicons (bundled with Expo). Color defaults to the theme text color. */
export function AppIcon({ name, size = 22, color }: AppIconProps) {
  const { colors } = useTheme();
  return <Ionicons name={name} size={size} color={color ?? colors.text} />;
}
