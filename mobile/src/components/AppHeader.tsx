import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';

import { AppText } from './AppText';
import { AppIcon, IconName } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

interface AppHeaderProps {
  title: string;
  subtitle?: string;
  showBack?: boolean;
  leftIcon?: IconName;
  onLeftPress?: () => void;
  right?: React.ReactNode;
}

/** Consistent app bar with optional back button and right slot. */
export function AppHeader({ title, subtitle, showBack = false, leftIcon, onLeftPress, right }: AppHeaderProps) {
  const { colors, spacing } = useTheme();
  const navigation = useNavigation();
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.container, { paddingTop: insets.top + spacing.sm }]}>
      <View style={styles.row}>
        {showBack || leftIcon ? (
          <Pressable
            onPress={onLeftPress ?? (() => navigation.goBack())}
            hitSlop={10}
            style={[styles.side, styles.left]}
            accessibilityRole="button"
            accessibilityLabel={showBack ? 'Go back' : undefined}
          >
            <AppIcon name={leftIcon ?? 'arrow-back'} size={24} color={colors.text} />
          </Pressable>
        ) : (
          <View style={[styles.side, styles.left]} />
        )}
        <View style={{ flex: 1, alignItems: 'center' }}>
          <AppText variant="h2" numberOfLines={1}>
            {title}
          </AppText>
          {subtitle ? (
            <AppText variant="caption" numberOfLines={1}>
              {subtitle}
            </AppText>
          ) : null}
        </View>
        <View style={[styles.side, { alignItems: 'flex-end' }]}>{right ?? null}</View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 8,
    paddingBottom: 8,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    minHeight: 44,
  },
  side: {
    width: 44,
    justifyContent: 'center',
  },
  left: {
    alignItems: 'flex-start',
  },
});
