import React, { useMemo } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppButton } from '../../components/AppButton';
import { ProfileAvatar } from '../../components/ProfileAvatar';
import { VerifiedBadge } from '../../components/VerifiedBadge';
import { PremiumBadge } from '../../components/PremiumBadge';
import { CollapsibleSection } from '../../components/CollapsibleSection';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { useOwnProfile, usePreferences } from './hooks';
import { useMatches } from '../matches/hooks';
import { useSubscription } from '../premium/hooks';
import { AppStackParamList } from '../../navigation/types';
import { formatHeight, formatIncome, fullName, maritalStatusLabel, profileCompleteness, titleCase } from '../../utils/format';

export function ProfileScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, spacing } = useTheme();

  const { data: profile, isLoading, error, refetch } = useOwnProfile();
  const { data: matches } = useMatches();
  const { data: preferences } = usePreferences();
  const { data: subscription } = useSubscription();

  const completeness = useMemo(
    () => profileCompleteness(profile as unknown as Record<string, unknown>),
    [profile],
  );
  const matchesFound = matches?.length ?? 0;
  const isPremium = subscription?.is_premium === true;

  if (isLoading) {
    return <ScreenContainer><LoadingState message="Loading your profile…" /></ScreenContainer>;
  }
  if (error) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const detailRows: { label: string; value: string }[] = [
    { label: 'Name', value: fullName(profile?.first_name, profile?.last_name) },
    { label: 'Height', value: formatHeight(profile?.height_cm) },
    { label: 'Caste', value: profile?.caste ?? '—' },
    { label: 'Religion', value: profile?.religion ?? '—' },
    { label: 'Occupation', value: profile?.occupation ?? '—' },
    { label: 'Salary Details', value: formatIncome(profile?.annual_income, profile?.income_currency) },
    { label: 'Smoking', value: titleCase(profile?.smoking ?? '') },
    { label: 'Drinking', value: titleCase(profile?.drinking ?? '') },
    { label: 'Body Type', value: titleCase(profile?.body_type ?? '') },
    { label: 'Colour', value: titleCase(profile?.complexion ?? '') },
    { label: 'Marital Status', value: maritalStatusLabel(profile?.marital_status) },
    { label: 'City', value: profile?.city ?? '—' },
    { label: 'State', value: profile?.state ?? '—' },
    { label: 'Country', value: profile?.country ?? '—' },
  ];

  const prefSummary = preferences
    ? [
        preferences.age_min && preferences.age_max
          ? `${preferences.age_min}–${preferences.age_max} yrs`
          : null,
        preferences.preferred_religions.length
          ? preferences.preferred_religions.map((r) => r.value).join(', ')
          : null,
        preferences.preferred_castes.length
          ? preferences.preferred_castes.map((c) => c.value).join(', ')
          : null,
      ]
        .filter(Boolean)
        .join(' · ')
    : null;

  return (
    <ScreenContainer scroll>
      <View style={[styles.headerCard, { backgroundColor: colors.surface, borderRadius: 20, padding: spacing.xl }]}>
        <View style={{ alignItems: 'center' }}>
          <ProfileAvatar uri={profile?.profile_photo} firstName={profile?.first_name} lastName={profile?.last_name} size={96} />
          <View style={{ flexDirection: 'row', alignItems: 'center', marginTop: spacing.md }}>
            <AppText variant="h2">{fullName(profile?.first_name, profile?.last_name)}</AppText>
            <View style={{ marginLeft: spacing.sm }}>
              <VerifiedBadge compact />
            </View>
          </View>
          {isPremium ? (
            <View style={{ marginTop: spacing.sm }}>
              <PremiumBadge size="md" />
            </View>
          ) : null}
          <AppText variant="caption" style={{ marginTop: spacing.xs }}>
            Profile completeness {completeness}%
          </AppText>
        </View>

        <View style={styles.buttonRow}>
          <View style={{ flex: 1, marginRight: spacing.sm }}>
            <AppButton title="Edit Profile" size="md" onPress={() => navigation.navigate('EditProfile')} />
          </View>
          <View style={{ flex: 1, marginLeft: spacing.sm }}>
            <AppButton
              title="Manage Photos"
              size="md"
              variant="outline"
              onPress={() => navigation.navigate('Photos')}
            />
          </View>
        </View>

        <View style={[styles.statsRow, { borderTopColor: colors.border }]}>
          <Stat label="Interests Sent" value="—" />
          <Stat label="Matches Found" value={String(matchesFound)} />
          <Stat label="Profile Views" value="—" />
        </View>
      </View>

      <CollapsibleSection title="My Details" defaultOpen={false}>
        {detailRows.map((row) => (
          <DetailRow key={row.label} label={row.label} value={row.value} />
        ))}
      </CollapsibleSection>

      <CollapsibleSection
        title="Partner Preferences"
        defaultOpen={false}
        trailing={
          <Pressable onPress={() => navigation.navigate('MatchFilters')} hitSlop={8} accessibilityRole="button">
            <AppIcon name="create-outline" size={18} color={colors.primary} />
          </Pressable>
        }
      >
        {prefSummary ? (
          <AppText variant="body">{prefSummary}</AppText>
        ) : (
          <AppText variant="bodySmall">No partner preferences set yet.</AppText>
        )}
        <View style={{ marginTop: spacing.md }}>
          <AppButton
            title="Configure Partner Preferences"
            size="md"
            variant="outline"
            onPress={() => navigation.navigate('MatchFilters')}
          />
        </View>
      </CollapsibleSection>

      <CollapsibleSection title="Account Settings" defaultOpen={false}>
        <AppText variant="bodySmall">
          Manage privacy, notifications, family details and more.
        </AppText>
        <View style={{ marginTop: spacing.md }}>
          <AppButton title="Open Settings" size="md" variant="outline" onPress={() => navigation.navigate('Settings')} />
        </View>
      </CollapsibleSection>
    </ScreenContainer>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  const { colors, spacing } = useTheme();
  return (
    <View style={{ alignItems: 'center', flex: 1 }}>
      <AppText variant="h2" color={colors.primary}>{value}</AppText>
      <AppText variant="caption" style={{ marginTop: 2, textAlign: 'center' }}>{label}</AppText>
    </View>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  const { colors, spacing } = useTheme();
  return (
    <View style={styles.detailRow}>
      <AppText variant="bodySmall" style={{ flex: 1 }}>{label}</AppText>
      <AppText variant="body" style={{ flex: 1.4, textAlign: 'right' }}>{value}</AppText>
    </View>
  );
}

const styles = StyleSheet.create({
  headerCard: {
    marginBottom: 16,
  },
  buttonRow: {
    flexDirection: 'row',
    marginTop: 20,
  },
  statsRow: {
    flexDirection: 'row',
    marginTop: 24,
    paddingTop: 16,
    borderTopWidth: StyleSheet.hairlineWidth,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 10,
  },
});
