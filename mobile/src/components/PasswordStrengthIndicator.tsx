import React from 'react';
import { StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { useTheme } from '../theme/ThemeProvider';
import { PasswordStrength } from '../utils/validators';

const BAR_COLORS = ['#C62828', '#D86C2C', '#C9A24B', '#6F9F4A', '#2E7D32'];

interface PasswordStrengthIndicatorProps {
  strength: PasswordStrength;
}

/** Visual password strength meter. Communicates with color AND text. */
export function PasswordStrengthIndicator({ strength }: PasswordStrengthIndicatorProps) {
  const { colors, radius, spacing } = useTheme();
  const color = strength.score > 0 ? BAR_COLORS[strength.score] : colors.border;

  return (
    <View style={{ marginTop: spacing.xs, marginBottom: spacing.lg }}>
      <View style={styles.bars}>
        {[1, 2, 3, 4].map((level) => (
          <View
            key={level}
            style={[
              styles.bar,
              {
                backgroundColor: strength.score >= level ? color : colors.border,
                borderRadius: radius.xs,
              },
            ]}
          />
        ))}
      </View>
      {strength.label ? (
        <AppText variant="caption" color={color} style={{ marginTop: spacing.xs }}>
          Password strength: {strength.label}
        </AppText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  bars: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  bar: {
    flex: 1,
    height: 4,
    marginHorizontal: 2,
  },
});
