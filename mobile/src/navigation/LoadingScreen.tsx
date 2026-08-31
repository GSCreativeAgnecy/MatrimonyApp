import React from 'react';
import { ActivityIndicator, StyleSheet, View } from 'react-native';

import { AppText } from '../components/AppText';
import { useTheme } from '../theme/ThemeProvider';
import { useRemoteConfig } from '../config/RemoteConfigProvider';

export function LoadingScreen() {
  const { colors } = useTheme();
  const { config } = useRemoteConfig();
  return (
    <View style={[styles.container, { backgroundColor: colors.background }]}>
      <ActivityIndicator size="large" color={colors.primary} />
      <AppText variant="h3" style={{ marginTop: 16 }}>
        {config.branding.app_name}
      </AppText>
      <AppText variant="caption" style={{ marginTop: 4 }}>
        Loading…
      </AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
