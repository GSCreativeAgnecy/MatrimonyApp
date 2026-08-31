import React, { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppButton } from '../../components/AppButton';
import { AppHeader } from '../../components/AppHeader';
import { ProfileAvatar } from '../../components/ProfileAvatar';
import { VerifiedBadge } from '../../components/VerifiedBadge';
import { Modal } from '../../components/Modal';
import { BottomSheet } from '../../components/BottomSheet';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { usePublicProfile, useSwipe } from '../matches/hooks';
import { useStartConversation } from '../chat/hooks';
import { moderationApi } from '../../api/moderation';
import { chatApi } from '../../api/chat';
import { ApiError } from '../../types/api';
import { AppStackParamList } from '../../navigation/types';
import { formatHeight, maritalStatusLabel, titleCase } from '../../utils/format';
import { imageUrl } from '../../utils/imageUrl';
import { Image } from 'react-native';

const REPORT_REASONS = [
  'FAKE_PROFILE',
  'SCAM',
  'HARASSMENT',
  'INAPPROPRIATE_CONTENT',
  'SPAM',
  'UNDERAGE',
  'IMPERSONATION',
  'OTHER',
];

export function ProfileDetailsScreen() {
  const route = useRoute<RouteProp<AppStackParamList, 'ProfileDetails'>>();
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { userId } = route.params;

  const { colors, radius, spacing } = useTheme();
  const { data: profile, isLoading, error, refetch } = usePublicProfile(userId);
  const swipeMutation = useSwipe();
  const startConversation = useStartConversation();

  const [actionError, setActionError] = useState<string | null>(null);
  const [reportOpen, setReportOpen] = useState(false);
  const [reportReason, setReportReason] = useState<string | null>(null);
  const [reported, setReported] = useState(false);
  const [blocked, setBlocked] = useState(false);

  const isMatched = Boolean((profile as { email?: string })?.email || (profile as { phone_number?: string })?.phone_number);

  const sendInterest = async () => {
    setActionError(null);
    try {
      await swipeMutation.mutateAsync({ userId, action: 'LIKE' });
    } catch (e) {
      setActionError(friendlySwipeError(e as ApiError));
    }
  };

  const message = async () => {
    setActionError(null);
    try {
      const conversation = await startConversation.mutateAsync(userId);
      if (conversation.id) {
        navigation.navigate('ChatConversation', {
          conversationId: conversation.id,
          otherUserId: userId,
          otherUserName: profile?.first_name ?? undefined,
        });
        return;
      }
      // Fall back to starting via the direct endpoint if the helper didn't create one.
      const direct = await chatApi.startConversation(userId);
      navigation.navigate('ChatConversation', {
        conversationId: direct.id,
        otherUserId: userId,
        otherUserName: profile?.first_name ?? undefined,
      });
    } catch (e) {
      const err = e as ApiError;
      if (err.code === 'NOT_MATCHED') {
        setActionError('You can only message users you have matched with.');
      } else {
        setActionError(err.message);
      }
    }
  };

  const submitReport = async () => {
    if (!reportReason) return;
    try {
      await moderationApi.report(userId, reportReason);
      setReported(true);
    } catch (e) {
      setActionError((e as ApiError).message);
    } finally {
      setReportOpen(false);
    }
  };

  const blockUser = async () => {
    try {
      await moderationApi.block(userId);
      setBlocked(true);
    } catch (e) {
      setActionError((e as ApiError).message);
    }
  };

  if (isLoading) {
    return (
      <ScreenContainer>
        <AppHeader title="Profile" showBack />
        <LoadingState message="Loading profile…" />
      </ScreenContainer>
    );
  }
  if (error || !profile) {
    return (
      <ScreenContainer>
        <AppHeader title="Profile" showBack />
        <ErrorState onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const photo = imageUrl(profile.profile_photo);
  const nameLine = [profile.first_name, profile.age ? `${profile.age} yrs` : null].filter(Boolean).join(', ');

  const infoRows: { label: string; value: string }[] = [
    { label: 'Height', value: formatHeight(profile.height_cm) },
    { label: 'Marital Status', value: maritalStatusLabel(profile.marital_status) },
    { label: 'Religion', value: profile.religion ?? '—' },
    { label: 'Caste', value: profile.caste ?? '—' },
    { label: 'Mother Tongue', value: profile.mother_tongue ?? '—' },
    { label: 'Education', value: profile.education ?? '—' },
    { label: 'Occupation', value: profile.occupation ?? '—' },
    { label: 'Location', value: [profile.city, profile.state, profile.country].filter(Boolean).join(', ') || '—' },
    { label: 'Diet', value: titleCase(profile.diet ?? '') },
    { label: 'Smoking', value: titleCase(profile.smoking ?? '') },
    { label: 'Drinking', value: titleCase(profile.drinking ?? '') },
  ];

  return (
    <ScreenContainer scroll>
      <AppHeader
        title="Profile"
        showBack
        right={
          <Pressable onPress={() => setReportOpen(true)} hitSlop={8} accessibilityRole="button" accessibilityLabel="Report">
            <AppIcon name="flag-outline" size={22} color={colors.textSecondary} />
          </Pressable>
        }
      />

      <View style={[styles.headerCard, { backgroundColor: colors.surface, borderRadius: radius.xxl }]}>
        {photo ? (
          <Image source={{ uri: photo }} style={[styles.photo, { backgroundColor: colors.secondary }]} />
        ) : (
          <View style={[styles.photo, { backgroundColor: colors.secondary, alignItems: 'center', justifyContent: 'center' }]}>
            <ProfileAvatar firstName={profile.first_name} size={96} />
          </View>
        )}
        <View style={{ alignItems: 'center', padding: spacing.xl }}>
          <AppText variant="h1" center>
            {nameLine || 'Profile'}
          </AppText>
          <View style={{ flexDirection: 'row', marginTop: spacing.sm, gap: spacing.sm }}>
            {profile.is_verified_photo || profile.is_verified_job ? <VerifiedBadge /> : null}
            {!profile.is_verified_photo && !profile.is_verified_job ? (
              <AppText variant="caption">Profile verification pending</AppText>
            ) : null}
          </View>
          <AppText variant="body" center style={{ marginTop: spacing.sm }}>
            {profile.bio ?? ''}
          </AppText>
        </View>
      </View>

      <View style={{ flexDirection: 'row', marginTop: spacing.lg }}>
        <View style={{ flex: 1, marginRight: spacing.sm }}>
          <AppButton title="Send Interest" onPress={sendInterest} loading={swipeMutation.isPending} size="md" />
        </View>
        <View style={{ flex: 1, marginLeft: spacing.sm }}>
          <AppButton title="Shortlist" variant="outline" size="md" onPress={() => swipeMutation.mutate({ userId, action: 'SUPER_LIKE' })} />
        </View>
      </View>
      <View style={{ marginTop: spacing.md }}>
        <AppButton title={isMatched ? 'Send Message' : 'Message (match required)'} variant="secondary" size="md" onPress={message} />
      </View>

      {actionError ? <ErrorState compact message={actionError} /> : null}

      {isMatched ? (
        <View style={[styles.contactCard, { backgroundColor: colors.surface, borderRadius: radius.lg, marginTop: spacing.lg, padding: spacing.lg }]}>
          <AppText variant="h3">Contact Details</AppText>
          <AppText variant="body" style={{ marginTop: spacing.sm }}>
            📞 {(profile as { phone_number?: string }).phone_number ?? 'Not shared'}
          </AppText>
          <AppText variant="body" style={{ marginTop: spacing.xs }}>
            ✉️ {(profile as { email?: string }).email ?? 'Not shared'}
          </AppText>
        </View>
      ) : null}

      <AppText variant="overline" style={{ marginVertical: 16 }}>
        About {profile.first_name ?? 'this profile'}
      </AppText>
      <View style={{ backgroundColor: colors.surface, borderRadius: radius.xl, padding: spacing.lg }}>
        {infoRows.map((row) => (
          <View key={row.label} style={styles.infoRow}>
            <AppText variant="bodySmall" style={{ flex: 1 }}>{row.label}</AppText>
            <AppText variant="body" style={{ flex: 1.4, textAlign: 'right' }}>{row.value}</AppText>
          </View>
        ))}
      </View>

      <View style={{ flexDirection: 'row', marginTop: spacing.xl, gap: spacing.md }}>
        <View style={{ flex: 1 }}>
          <AppButton title="Block" variant="ghost" size="md" onPress={blockUser} disabled={blocked} />
        </View>
        <View style={{ flex: 1 }}>
          <AppButton title={blocked ? 'Blocked' : 'Report'} variant="ghost" size="md" onPress={() => setReportOpen(true)} disabled={reported} />
        </View>
      </View>
      {reported ? (
        <AppText variant="bodySmall" center style={{ marginTop: spacing.sm }}>
          Thank you — this profile has been reported to our moderation team.
        </AppText>
      ) : null}
      {blocked ? (
        <AppText variant="bodySmall" center style={{ marginTop: spacing.sm }}>
          You have blocked this user.
        </AppText>
      ) : null}

      <BottomSheet visible={reportOpen} onClose={() => setReportOpen(false)} title="Report Profile">
        <AppText variant="bodySmall" style={{ marginBottom: spacing.md }}>
          Help us keep the community safe. Select a reason for reporting this profile.
        </AppText>
        {REPORT_REASONS.map((reason) => (
          <Pressable
            key={reason}
            onPress={() => {
              setReportReason(reason);
              submitReport();
            }}
            style={({ pressed }) => [styles.reasonRow, { opacity: pressed ? 0.7 : 1 }]}
          >
            <AppText variant="body">{reason.replace(/_/g, ' ')}</AppText>
            <AppIcon name="chevron-forward" size={18} color={colors.textSecondary} />
          </Pressable>
        ))}
      </BottomSheet>

      <Modal
        visible={reported}
        onClose={() => setReported(false)}
        title="Report received"
        message="Our moderation team will review this profile shortly."
        actions={[{ label: 'OK', onPress: () => undefined }]}
      />
    </ScreenContainer>
  );
}

function friendlySwipeError(err: ApiError): string {
  if (err.code === 'DUPLICATE_SWIPE') return 'You have already sent interest to this profile.';
  if (err.code === 'ALREADY_MATCHED') return 'You are already matched with this user.';
  if (err.isPremiumGated) return 'Upgrade required to continue. Visit the Premium tab for details.';
  return err.message;
}

const styles = StyleSheet.create({
  headerCard: {
    overflow: 'hidden',
  },
  photo: {
    width: '100%',
    aspectRatio: 16 / 10,
  },
  infoRow: {
    flexDirection: 'row',
    paddingVertical: 10,
  },
  contactCard: {},
  reasonRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 14,
  },
});
