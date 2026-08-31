import 'react-native-gesture-handler';
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { QueryClientProvider } from '@tanstack/react-query';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { GestureHandlerRootView } from 'react-native-gesture-handler';

import { queryClient } from './src/query/client';
import { RemoteConfigProvider } from './src/config/RemoteConfigProvider';
import { ThemeProvider } from './src/theme/ThemeProvider';
import { AuthProvider } from './src/auth/AuthContext';
import { RootNavigator } from './src/navigation/RootNavigator';

export default function App() {
  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <QueryClientProvider client={queryClient}>
        <SafeAreaProvider>
          <RemoteConfigProvider>
            <ThemeProvider>
              <AuthProvider>
                <RootNavigator />
                <StatusBar style="auto" />
              </AuthProvider>
            </ThemeProvider>
          </RemoteConfigProvider>
        </SafeAreaProvider>
      </QueryClientProvider>
    </GestureHandlerRootView>
  );
}
