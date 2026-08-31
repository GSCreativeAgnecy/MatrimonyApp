import React, { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppHeader } from '../../components/AppHeader';
import { ProfileAvatar } from '../../components/ProfileAvatar';
import { NotificationBadge } from '../../components/NotificationBadge';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { useConversations } from './hooks';
import { AppStackParamList } from '../../navigation/types';
import { relativeTime } from '../../utils/format';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

type Tab = 'active' | 'pending';

export function ChatRoomScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, spacing } = useTheme();
  const insets = useSafeAreaInsets();

  const { data: conversations, isLoading, error, refetch } = useConversations();
  const [tab, setTab] = useState<Tab>('active');

  const active = conversations ?? [];

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <AppHeader title="Conversations" />

      <View style={styles.tabs}>
        <TabButton label="Active Chats" active={tab === 'active'} onPress={() => setTab('active')} count={active.length} />
        <TabButton label="Pending Requests" active={tab === 'pending'} onPress={() => setTab('pending')} count={0} />
      </View>

      {isLoading ? (
        <LoadingState message="Loading conversations…" />
      ) : error ? (
        <ErrorState onRetry={refetch} />
      ) : tab === 'pending' ? (
        <EmptyState
          icon="mail-open-outline"
          title="No pending requests"
          message="Chat requests are not available yet. Once enabled by the backend they will appear here."
        />
      ) : active.length === 0 ? (
        <EmptyState
          icon="chatbubbles-outline"
          title="No conversations yet"
          message="Start connecting with profiles you like. Conversations appear here once you match."
        />
      ) : (
        <View style={{ flex: 1, paddingHorizontal: spacing.lg }}>
          {active.map((conversation) => (
            <Pressable
              key={conversation.id}
              accessibilityRole="button"
              onPress={() =>
                navigation.navigate('ChatConversation', {
                  conversationId: conversation.id,
                  otherUserId: conversation.other_user_id,
                  otherUserName: conversation.other_user_name ?? undefined,
                })
              }
              style={({ pressed }) => [
                styles.row,
                { backgroundColor: colors.surface, borderRadius: 16, opacity: pressed ? 0.92 : 1 },
              ]}
            >
              <ProfileAvatar uri={conversation.other_user_photo} firstName={conversation.other_user_name} size={52} />
              <View style={{ flex: 1, marginLeft: spacing.md }}>
                <AppText variant="h3" numberOfLines={1}>
                  {conversation.other_user_name ?? 'Match'}
                </AppText>
                <AppText variant="bodySmall" numberOfLines={1} style={{ marginTop: 2 }}>
                  {conversation.last_message_preview ?? 'Say hello!'}
                </AppText>
              </View>
              <View style={{ alignItems: 'flex-end', marginLeft: spacing.sm }}>
                <AppText variant="caption">{relativeTime(conversation.last_message_at)}</AppText>
                {conversation.unread_count > 0 ? (
                  <View style={{ marginTop: 6 }}>
                    <NotificationBadge count={conversation.unread_count} />
                  </View>
                ) : null}
              </View>
            </Pressable>
          ))}
        </View>
      )}
      <View style={{ height: insets.bottom }} />
    </View>
  );
}

function TabButton({ label, active, onPress, count }: { label: string; active: boolean; onPress: () => void; count: number }) {
  const { colors, radius, spacing } = useTheme();
  return (
    <Pressable
      accessibilityRole="tab"
      accessibilityState={{ selected: active }}
      onPress={onPress}
      style={[
        styles.tab,
        { borderRadius: radius.pill, backgroundColor: active ? colors.primary : colors.surface },
      ]}
    >
      <AppText variant="pill" color={active ? colors.textInverse : colors.textSecondary}>
        {label}
      </AppText>
      {count > 0 ? (
        <View style={{ marginLeft: spacing.xs }}>
          <NotificationBadge count={count} />
        </View>
      ) : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  tabs: {
    flexDirection: 'row',
    gap: 8,
    paddingHorizontal: 16,
    marginBottom: 16,
  },
  tab: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    marginBottom: 10,
  },
});
