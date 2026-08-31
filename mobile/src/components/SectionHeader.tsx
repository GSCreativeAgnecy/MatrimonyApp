import React from 'react';
import { StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { useTheme } from '../theme/ThemeProvider';

interface SectionHeaderProps {
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
  actionLabel?: string;
  onAction?: () => void;
}

export function SectionHeader({ title, subtitle, right, actionLabel, onAction }: SectionHeaderProps) {
  const { colors, spacing } = useTheme();
  return (
    <View style={[styles.row, { marginTop: spacing.xl, marginBottom: spacing.md }]}>
      <View style={{ flex: 1 }}>
        <AppText variant="h2">{title}</AppText>
        {subtitle ? (
          <AppText variant="bodySmall" style={{ marginTop: 2 }}>
            {subtitle}
          </AppText>
        ) : null}
      </View>
      {actionLabel && onAction ? (
        <AppText variant="label" color={colors.primary} onPress={onAction} accessibilityRole="button">
          {actionLabel}
        </AppText>
      ) : (
        right
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});
