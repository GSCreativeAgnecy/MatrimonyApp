import React from 'react';
import { View } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

import { AppIcon } from '../components/AppIcon';
import { AppText } from '../components/AppText';
import { useTheme } from '../theme/ThemeProvider';
import { useUnreadCount } from '../features/alerts/hooks';
import { ProfileScreen } from '../features/profile/ProfileScreen';
import { MatchesScreen } from '../features/matches/MatchesScreen';
import { ChatRoomScreen } from '../features/chat/ChatRoomScreen';
import { AlertsScreen } from '../features/alerts/AlertsScreen';
import { PremiumScreen } from '../features/premium/PremiumScreen';
import { MainTabsParamList } from './types';

const Tab = createBottomTabNavigator<MainTabsParamList>();

const ICONS: Record<keyof MainTabsParamList, { active: React.ComponentProps<typeof AppIcon>['name']; inactive: React.ComponentProps<typeof AppIcon>['name'] }> = {
  ProfileTab: { active: 'person', inactive: 'person-outline' },
  MatchesTab: { active: 'heart', inactive: 'heart-outline' },
  ChatTab: { active: 'chatbubbles', inactive: 'chatbubbles-outline' },
  AlertsTab: { active: 'notifications', inactive: 'notifications-outline' },
  PremiumTab: { active: 'diamond', inactive: 'diamond-outline' },
};

export function MainTabs() {
  const { colors } = useTheme();
  const { data: unread } = useUnreadCount();

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.textSecondary,
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: 64,
          paddingBottom: 8,
          paddingTop: 6,
        },
        tabBarLabel: ({ color, focused }) => (
          <AppText variant="caption" color={color} style={{ fontWeight: focused ? '700' : '400', fontSize: 11, lineHeight: 14 }}>
            {route.name.replace('Tab', '')}
          </AppText>
        ),
        tabBarIcon: ({ focused, color }) => (
          <AppIcon name={focused ? ICONS[route.name as keyof MainTabsParamList].active : ICONS[route.name as keyof MainTabsParamList].inactive} size={24} color={color} />
        ),
      })}
    >
      <Tab.Screen name="ProfileTab" component={ProfileScreen} />
      <Tab.Screen name="MatchesTab" component={MatchesScreen} />
      <Tab.Screen name="ChatTab" component={ChatRoomScreen} />
      <Tab.Screen
        name="AlertsTab"
        component={AlertsScreen}
        options={{
          tabBarBadge: (unread ?? 0) > 0 ? unread : undefined,
          tabBarBadgeStyle: { backgroundColor: colors.error, fontSize: 11, color: '#FFFFFF' },
        }}
      />
      <Tab.Screen name="PremiumTab" component={PremiumScreen} />
    </Tab.Navigator>
  );
}
