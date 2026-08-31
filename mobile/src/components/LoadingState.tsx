import React from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { useTheme } from '../theme/ThemeProvider';

interface LoadingStateProps {
  message?: string;
  fullScreen?: boolean;
}

export function LoadingState({ message = 'Loading…', fullScreen = true }: LoadingStateProps) {
  const { colors } = useTheme();
  return (
    <View style={[styles.container, fullScreen && styles.fullScreen]}>
      <ActivityIndicator size="large" color={colors.primary} />
      {message ? (
        <AppText variant="body" color={colors.textSecondary} style={{ marginTop: 12 }}>
          {message}
        </AppText>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
  },
  fullScreen: {
    flex: 1,
  },
});
