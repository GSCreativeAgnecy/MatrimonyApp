import React from 'react';
import { Modal as RNModal, Pressable, StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { AppButton } from './AppButton';
import { AppIcon } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';

interface ModalProps {
  visible: boolean;
  onClose: () => void;
  title?: string;
  message?: string;
  children?: React.ReactNode;
  actions?: { label: string; onPress: () => void; variant?: 'primary' | 'ghost' }[];
}

/** Centered branded modal. */
export function Modal({ visible, onClose, title, message, children, actions }: ModalProps) {
  const { colors, radius, spacing } = useTheme();
  return (
    <RNModal visible={visible} transparent animationType="fade" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.xxl, padding: spacing.xl }]}>
          <View style={styles.closeRow}>
            <Pressable onPress={onClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close">
              <AppIcon name="close" size={20} color={colors.textSecondary} />
            </Pressable>
          </View>
          {title ? (
            <AppText variant="h2" center style={{ marginBottom: spacing.sm }}>
              {title}
            </AppText>
          ) : null}
          {message ? (
            <AppText variant="body" center style={{ marginBottom: spacing.lg }}>
              {message}
            </AppText>
          ) : null}
          {children}
          {actions && actions.length > 0 ? (
            <View style={{ marginTop: spacing.lg }}>
              {actions.map((action) => (
                <View key={action.label} style={{ marginBottom: spacing.sm }}>
                  <AppButton
                    title={action.label}
                    onPress={() => {
                      action.onPress();
                      onClose();
                    }}
                    variant={action.variant ?? 'primary'}
                    size="md"
                  />
                </View>
              ))}
            </View>
          ) : null}
        </View>
      </View>
    </RNModal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.4)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  card: {
    width: '100%',
    maxWidth: 400,
  },
  closeRow: {
    alignItems: 'flex-end',
    marginBottom: 4,
  },
});
