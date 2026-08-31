import React, { useEffect, useRef } from 'react';
import { Animated, Modal, Pressable, StyleSheet, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { AppText } from './AppText';
import { AppIcon, IconName } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';

export interface MenuItem {
  key: string;
  label: string;
  icon: IconName;
  onPress: () => void;
  danger?: boolean;
}

interface MenuDrawerProps {
  visible: boolean;
  onClose: () => void;
  items: MenuItem[];
  footer?: React.ReactNode;
  header?: React.ReactNode;
}

/** Slide-out hamburger drawer with brand styling. */
export function MenuDrawer({ visible, onClose, items, footer, header }: MenuDrawerProps) {
  const { colors, radius, spacing, shadows } = useTheme();
  const insets = useSafeAreaInsets();
  const translateX = useRef(new Animated.Value(-320)).current;

  useEffect(() => {
    if (visible) {
      translateX.setValue(-320);
      Animated.spring(translateX, {
        toValue: 0,
        useNativeDriver: true,
        damping: 22,
        stiffness: 220,
      }).start();
    }
  }, [visible, translateX]);

  return (
    <Modal visible={visible} transparent animationType="none" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <Pressable style={StyleSheet.absoluteFill} onPress={onClose} accessibilityLabel="Close menu" />
        <Animated.View
          style={[
            styles.drawer,
            {
              transform: [{ translateX }],
              width: Math.min(320, 320),
              backgroundColor: colors.background,
              borderTopRightRadius: radius.xxl,
              borderBottomRightRadius: radius.xxl,
              paddingTop: insets.top + spacing.lg,
              paddingBottom: Math.max(insets.bottom, spacing.lg),
              ...shadows.elevated,
            },
          ]}
        >
          <View style={styles.header}>
            <Pressable onPress={onClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close menu">
              <AppIcon name="close" size={22} color={colors.textSecondary} />
            </Pressable>
          </View>

          {header ? <View style={{ paddingHorizontal: spacing.lg, marginBottom: spacing.lg }}>{header}</View> : null}

          <View style={{ flex: 1, paddingHorizontal: spacing.lg }}>
            {items.map((item) => (
              <Pressable
                key={item.key}
                accessibilityRole="button"
                onPress={() => {
                  onClose();
                  item.onPress();
                }}
                style={({ pressed }) => [
                  styles.item,
                  { borderRadius: radius.lg, opacity: pressed ? 0.7 : 1 },
                ]}
              >
                <AppIcon name={item.icon} size={22} color={item.danger ? colors.error : colors.primary} />
                <AppText variant="body" color={item.danger ? colors.error : colors.text} style={{ marginLeft: spacing.lg, flex: 1 }}>
                  {item.label}
                </AppText>
                <AppIcon name="chevron-forward" size={18} color={colors.textSecondary} />
              </Pressable>
            ))}
          </View>

          {footer ? (
            <View style={{ paddingHorizontal: spacing.lg, paddingTop: spacing.md }}>{footer}</View>
          ) : null}
        </Animated.View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.35)',
  },
  drawer: {
    flex: 1,
    maxWidth: 320,
    paddingHorizontal: 0,
  },
  header: {
    paddingHorizontal: 16,
    alignItems: 'flex-end',
    marginBottom: 8,
  },
  item: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 12,
    marginBottom: 4,
  },
});
