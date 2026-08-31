import React from 'react';
import { StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { AppIcon } from './AppIcon';
import { AppButton } from './AppButton';
import { useTheme } from '../theme/ThemeProvider';
import { ApiError } from '../types/api';

interface ErrorStateProps {
  onRetry?: () => void;
  message?: string;
  compact?: boolean;
  error?: unknown;
}

/**
 * Branded error state. Never shows raw API errors, stack traces or internal
 * details to the user.
 */
export function ErrorState({ onRetry, message, compact = false, error }: ErrorStateProps) {
  const { colors } = useTheme();

  const friendly = () => {
    if (message) {
      return message;
    }
    if (error instanceof ApiError) {
      switch (error.code) {
        case 'NETWORK_ERROR':
          return 'You appear to be offline. Please check your connection and try again.';
        case 'RATE_LIMIT_EXCEEDED':
          return 'Too many attempts. Please try again in a little while.';
        default:
          return 'Something went wrong. Please try again.';
      }
    }
    return 'Something went wrong. Please try again.';
  };

  return (
    <View style={[styles.container, compact ? styles.compact : styles.full]}>
      <AppIcon name="cloud-offline-outline" size={40} color={colors.textSecondary} />
      <AppText variant="h3" center style={{ marginTop: 12 }}>
        {friendly()}
      </AppText>
      {onRetry ? (
        <View style={{ marginTop: 16, width: '60%' }}>
          <AppButton title="Try Again" onPress={onRetry} size="md" />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
  },
  full: {
    flexGrow: 1,
  },
  compact: {
    padding: 16,
  },
});
