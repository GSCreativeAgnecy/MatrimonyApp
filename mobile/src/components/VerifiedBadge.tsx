import React from 'react';
import { View } from 'react-native';

import { AppText } from './AppText';
import { AppIcon } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';

interface VerifiedBadgeProps {
  label?: string;
  compact?: boolean;
}

/** Verification badge used across profile screens. */
export function VerifiedBadge({ label = 'Verified', compact = false }: VerifiedBadgeProps) {
  const { colors, radius, spacing } = useTheme();
  return (
    <View
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.secondary,
        borderRadius: radius.pill,
        paddingHorizontal: compact ? spacing.sm : spacing.md,
        paddingVertical: compact ? 3 : spacing.xs,
      }}
    >
      <AppIcon name="shield-checkmark" size={compact ? 12 : 14} color={colors.verified} />
      {!compact ? (
        <AppText variant="caption" color={colors.verified} style={{ marginLeft: spacing.xs, fontWeight: '700' }}>
          {label}
        </AppText>
      ) : null}
    </View>
  );
}
