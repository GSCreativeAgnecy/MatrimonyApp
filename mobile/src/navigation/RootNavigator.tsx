import React from 'react';
import { NavigationContainer, DefaultTheme as NavDefaultTheme } from '@react-navigation/native';

import { useAuth } from '../auth/AuthContext';
import { useTheme } from '../theme/ThemeProvider';
import { useRemoteConfig } from '../config/RemoteConfigProvider';
import { LoadingScreen } from './LoadingScreen';
import { MaintenanceScreen } from './MaintenanceScreen';
import { AuthNavigator } from './AuthNavigator';
import { AppNavigator } from './AppNavigator';

/**
 * Root navigator — protects authenticated routes.
 *
 *   Loading      -> shown while the session is restored from secure storage
 *   Maintenance  -> shown whenever the backend enables maintenance mode
 *   AuthNavigator -> unauthenticated users only
 *   AppNavigator  -> authenticated users only
 */
export function RootNavigator() {
  const { status } = useAuth();
  const { config, ready } = useRemoteConfig();
  const { colors } = useTheme();

  const navigationTheme = {
    ...NavDefaultTheme,
    colors: {
      ...NavDefaultTheme.colors,
      primary: colors.primary,
      background: colors.background,
      card: colors.surface,
      text: colors.text,
      border: colors.border,
    },
  };

  const showLoading = !ready || status === 'loading';
  const maintenance = config.app.maintenance_mode;

  const content = (() => {
    if (maintenance) {
      return <MaintenanceScreen />;
    }
    if (showLoading) {
      return <LoadingScreen />;
    }
    if (status === 'authenticated') {
      return <AppNavigator />;
    }
    return <AuthNavigator />;
  })();

  return <NavigationContainer theme={navigationTheme}>{content}</NavigationContainer>;
}
