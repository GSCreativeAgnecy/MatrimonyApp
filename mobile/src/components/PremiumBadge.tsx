import React from 'react';
import { StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { AppIcon } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';

interface PremiumBadgeProps {
  label?: string;
  size?: 'sm' | 'md';
}

export function PremiumBadge({ label = 'Premium', size = 'sm' }: PremiumBadgeProps) {
  const { colors, radius, spacing } = useTheme();
  const isSm = size === 'sm';
  return (
    <View
      style={[
        styles.badge,
        {
          backgroundColor: colors.accent,
          borderRadius: radius.pill,
          paddingHorizontal: isSm ? spacing.sm : spacing.md,
          paddingVertical: isSm ? 2 : spacing.xs,
        },
      ]}
    >
      <AppIcon name="diamond" size={isSm ? 11 : 13} color={colors.textInverse} />
      <AppText
        variant="caption"
        color={colors.textInverse}
        style={{ marginLeft: 4, fontWeight: '800', fontSize: isSm ? 10 : 12 }}
      >
        {label}
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});
