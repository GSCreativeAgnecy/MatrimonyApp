import React, { useMemo, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { LinearGradient } from 'expo-linear-gradient';

import { AppText } from '../../components/AppText';
import { AppIcon, IconName } from '../../components/AppIcon';
import { ProfileAvatar } from '../../components/ProfileAvatar';
import { VerifiedBadge } from '../../components/VerifiedBadge';
import { NotificationBadge } from '../../components/NotificationBadge';
import { MenuDrawer, MenuItem } from '../../components/MenuDrawer';
import { ScreenContainer } from '../../components/ScreenContainer';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';
import { useAuth } from '../../auth/AuthContext';
import { useOwnProfile } from '../profile/hooks';
import { useUnreadCount } from '../alerts/hooks';
import { AppStackParamList } from '../../navigation/types';
import { useTheme } from '../../theme/ThemeProvider';
import { fullName, greeting, profileCompleteness } from '../../utils/format';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';

interface NavCard {
  key: string;
  title: string;
  subtitle: string;
  icon: IconName;
  screen: keyof AppStackParamList;
  badge?: number;
}

export function DashboardScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, radius, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const { user, signOut } = useAuth();
  const { data: profile, isLoading, error, refetch } = useOwnProfile();
  const { data: unread } = useUnreadCount();

  const [menuOpen, setMenuOpen] = useState(false);

  const completeness = useMemo(() => profileCompleteness(profile as unknown as Record<string, unknown>), [profile]);

  const navCards: NavCard[] = [
    {
      key: 'matches',
      title: 'Matches',
      subtitle: 'Search | Daily Recommendations | Shortlisted',
      icon: 'heart',
      screen: 'MainTabs',
    },
    {
      key: 'conversations',
      title: 'Conversations',
      subtitle: 'Messages | Requests | Chats',
      icon: 'chatbubbles',
      screen: 'MainTabs',
    },
    {
      key: 'activity',
      title: 'Activity',
      subtitle: 'Profile Visitors | Profile Mutual',
      icon: 'notifications',
      screen: 'MainTabs',
      badge: unread,
    },
    {
      key: 'services',
      title: 'Services',
      subtitle: 'Astrology | Personalised | Verification',
      icon: 'sparkles',
      screen: 'Services',
    },
    {
      key: 'profile',
      title: 'Profile',
      subtitle: 'View/Edit | Settings | Photos',
      icon: 'person-circle',
      screen: 'MainTabs',
    },
  ];

  const menuItems: MenuItem[] = [
    { key: 'horoscope', label: 'Horoscope Match', icon: 'planet', onPress: () => navigation.navigate('HoroscopeMatch') },
    { key: 'help', label: 'Help & Support', icon: 'help-buoy', onPress: () => navigation.navigate('HelpSupport') },
    { key: 'referral', label: 'Referral', icon: 'gift', onPress: () => navigation.navigate('Referral') },
    { key: 'settings', label: 'Settings', icon: 'settings', onPress: () => navigation.navigate('Settings') },
    { key: 'more', label: 'More Options', icon: 'ellipsis-horizontal-circle', onPress: () => navigation.navigate('More') },
    { key: 'logout', label: 'Logout', icon: 'log-out', danger: true, onPress: () => signOut() },
  ];

  const openCard = (card: NavCard) => {
    if (card.screen === 'MainTabs') {
      navigation.navigate('MainTabs', { screen: card.key === 'matches' ? 'MatchesTab' : card.key === 'conversations' ? 'ChatTab' : card.key === 'activity' ? 'AlertsTab' : 'ProfileTab' });
      return;
    }
    navigation.navigate(card.screen as never);
  };

  return (
    <ScreenContainer scroll>
      <View style={styles.topBar}>
        <Pressable onPress={() => setMenuOpen(true)} hitSlop={10} accessibilityRole="button" accessibilityLabel="Open menu">
          <AppIcon name="menu" size={26} color={colors.text} />
        </Pressable>
        <AppText variant="h3">{config.branding.app_name}</AppText>
        <Pressable onPress={() => navigation.navigate('MainTabs', { screen: 'AlertsTab' })} hitSlop={10} accessibilityRole="button" accessibilityLabel="Notifications">
          <View>
            <AppIcon name="notifications-outline" size={24} color={colors.text} />
            {unread ? (
              <View style={{ position: 'absolute', top: -6, right: -8 }}>
                <NotificationBadge count={unread} />
              </View>
            ) : null}
          </View>
        </Pressable>
      </View>

      <LinearGradient
        colors={[colors.primary, colors.primaryDark]}
        style={[styles.hero, { borderRadius: radius.xxl, padding: spacing.xl }]}
      >
        <View style={styles.heroTop}>
          <ProfileAvatar
            uri={profile?.profile_photo}
            firstName={profile?.first_name}
            lastName={profile?.last_name}
            size={64}
          />
          <View style={{ flex: 1, marginLeft: spacing.lg }}>
            <AppText variant="caption" color={colors.secondary}>
              {greeting()}
            </AppText>
            <AppText variant="h2" color={colors.textInverse} numberOfLines={1}>
              {fullName(profile?.first_name, profile?.last_name)}
            </AppText>
          </View>
          <VerifiedBadge compact />
        </View>

        <View style={{ marginTop: spacing.lg }}>
          <AppText variant="caption" color={colors.secondary}>
            Profile Completeness
          </AppText>
          <View style={styles.progressRow}>
            <View style={[styles.progressTrack, { backgroundColor: colors.overlay }]}>
              <View style={[styles.progressFill, { backgroundColor: colors.accent, width: `${completeness}%` }]} />
            </View>
            <AppText variant="label" color={colors.textInverse} style={{ marginLeft: spacing.md }}>
              {completeness}%
            </AppText>
          </View>
        </View>

        {completeness < 100 ? (
          <Pressable
            onPress={() => navigation.navigate('EditProfile')}
            style={({ pressed }) => [
              styles.cta,
              {
                backgroundColor: colors.accent,
                borderRadius: radius.lg,
                marginTop: spacing.lg,
                opacity: pressed ? 0.85 : 1,
              },
            ]}
            accessibilityRole="button"
          >
            <AppText variant="label" color={colors.textInverse}>
              Complete your profile
            </AppText>
            <AppIcon name="arrow-forward" size={18} color={colors.textInverse} />
          </Pressable>
        ) : null}
      </LinearGradient>

      {isLoading ? <LoadingState message="Loading your dashboard…" /> : null}
      {error ? <ErrorState onRetry={refetch} /> : null}

      <View style={styles.grid}>
        {navCards.map((card) => (
          <Pressable
            key={card.key}
            accessibilityRole="button"
            onPress={() => openCard(card)}
            style={({ pressed }) => [
              styles.card,
              {
                backgroundColor: colors.surface,
                borderRadius: radius.xl,
                padding: spacing.lg,
                opacity: pressed ? 0.92 : 1,
              },
            ]}
          >
            <View style={styles.cardTop}>
              <View style={[styles.iconWrap, { backgroundColor: colors.secondary, borderRadius: radius.md }]}>
                <AppIcon name={card.icon} size={22} color={colors.primary} />
              </View>
              {card.badge ? (
                <View style={{ position: 'absolute', top: 0, right: 0 }}>
                  <NotificationBadge count={card.badge} />
                </View>
              ) : null}
            </View>
            <AppText variant="h3" style={{ marginTop: spacing.md }}>
              {card.title}
            </AppText>
            <AppText variant="caption" style={{ marginTop: 4 }} numberOfLines={2}>
              {card.subtitle}
            </AppText>
          </Pressable>
        ))}
      </View>

      <MenuDrawer
        visible={menuOpen}
        onClose={() => setMenuOpen(false)}
        items={menuItems}
        header={
          <View>
            <AppText variant="h2">{config.branding.app_name}</AppText>
            <AppText variant="caption">{user?.email ?? ''}</AppText>
          </View>
        }
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  hero: {
    marginBottom: 8,
  },
  heroTop: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 6,
  },
  progressTrack: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 4,
  },
  cta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    paddingHorizontal: 16,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginTop: 12,
  },
  card: {
    width: '48.5%',
    marginBottom: 12,
  },
  cardTop: {
    flexDirection: 'row',
    position: 'relative',
  },
  iconWrap: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
