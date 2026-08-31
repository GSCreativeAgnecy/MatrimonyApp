import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { FlatList, KeyboardAvoidingView, Platform, Pressable, StyleSheet, TextInput, View } from 'react-native';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppButton } from '../../components/AppButton';
import { AppHeader } from '../../components/AppHeader';
import { Modal } from '../../components/Modal';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';
import { useMessages, useSendMessage } from './hooks';
import { useSubscription } from '../premium/hooks';
import { ApiError } from '../../types/api';
import { Message } from '../../types/models';
import { relativeTime } from '../../utils/format';
import { useRoute, RouteProp, useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AppStackParamList } from '../../navigation/types';

/** Local free-tier reply allowance per conversation (UX affordance only — the backend remains authoritative). */
const FREE_REPLY_ALLOWANCE = 3;
const freeUsage = new Map<string, number>();

const FREE_TEMPLATES = ['I like your profile.', 'Shall we know more about each other?'];

export function ChatConversationScreen() {
  const route = useRoute<RouteProp<AppStackParamList, 'ChatConversation'>>();
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { conversationId, otherUserName } = route.params;

  const { colors, radius, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const { data: subscription } = useSubscription();

  const isPremium = subscription?.is_premium === true;
  const messagingEnabled = config.features.messaging;

  const { data, isLoading, error, refetch, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useMessages(conversationId);
  const sendMutation = useSendMessage(conversationId);

  const [draft, setDraft] = useState('');
  const [upgradeVisible, setUpgradeVisible] = useState(false);
  const [gateMessage, setGateMessage] = useState<string | null>(null);
  const [banner, setBanner] = useState<string | null>(null);
  const listRef = useRef<FlatList<Message>>(null);

  const messages = useMemo(() => {
    // Backend returns messages newest-first. Pages are consumed with `before`
    // cursors, so flattening keeps newest messages at the front of the list.
    const pages = data?.pages ?? [];
    const flat: Message[] = [];
    for (const page of pages) {
      flat.push(...page);
    }
    return flat;
  }, [data]);

  useEffect(() => {
    const count = freeUsage.get(conversationId) ?? 0;
    if (!isPremium && count >= FREE_REPLY_ALLOWANCE) {
      setGateMessage('You have used all your free replies in this conversation.');
      setUpgradeVisible(true);
    }
  }, [conversationId, isPremium, messages.length]);

  const sendText = useCallback(
    async (body: string) => {
      if (!body.trim() || sendMutation.isPending) {
        return;
      }
      try {
        await sendMutation.mutateAsync(body.trim());
        setDraft('');
        setBanner(null);
        if (!isPremium) {
          const count = (freeUsage.get(conversationId) ?? 0) + 1;
          freeUsage.set(conversationId, count);
          if (count >= FREE_REPLY_ALLOWANCE) {
            setGateMessage('You have reached the free reply limit for this conversation.');
            setUpgradeVisible(true);
          } else {
            setBanner(`You have ${FREE_REPLY_ALLOWANCE - count} free ${FREE_REPLY_ALLOWANCE - count === 1 ? 'reply' : 'replies'} left.`);
          }
        }
      } catch (e) {
        const err = e as ApiError;
        if (err.isPremiumGated) {
          setGateMessage(err.message);
          setUpgradeVisible(true);
          return;
        }
        if (err.code === 'NOT_MATCHED') {
          setBanner('You can only message your matches.');
          return;
        }
        setBanner(err.message);
      }
    },
    [conversationId, isPremium, sendMutation],
  );

  if (isLoading) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.background }}>
        <AppHeader title={otherUserName ?? 'Chat'} showBack />
        <LoadingState />
      </View>
    );
  }

  if (error) {
    return (
      <View style={{ flex: 1, backgroundColor: colors.background }}>
        <AppHeader title={otherUserName ?? 'Chat'} showBack />
        <ErrorState onRetry={refetch} />
      </View>
    );
  }

  const renderItem = ({ item }: { item: Message }) => {
    const mine = item.sender_id === 'me';
    return (
      <View style={[styles.bubbleRow, { justifyContent: mine ? 'flex-end' : 'flex-start' }]}>
        <View
          style={[
            styles.bubble,
            {
              backgroundColor: mine ? colors.primary : colors.surface,
              borderRadius: radius.lg,
              maxWidth: '78%',
            },
          ]}
        >
          <AppText variant="body" color={mine ? colors.textInverse : colors.text}>
            {item.body ?? ''}
          </AppText>
          <AppText variant="caption" style={{ marginTop: 4, color: mine ? colors.secondary : colors.textSecondary }}>
            {relativeTime(item.created_at)}
          </AppText>
        </View>
      </View>
    );
  };

  return (
    <KeyboardAvoidingView
      style={{ flex: 1, backgroundColor: colors.background }}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <AppHeader title={otherUserName ?? 'Chat'} showBack />

      {banner ? (
        <View style={{ backgroundColor: colors.secondary, paddingVertical: 8, paddingHorizontal: 16 }}>
          <AppText variant="bodySmall" color={colors.primary}>
            {banner}
          </AppText>
        </View>
      ) : null}

      <FlatList
        ref={listRef}
        inverted
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={renderItem}
        contentContainerStyle={{ padding: spacing.lg }}
        onEndReachedThreshold={0.3}
        onEndReached={() => hasNextPage && fetchNextPage()}
        ListFooterComponent={isFetchingNextPage ? <LoadingState /> : null}
        keyboardShouldPersistTaps="handled"
      />

      {!messagingEnabled ? (
        <View style={[styles.inputBar, { backgroundColor: colors.surface }]}>
          <AppText variant="bodySmall" center>
            Messaging is temporarily disabled by the app configuration.
          </AppText>
        </View>
      ) : isPremium ? (
        <View style={[styles.inputBar, { backgroundColor: colors.surface }]}>
          <TextInput
            value={draft}
            onChangeText={setDraft}
            placeholder="Type a message…"
            placeholderTextColor={colors.textSecondary}
            style={[styles.input, { backgroundColor: colors.background, borderRadius: radius.pill, color: colors.text }]}
            multiline
          />
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Send message"
            onPress={() => sendText(draft)}
            style={[styles.send, { backgroundColor: colors.primary, borderRadius: radius.pill }]}
          >
            <AppIcon name="send" size={18} color={colors.textInverse} />
          </Pressable>
        </View>
      ) : (
        <View style={[styles.templateBar, { backgroundColor: colors.surface }]}>
          <AppText variant="caption" center style={{ marginBottom: spacing.sm }}>
            Free members can send these message templates
          </AppText>
          <View style={{ flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'center', gap: spacing.sm }}>
            {FREE_TEMPLATES.map((template) => (
              <Pressable
                key={template}
                onPress={() => sendText(template)}
                style={[styles.templateChip, { backgroundColor: colors.secondary, borderRadius: radius.pill }]}
              >
                <AppText variant="pill" color={colors.primary}>
                  {template}
                </AppText>
              </Pressable>
            ))}
          </View>
          <Pressable onPress={() => setUpgradeVisible(true)} style={{ marginTop: spacing.sm }} accessibilityRole="button">
            <AppText variant="label" color={colors.accent} center>
              Upgrade to send free-form messages
            </AppText>
          </Pressable>
        </View>
      )}

      <Modal
        visible={upgradeVisible}
        onClose={() => setUpgradeVisible(false)}
        title="Upgrade to continue chatting"
        message={gateMessage ?? 'Premium members enjoy unlimited messaging with their matches.'}
        actions={[
          { label: 'View Plans', onPress: () => navigation.navigate('MainTabs', { screen: 'PremiumTab' }) },
          { label: 'Not Now', onPress: () => undefined, variant: 'ghost' },
        ]}
      />
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  bubbleRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  bubble: {
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  inputBar: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
  },
  input: {
    flex: 1,
    paddingHorizontal: 16,
    paddingVertical: 10,
    maxHeight: 100,
  },
  send: {
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: 10,
  },
  templateBar: {
    padding: 12,
  },
  templateChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
  },
});
