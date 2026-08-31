import React from 'react';
import { Linking, View } from 'react-native';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppHeader } from '../../components/AppHeader';
import { AppButton } from '../../components/AppButton';
import { ScreenContainer } from '../../components/ScreenContainer';
import { useTheme } from '../../theme/ThemeProvider';
import { useAuth } from '../../auth/AuthContext';

export function ReferralScreen() {
  const { colors, radius, spacing } = useTheme();
  const { user } = useAuth();

  const shareText = `Join me on ${''} and find your perfect match! Use my referral to get started.`;

  const share = () => {
    const message = `${shareText}\n${user?.email ?? ''}`;
    Linking.openURL(`sms:?&body=${encodeURIComponent(message)}`).catch(() => undefined);
  };

  return (
    <ScreenContainer scroll>
      <AppHeader title="Referral" showBack />

      <View style={{ alignItems: 'center', marginTop: 24 }}>
        <View style={{ width: 80, height: 80, borderRadius: 40, backgroundColor: colors.secondary, alignItems: 'center', justifyContent: 'center' }}>
          <AppIcon name="gift" size={36} color={colors.primary} />
        </View>
        <AppText variant="h1" center style={{ marginTop: spacing.lg }}>
          Refer & Earn
        </AppText>
        <AppText variant="body" center style={{ marginTop: spacing.sm, maxWidth: 300 }}>
          Invite your friends to find their perfect match. Referral rewards are being rolled out.
        </AppText>
      </View>

      <View style={{ backgroundColor: colors.surface, borderRadius: radius.xl, padding: spacing.xl, marginTop: spacing.xl }}>
        <AppText variant="label">Referral code</AppText>
        <AppText variant="display" color={colors.primary} style={{ marginVertical: spacing.md }}>
          {user?.id?.slice(0, 8).toUpperCase() ?? 'COMING SOON'}
        </AppText>
        <AppText variant="caption">
          Referral codes and reward rules will be activated once the backend referral program is available.
        </AppText>
        <View style={{ marginTop: spacing.xl }}>
          <AppButton title="Invite via SMS" onPress={share} />
        </View>
      </View>
    </ScreenContainer>
  );
}
