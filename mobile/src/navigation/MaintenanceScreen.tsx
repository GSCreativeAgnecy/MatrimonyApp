import React from 'react';
import { StyleSheet, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { AppText } from '../components/AppText';
import { AppIcon } from '../components/AppIcon';
import { useTheme } from '../theme/ThemeProvider';
import { useRemoteConfig } from '../config/RemoteConfigProvider';

/** Shown when the backend marks the app as under maintenance. */
export function MaintenanceScreen() {
  const { colors, radius, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const insets = useSafeAreaInsets();

  return (
    <LinearGradient colors={[colors.primary, colors.primaryDark]} style={styles.container}>
      <View style={{ paddingTop: insets.top + 40, paddingBottom: insets.bottom + 24, alignItems: 'center' }}>
        <View style={{ width: 80, height: 80, borderRadius: radius.pill, backgroundColor: colors.accent, alignItems: 'center', justifyContent: 'center' }}>
          <AppIcon name="hammer" size={36} color={colors.textInverse} />
        </View>
        <AppText variant="display" color={colors.textInverse} center style={{ marginTop: spacing.xl }}>
          {config.branding.app_name}
        </AppText>
        <AppText variant="h2" color={colors.secondary} center style={{ marginTop: spacing.lg }}>
          Under Maintenance
        </AppText>
        <AppText variant="body" color={colors.secondary} center style={{ marginTop: spacing.md, maxWidth: 300 }}>
          {config.app.maintenance_message ?? 'We are performing scheduled maintenance. Please check back soon.'}
        </AppText>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
});
