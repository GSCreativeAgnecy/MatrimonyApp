import React from 'react';
import { Image, Pressable, StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { AppIcon, IconName } from './AppIcon';
import { useTheme } from '../theme/ThemeProvider';
import { PublicProfile } from '../types/models';
import { formatHeight } from '../utils/format';
import { imageUrl } from '../utils/imageUrl';

const REASON_LABELS: Record<string, string> = {
  AGE_MATCH: 'Age match',
  HEIGHT_MATCH: 'Height match',
  LOCATION_MATCH: 'Nearby',
  RELIGION_MATCH: 'Same religion',
  CASTE_MATCH: 'Same community',
  LANGUAGE_MATCH: 'Same language',
  EDUCATION_MATCH: 'Educated',
  OCCUPATION_MATCH: 'Good profession',
  DIET_MATCH: 'Same diet',
  SMOKING_MATCH: 'Same habits',
  DRINKING_MATCH: 'Same habits',
  FAMILY_VALUES_MATCH: 'Similar family values',
  SHARED_INTERESTS: 'Shared interests',
  MARITAL_STATUS_MATCH: 'Same marital status',
  INTENT_MATCH: 'Same intent',
};

interface ProfileCardProps {
  profile: PublicProfile;
  reasonCodes?: string[];
  onSendInterest?: () => void;
  onShortlist?: () => void;
  onMessage?: () => void;
  onPress?: () => void;
  actionPending?: boolean;
}

/** Two-column discovery grid card. */
export function ProfileCard({
  profile,
  reasonCodes = [],
  onSendInterest,
  onShortlist,
  onMessage,
  onPress,
  actionPending = false,
}: ProfileCardProps) {
  const { colors, radius, spacing } = useTheme();
  const photo = imageUrl(profile.profile_photo);
  const traits = reasonCodes
    .map((code) => REASON_LABELS[code])
    .filter(Boolean)
    .slice(0, 2);

  const ageText = profile.age ? String(profile.age) : '';
  const heightText = profile.height_cm ? formatHeight(profile.height_cm) : '';
  const nameLine = [profile.first_name, ageText, profile.age ? 'yrs' : null].filter(Boolean).join(', ');
  const location = [profile.city, profile.state].filter(Boolean).join(', ');

  return (
    <Pressable
      onPress={onPress}
      accessibilityRole="button"
      style={({ pressed }) => [
        styles.card,
        {
          backgroundColor: colors.surface,
          borderRadius: radius.xl,
          opacity: pressed ? 0.94 : 1,
        },
      ]}
    >
      {photo ? (
        <Image
          source={{ uri: photo }}
          style={[styles.photo, { borderTopLeftRadius: radius.xl, borderTopRightRadius: radius.xl, backgroundColor: colors.secondary }]}
          accessibilityLabel={`${profile.first_name ?? 'Profile'} photo`}
        />
      ) : (
        <View
          style={[
            styles.photoFallback,
            { borderTopLeftRadius: radius.xl, borderTopRightRadius: radius.xl, backgroundColor: colors.secondary },
          ]}
        >
          <AppIcon name="person" size={40} color={colors.primary} />
        </View>
      )}

      <View style={{ padding: spacing.md }}>
        <AppText variant="h3" numberOfLines={1}>
          {nameLine || 'New profile'}
        </AppText>
        {heightText ? (
          <AppText variant="bodySmall" numberOfLines={1}>
            {heightText}
          </AppText>
        ) : null}
        <AppText variant="bodySmall" numberOfLines={1}>
          {[location, profile.occupation].filter(Boolean).join(' · ') || '—'}
        </AppText>

        {traits.length > 0 ? (
          <View style={styles.traits}>
            {traits.map((trait) => (
              <View key={trait} style={[styles.traitChip, { backgroundColor: colors.secondary, borderRadius: radius.pill }]}>
                <AppText variant="caption" color={colors.primary} style={{ fontSize: 10, lineHeight: 13 }}>
                  {trait}
                </AppText>
              </View>
            ))}
          </View>
        ) : null}

        <View style={styles.actions}>
          <ActionButton icon="heart" label="Interest" color={colors.primary} onPress={onSendInterest} pending={actionPending} />
          <ActionButton icon="star" label="Save" color={colors.accent} onPress={onShortlist} />
          <ActionButton icon="chatbubble" label="Msg" color={colors.textSecondary} onPress={onMessage} />
        </View>
      </View>
    </Pressable>
  );
}

function ActionButton({
  icon,
  label,
  color,
  onPress,
  pending = false,
}: {
  icon: IconName;
  label: string;
  color: string;
  onPress?: () => void;
  pending?: boolean;
}) {
  const { colors, spacing } = useTheme();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={label}
      onPress={onPress}
      style={({ pressed }) => ({
        alignItems: 'center',
        opacity: pressed ? 0.6 : 1,
      })}
    >
      <AppIcon name={pending ? 'hourglass-outline' : icon} size={18} color={pending ? colors.textSecondary : color} />
      <AppText variant="caption" style={{ marginTop: 2, fontSize: 10, lineHeight: 13 }}>
        {label}
      </AppText>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    overflow: 'hidden',
  },
  photo: {
    width: '100%',
    aspectRatio: 3 / 3.4,
  },
  photoFallback: {
    width: '100%',
    aspectRatio: 3 / 3.4,
    alignItems: 'center',
    justifyContent: 'center',
  },
  traits: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 8,
    gap: 6,
  },
  traitChip: {
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  actions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 12,
  },
});
