import React from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppIcon, IconName } from '../../components/AppIcon';
import { AppHeader } from '../../components/AppHeader';
import { ProfileAvatar } from '../../components/ProfileAvatar';
import { AppButton } from '../../components/AppButton';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { useNotifications, useMarkNotificationRead, useMarkAllRead } from './hooks';
import { AppStackParamList } from '../../navigation/types';
import { relativeTime } from '../../utils/format';
import { AppNotification } from '../../types/models';

const TYPE_META: Record<string, { icon: IconName; title: string }> = {
  NEW_MATCH: { icon: 'heart', title: 'New Match' },
  NEW_MESSAGE: { icon: 'chatbubble', title: 'Message' },
  NEW_LIKE: { icon: 'heart-outline', title: 'Interest Received' },
  PROFILE_VIEW: { icon: 'eye-outline', title: 'Profile Viewed' },
  VERIFICATION_COMPLETE: { icon: 'shield-checkmark', title: 'Verification' },
  SUBSCRIPTION_EXPIRING: { icon: 'timer-outline', title: 'Subscription' },
  SYSTEM: { icon: 'notifications-outline', title: 'Ardhang Matrimony' },
};

export function AlertsScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, radius, spacing } = useTheme();

  const { data, isLoading, error, refetch } = useNotifications();
  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllRead();

  const openNotification = (notification: AppNotification) => {
    if (!notification.is_read) {
      markRead.mutate(notification.id);
    }
    const actorId = (notification.data?.user_id as string | undefined) ?? (notification.data?.actor_id as string | undefined);
    if (actorId && notification.type !== 'NEW_MATCH') {
      navigation.navigate('ProfileDetails', { userId: actorId });
      return;
    }
    switch (notification.type) {
      case 'NEW_MATCH':
        navigation.navigate('MainTabs', { screen: 'MatchesTab' });
        break;
      case 'NEW_MESSAGE':
        navigation.navigate('MainTabs', { screen: 'ChatTab' });
        break;
      case 'NEW_LIKE':
        navigation.navigate('MainTabs', { screen: 'MatchesTab' });
        break;
      default:
        break;
    }
  };

  if (isLoading) {
    return (
      <ScreenContainer>
        <AppHeader title="Alerts" />
        <LoadingState message="Loading your alerts…" />
      </ScreenContainer>
    );
  }

  if (error) {
    return (
      <ScreenContainer>
        <AppHeader title="Alerts" />
        <ErrorState onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const notifications = data ?? [];
  const unread = notifications.filter((n) => !n.is_read).length;

  return (
    <ScreenContainer scroll={false}>
      <AppHeader
        title="Alerts"
        right={
          unread > 0 ? (
            <Pressable onPress={() => markAllRead.mutate()} accessibilityRole="button" hitSlop={8}>
              <AppText variant="label" color={colors.primary}>
                Mark all read
              </AppText>
            </Pressable>
          ) : undefined
        }
      />

      {notifications.length === 0 ? (
        <EmptyState
          icon="notifications-off-outline"
          title="No alerts yet"
          message="When someone likes your profile, views it or messages you, you will see it here."
        />
      ) : (
        <View style={{ paddingHorizontal: spacing.lg }}>
          {notifications.map((notification) => {
            const meta = TYPE_META[notification.type] ?? TYPE_META.SYSTEM;
            return (
              <Pressable
                key={notification.id}
                accessibilityRole="button"
                onPress={() => openNotification(notification)}
                style={({ pressed }) => [
                  styles.row,
                  {
                    backgroundColor: notification.is_read ? colors.surface : colors.surfaceMuted,
                    borderRadius: radius.lg,
                    opacity: pressed ? 0.92 : 1,
                    borderLeftWidth: notification.is_read ? 0 : 3,
                    borderLeftColor: colors.accent,
                  },
                ]}
              >
                <View style={[styles.iconWrap, { backgroundColor: colors.secondary, borderRadius: radius.md }]}>
                  <AppIcon name={meta.icon} size={22} color={colors.primary} />
                </View>
                <View style={{ flex: 1, marginLeft: spacing.md }}>
                  <View style={{ flexDirection: 'row', alignItems: 'center' }}>
                    <AppText variant="h3" style={{ flex: 1 }} numberOfLines={1}>
                      {notification.title ?? meta.title}
                    </AppText>
                    <AppText variant="caption" style={{ marginLeft: spacing.sm }}>
                      {relativeTime(notification.created_at)}
                    </AppText>
                  </View>
                  <AppText variant="bodySmall" style={{ marginTop: 2 }} numberOfLines={2}>
                    {notification.body ?? ''}
                  </AppText>
                </View>
                {!notification.is_read ? <View style={[styles.dot, { backgroundColor: colors.accent }]} /> : null}
              </Pressable>
            );
          })}
        </View>
      )}

      {notifications.length > 0 ? (
        <View style={{ paddingHorizontal: spacing.lg, marginTop: spacing.lg }}>
          <AppButton title="Mark all as read" size="md" variant="outline" onPress={() => markAllRead.mutate()} />
        </View>
      ) : null}
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
    width: 46,
    height: 46,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    marginLeft: 8,
  },
});
