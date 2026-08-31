import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { AppIcon, IconName } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';

interface FilterChipProps {
  label: string;
  onPress?: () => void;
  active?: boolean;
  icon?: IconName;
  trailingIcon?: IconName;
}

/** Pill-shaped filter chip with dropdown chevron. */
export function FilterChip({ label, onPress, active = false, icon, trailingIcon = 'chevron-down' }: FilterChipProps) {
  const { colors, radius, spacing } = useTheme();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.chip,
        {
          borderRadius: radius.pill,
          backgroundColor: active ? colors.primary : colors.surface,
          borderColor: active ? colors.primary : colors.border,
          paddingHorizontal: spacing.md,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      {icon ? <AppIcon name={icon} size={16} color={active ? colors.textInverse : colors.primary} /> : null}
      <AppText
        variant="pill"
        color={active ? colors.textInverse : colors.text}
        style={{ marginHorizontal: spacing.xs }}
      >
        {label}
      </AppText>
      <AppIcon name={trailingIcon} size={14} color={active ? colors.textInverse : colors.textSecondary} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    height: 40,
    borderWidth: 1,
    paddingVertical: 0,
  },
});
