import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppIcon, IconName } from '../../components/AppIcon';
import { AppHeader } from '../../components/AppHeader';
import { ScreenContainer } from '../../components/ScreenContainer';
import { useTheme } from '../../theme/ThemeProvider';
import { useAuth } from '../../auth/AuthContext';
import { AppStackParamList } from '../../navigation/types';

interface Row {
  key: string;
  label: string;
  icon: IconName;
  screen?: keyof AppStackParamList;
  onPress?: () => void;
  danger?: boolean;
}

export function MoreScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, radius, spacing } = useTheme();
  const { signOut } = useAuth();

  const rows: Row[] = [
    { key: 'astro', label: 'Astro Matching', icon: 'planet', screen: 'HoroscopeMatch' },
    { key: 'plans', label: 'Membership Plans', icon: 'diamond', screen: 'MainTabs' },
    { key: 'referral', label: 'Referral Program', icon: 'gift', screen: 'Referral' },
    { key: 'stories', label: 'Success Stories', icon: 'heart-circle', onPress: () => navigation.navigate('MainTabs', { screen: 'MatchesTab' }) },
    { key: 'help', label: 'Help & Support', icon: 'help-buoy', screen: 'HelpSupport' },
    { key: 'logout', label: 'Logout', icon: 'log-out', danger: true, onPress: () => signOut() },
  ];

  const open = (row: Row) => {
    if (row.onPress) {
      row.onPress();
      return;
    }
    if (row.screen === 'MainTabs') {
      navigation.navigate('MainTabs', { screen: 'PremiumTab' });
      return;
    }
    if (row.screen) {
      navigation.navigate(row.screen as never);
    }
  };

  return (
    <ScreenContainer scroll>
      <AppHeader title="More Options" showBack />

      {rows.map((row) => (
        <Pressable
          key={row.key}
          accessibilityRole="button"
          onPress={() => open(row)}
          style={({ pressed }) => [
            styles.row,
            {
              backgroundColor: colors.surface,
              borderRadius: radius.lg,
              opacity: pressed ? 0.9 : 1,
            },
          ]}
        >
          <View style={[styles.iconWrap, { backgroundColor: colors.secondary, borderRadius: radius.md }]}>
            <AppIcon name={row.icon} size={20} color={row.danger ? colors.error : colors.primary} />
          </View>
          <AppText variant="body" color={row.danger ? colors.error : colors.text} style={{ flex: 1, marginLeft: spacing.md }}>
            {row.label}
          </AppText>
          <AppIcon name="chevron-forward" size={18} color={colors.textSecondary} />
        </Pressable>
      ))}
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 14,
    marginBottom: 10,
  },
  iconWrap: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
