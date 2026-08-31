import React, { useState } from 'react';
import {
  KeyboardTypeOptions,
  Pressable,
  StyleProp,
  StyleSheet,
  TextInput,
  TextInputProps,
  View,
  ViewStyle,
} from 'react-native';

import { AppText } from './AppText';
import { AppIcon, IconName } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';

interface AppInputProps extends TextInputProps {
  label?: string;
  error?: string | null;
  helper?: string;
  leftIcon?: IconName;
  secureToggle?: boolean;
  containerStyle?: StyleProp<ViewStyle>;
}

/** Form input with label, error, optional secure toggle and leading icon. */
export function AppInput({
  label,
  error,
  helper,
  leftIcon,
  secureToggle,
  secureTextEntry,
  multiline,
  containerStyle,
  onFocus,
  onBlur,
  ...rest
}: AppInputProps) {
  const { colors, radius, typography, spacing } = useTheme();
  const [focused, setFocused] = useState(false);
  const [hidden, setHidden] = useState(secureTextEntry === true);

  return (
    <View style={[{ marginBottom: spacing.lg }, containerStyle]}>
      {label ? (
        <AppText variant="label" style={{ marginBottom: spacing.xs }}>
          {label}
        </AppText>
      ) : null}
      <View
        style={[
          styles.wrapper,
          {
            borderRadius: radius.md,
            borderColor: error ? colors.error : focused ? colors.primary : colors.border,
            borderWidth: 1.5,
            backgroundColor: colors.surface,
            height: multiline ? undefined : 52,
          },
        ]}
      >
        {leftIcon ? (
          <AppIcon name={leftIcon} size={20} color={focused ? colors.primary : colors.textSecondary} />
        ) : null}
        <TextInput
          {...rest}
          secureTextEntry={hidden}
          placeholderTextColor={colors.textSecondary}
          style={[
            styles.input,
            typography.body,
            { color: colors.text, paddingLeft: leftIcon ? spacing.sm : 0 },
          ]}
          onFocus={(e) => {
            setFocused(true);
            onFocus?.(e);
          }}
          onBlur={(e) => {
            setFocused(false);
            onBlur?.(e);
          }}
        />
        {secureToggle ? (
          <Pressable accessibilityRole="button" accessibilityLabel="Toggle password visibility" onPress={() => setHidden((h) => !h)} hitSlop={8}>
            <AppIcon name={hidden ? 'eye-off-outline' : 'eye-outline'} size={20} color={colors.textSecondary} />
          </Pressable>
        ) : null}
      </View>
      {error ? (
        <AppText variant="caption" color={colors.error} style={{ marginTop: spacing.xs }}>
          {error}
        </AppText>
      ) : helper ? (
        <AppText variant="caption" style={{ marginTop: spacing.xs }}>
          {helper}
        </AppText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 14,
    height: 52,
  },
  input: {
    flex: 1,
    paddingVertical: 0,
  },
});
