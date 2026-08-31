import React from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, StyleProp, StyleSheet, View, ViewStyle } from 'react-native';
import { SafeAreaView, useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '../theme/ThemeProvider';

interface ScreenContainerProps {
  children: React.ReactNode;
  scroll?: boolean;
  keyboardAvoiding?: boolean;
  contentContainerStyle?: StyleProp<ViewStyle>;
  style?: StyleProp<ViewStyle>;
  edges?: ('top' | 'right' | 'bottom' | 'left')[];
}

/**
 * Standard screen wrapper: safe areas + themed background + optional keyboard
 * avoidance and scroll.
 */
export function ScreenContainer({
  children,
  scroll = false,
  keyboardAvoiding = false,
  contentContainerStyle,
  style,
  edges = ['top', 'left', 'right'],
}: ScreenContainerProps) {
  const { colors, spacing } = useTheme();
  const insets = useSafeAreaInsets();

  const inner = scroll ? (
    <ScrollView
      showsVerticalScrollIndicator={false}
      keyboardShouldPersistTaps="handled"
      contentContainerStyle={[{ padding: spacing.lg, paddingBottom: Math.max(insets.bottom, spacing.xl) }, contentContainerStyle]}
    >
      {children}
    </ScrollView>
  ) : (
    <View style={[styles.flex, { padding: spacing.lg }, contentContainerStyle]}>{children}</View>
  );

  return (
    <SafeAreaView edges={edges} style={[{ flex: 1, backgroundColor: colors.background }, style]}>
      {keyboardAvoiding ? (
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : undefined}
          style={styles.flex}
          keyboardVerticalOffset={Platform.OS === 'ios' ? 64 : 0}
        >
          {inner}
        </KeyboardAvoidingView>
      ) : (
        inner
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  flex: {
    flex: 1,
  },
});
