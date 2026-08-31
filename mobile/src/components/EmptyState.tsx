import React from 'react';
import { StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { AppIcon, IconName } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';

interface EmptyStateProps {
  icon?: IconName;
  title: string;
  message?: string;
  children?: React.ReactNode;
}

export function EmptyState({ icon = 'heart-outline', title, message, children }: EmptyStateProps) {
  const { colors } = useTheme();
  return (
    <View style={styles.container}>
      <View
        style={{
          width: 72,
          height: 72,
          borderRadius: 36,
          backgroundColor: colors.secondary,
          alignItems: 'center',
          justifyContent: 'center',
          marginBottom: 16,
        }}
      >
        <AppIcon name={icon} size={34} color={colors.primary} />
      </View>
      <AppText variant="h2" center>
        {title}
      </AppText>
      {message ? (
        <AppText variant="body" center style={{ marginTop: 8, maxWidth: 280 }}>
          {message}
        </AppText>
      ) : null}
      {children ? <View style={{ marginTop: 20, width: '100%', maxWidth: 280 }}>{children}</View> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 32,
    flexGrow: 1,
  },
});
