import React, { useCallback, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { FlashList } from '@shopify/flash-list';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppHeader } from '../../components/AppHeader';
import { FilterChip } from '../../components/FilterChip';
import { ProfileCard } from '../../components/ProfileCard';
import { LoadingState } from '../../components/LoadingState';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import { Modal } from '../../components/Modal';
import { useTheme } from '../../theme/ThemeProvider';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';
import { useFeedProfiles, useSwipe } from './hooks';
import { ApiError } from '../../types/api';
import { SwipeResult } from '../../types/models';
import { AppStackParamList } from '../../navigation/types';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export function MatchesScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, radius, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const insets = useSafeAreaInsets();

  const { feed, profiles, loadingProfiles } = useFeedProfiles();
  const swipeMutation = useSwipe();

  const [matchModal, setMatchModal] = useState<{ name: string; photo?: string | null } | null>(null);
  const [upgradeModal, setUpgradeModal] = useState<string | null>(null);

  const items = (feed.data?.pages ?? []).flatMap((page) => page.items ?? []);
  const loadedCount = items.length;
  const isInitialLoading = feed.isLoading || (loadingProfiles && loadedCount === 0);

  const handleSwipe = useCallback(
    async (userId: string, action: 'LIKE' | 'PASS' | 'SUPER_LIKE', name?: string | null, photo?: string | null) => {
      try {
        const result = await swipeMutation.mutateAsync({ userId, action });
        if (result.match_created && (result as SwipeResult).match_id) {
          setMatchModal({ name: name ?? 'Your match', photo });
        }
      } catch (e) {
        const err = e as ApiError;
        if (err.code === 'DUPLICATE_SWIPE' || err.code === 'ALREADY_MATCHED') {
          return;
        }
        if (err.isPremiumGated) {
          setUpgradeModal('Upgrade to continue matching. Premium members get unlimited daily matches and advanced discovery.');
          return;
        }
        if (err.code === 'RATE_LIMIT_EXCEEDED') {
          setUpgradeModal('You have reached your daily matching limit. Upgrade for unlimited swipes.');
          return;
        }
        setUpgradeModal(err.message);
      }
    },
    [swipeMutation],
  );

  const renderItem = ({ item }: { item: (typeof items)[number] }) => {
    const profile = profiles[item.candidate_user_id];
    if (!profile) {
      return (
        <View style={{ flex: 1, padding: spacing.md }}>
          <LoadingState message="Loading profile…" />
        </View>
      );
    }
    return (
      <View style={styles.cardWrap}>
        <ProfileCard
          profile={profile}
          reasonCodes={item.reason_codes}
          actionPending={swipeMutation.isPending}
          onPress={() => navigation.navigate('ProfileDetails', { userId: item.candidate_user_id })}
          onSendInterest={() => handleSwipe(item.candidate_user_id, 'LIKE', profile.first_name, profile.profile_photo)}
          onShortlist={() => handleSwipe(item.candidate_user_id, 'SUPER_LIKE', profile.first_name, profile.profile_photo)}
          onMessage={() => navigation.navigate('ProfileDetails', { userId: item.candidate_user_id })}
        />
      </View>
    );
  };

  const emptyFeed = !isInitialLoading && !feed.error && items.length === 0;

  return (
    <View style={{ flex: 1, backgroundColor: colors.background }}>
      <AppHeader title="Discover Matches" right={<FilterChip label="Filter" onPress={() => navigation.navigate('MatchFilters')} />} />

      <View style={{ paddingHorizontal: spacing.lg, marginBottom: spacing.md }}>
        <View style={styles.chipRow}>
          <FilterChip label="Community" onPress={() => navigation.navigate('MatchFilters')} />
          <FilterChip label="Location" onPress={() => navigation.navigate('MatchFilters')} />
          <FilterChip label="Profession" onPress={() => navigation.navigate('MatchFilters')} />
        </View>

        <Pressable
          accessibilityRole="button"
          onPress={() => navigation.navigate('MatchFilters')}
          style={({ pressed }) => [
            styles.banner,
            {
              backgroundColor: colors.secondary,
              borderRadius: radius.lg,
              marginTop: spacing.md,
              opacity: pressed ? 0.9 : 1,
            },
          ]}
        >
          <View style={[styles.iconWrap, { backgroundColor: colors.primary, borderRadius: radius.pill }]}>
            <AppIcon name="search" size={20} color={colors.textInverse} />
          </View>
          <View style={{ flex: 1, marginLeft: spacing.md }}>
            <AppText variant="h3">{config.branding.tagline}</AppText>
            <AppText variant="caption">Refine your search with advanced filters</AppText>
          </View>
          <AppIcon name="chevron-forward" size={20} color={colors.primary} />
        </Pressable>
      </View>

      {isInitialLoading ? (
        <LoadingState message="Finding compatible profiles…" />
      ) : feed.error ? (
        <ErrorState onRetry={feed.refetch} />
      ) : emptyFeed ? (
        <EmptyState
          icon="heart-outline"
          title="No matches yet"
          message="Complete your profile to discover better matches."
        />
      ) : (
        <FlashList
          data={items}
          keyExtractor={(item) => item.candidate_user_id}
          renderItem={renderItem}
          numColumns={2}
          onEndReached={() => feed.fetchNextPage()}
          onEndReachedThreshold={0.4}
          onRefresh={feed.refetch}
          refreshing={feed.isRefetching}
          contentContainerStyle={{ paddingHorizontal: spacing.lg, paddingBottom: insets.bottom + spacing.xl }}
        />
      )}

      <Modal
        visible={Boolean(matchModal)}
        onClose={() => setMatchModal(null)}
        title="It's a Match!"
        message={matchModal ? `You and ${matchModal.name} liked each other. Start a conversation!` : undefined}
        actions={[
          { label: 'Send Message', onPress: () => navigation.navigate('MainTabs', { screen: 'ChatTab' }) },
          { label: 'Keep Browsing', onPress: () => undefined, variant: 'ghost' },
        ]}
      />

      <Modal
        visible={Boolean(upgradeModal)}
        onClose={() => setUpgradeModal(null)}
        title="Upgrade to Premium"
        message={upgradeModal ?? undefined}
        actions={[
          { label: 'View Plans', onPress: () => navigation.navigate('MainTabs', { screen: 'PremiumTab' }) },
          { label: 'Not Now', onPress: () => undefined, variant: 'ghost' },
        ]}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  chipRow: {
    flexDirection: 'row',
    gap: 8,
  },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
  },
  iconWrap: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cardWrap: {
    flex: 1,
    padding: 6,
  },
});
