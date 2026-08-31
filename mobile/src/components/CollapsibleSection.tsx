import React, { useState } from 'react';
import { LayoutAnimation, Platform, Pressable, StyleSheet, UIManager, View } from 'react-native';

import { AppText } from './AppText';
import { AppIcon } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
  trailing?: React.ReactNode;
}

export function CollapsibleSection({ title, children, defaultOpen = true, trailing }: CollapsibleSectionProps) {
  const { colors, radius, spacing } = useTheme();
  const [open, setOpen] = useState(defaultOpen);

  const toggle = () => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setOpen((o) => !o);
  };

  return (
    <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.xl, marginBottom: spacing.md }]}>
      <Pressable
        onPress={toggle}
        accessibilityRole="button"
        accessibilityState={{ expanded: open }}
        style={styles.header}
      >
        <AppText variant="h3" style={{ flex: 1 }}>
          {title}
        </AppText>
        {trailing}
        <AppIcon name={open ? 'chevron-up' : 'chevron-down'} size={20} color={colors.textSecondary} />
      </Pressable>
      {open ? <View style={{ paddingHorizontal: spacing.lg, paddingBottom: spacing.lg }}>{children}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    paddingTop: 4,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 16,
  },
});
