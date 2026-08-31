import React from 'react';
import { View } from 'react-native';

import { AppText } from './AppText';
import { useTheme } from '../theme/ThemeProvider';

interface NotificationBadgeProps {
  count: number;
  max?: number;
}

/** Red badge for unread notifications. */
export function NotificationBadge({ count, max = 99 }: NotificationBadgeProps) {
  const { colors, radius, spacing } = useTheme();
  if (count <= 0) {
    return null;
  }
  const label = count > max ? `${max}+` : String(count);
  return (
    <View
      style={{
        minWidth: 20,
        height: 20,
        borderRadius: radius.pill,
        backgroundColor: colors.error,
        alignItems: 'center',
        justifyContent: 'center',
        paddingHorizontal: spacing.xs,
      }}
    >
      <AppText
        variant="caption"
        color={colors.textInverse}
        style={{ fontWeight: '800', fontSize: 11, lineHeight: 14 }}
      >
        {label}
      </AppText>
    </View>
  );
}
