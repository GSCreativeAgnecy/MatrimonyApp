import React from 'react';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

import { MainTabs } from './MainTabs';
import { DashboardScreen } from '../features/dashboard/DashboardScreen';
import { ProfileDetailsScreen } from '../features/profile/ProfileDetailsScreen';
import { EditProfileScreen } from '../features/profile/EditProfileScreen';
import { PhotosScreen } from '../features/profile/PhotosScreen';
import { MatchFiltersScreen } from '../features/matches/MatchFiltersScreen';
import { ChatConversationScreen } from '../features/chat/ChatConversationScreen';
import { HoroscopeMatchScreen } from '../features/horoscope/HoroscopeMatchScreen';
import { ServicesScreen } from '../features/services/ServicesScreen';
import { SettingsScreen } from '../features/settings/SettingsScreen';
import { HelpSupportScreen } from '../features/settings/HelpSupportScreen';
import { ReferralScreen } from '../features/settings/ReferralScreen';
import { MoreScreen } from '../features/settings/MoreScreen';
import { JobVerificationScreen } from '../features/premium/JobVerificationScreen';
import { AppStackParamList } from './types';
import { useTheme } from '../theme/ThemeProvider';

const Stack = createNativeStackNavigator<AppStackParamList>();

export function AppNavigator() {
  const { colors } = useTheme();
  return (
    <Stack.Navigator
      initialRouteName="Dashboard"
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: colors.background },
      }}
    >
      <Stack.Screen name="MainTabs" component={MainTabs} />
      <Stack.Screen name="Dashboard" component={DashboardScreen} />
      <Stack.Screen name="ProfileDetails" component={ProfileDetailsScreen} />
      <Stack.Screen name="EditProfile" component={EditProfileScreen} />
      <Stack.Screen name="Photos" component={PhotosScreen} />
      <Stack.Screen name="MatchFilters" component={MatchFiltersScreen} />
      <Stack.Screen name="ChatConversation" component={ChatConversationScreen} options={{ animation: 'slide_from_right' }} />
      <Stack.Screen name="HoroscopeMatch" component={HoroscopeMatchScreen} />
      <Stack.Screen name="Services" component={ServicesScreen} />
      <Stack.Screen name="Settings" component={SettingsScreen} />
      <Stack.Screen name="HelpSupport" component={HelpSupportScreen} />
      <Stack.Screen name="Referral" component={ReferralScreen} />
      <Stack.Screen name="More" component={MoreScreen} />
      <Stack.Screen name="JobVerification" component={JobVerificationScreen} />
    </Stack.Navigator>
  );
}
