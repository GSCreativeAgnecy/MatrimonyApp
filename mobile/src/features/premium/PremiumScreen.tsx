import React, { useState } from 'react';
import { ScrollView, View } from 'react-native';
import * as WebBrowser from 'expo-web-browser';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppHeader } from '../../components/AppHeader';
import { AppButton } from '../../components/AppButton';
import { SubscriptionCard } from '../../components/SubscriptionCard';
import { PremiumBadge } from '../../components/PremiumBadge';
import { Modal } from '../../components/Modal';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';
import { usePlans, useSubscription, useCheckout, useMyVerifications } from './hooks';
import { useAuth } from '../../auth/AuthContext';
import { ApiError } from '../../types/api';
import { SubscriptionPlan } from '../../types/models';
import { formatPrice } from '../../utils/format';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AppStackParamList } from '../../navigation/types';

export function PremiumScreen() {
  const { colors, radius, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const { refreshUser } = useAuth();
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();

  const { data: plans, isLoading, error, refetch } = usePlans();
  const { data: subscription, refetch: refetchSubscription } = useSubscription();
  const checkout = useCheckout();
  const { data: verifications } = useMyVerifications();

  const [checkoutModal, setCheckoutModal] = useState<{ planName: string; amount: number; currency: string; url: string | null } | null>(null);
  const [errorModal, setErrorModal] = useState<string | null>(null);

  const openCheckout = async (plan: SubscriptionPlan) => {
    try {
      const result = await checkout.mutateAsync(plan.id);
      setCheckoutModal({
        planName: plan.name,
        amount: result.amount,
        currency: result.currency,
        url: result.checkout_url,
      });
      if (result.checkout_url) {
        await WebBrowser.openBrowserAsync(result.checkout_url);
        // Refresh subscription + user after the (mock/provider) checkout.
        refetchSubscription();
        refreshUser();
      }
    } catch (e) {
      setErrorModal((e as ApiError).message);
    }
  };

  if (isLoading) {
    return (
      <ScreenContainer>
        <AppHeader title="Premium" />
        <LoadingState message="Loading membership plans…" />
      </ScreenContainer>
    );
  }
  if (error) {
    return (
      <ScreenContainer>
        <AppHeader title="Premium" />
        <ErrorState onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const plansList = plans ?? [];
  const highlight = plansList.find((p) => /premium/i.test(p.name) && !/plus/i.test(p.name));
  const premiumPlus = plansList.find((p) => /plus/i.test(p.name));
  const basic = plansList.find((p) => /basic/i.test(p.name));
  const free = plansList.find((p) => /free/i.test(p.name));
  const ordered = [free, basic, premiumPlus ?? highlight].filter((p): p is SubscriptionPlan => Boolean(p));

  return (
    <ScreenContainer scroll>
      <AppHeader title="Membership & Premium" />

      {subscription && subscription.is_premium ? (
        <View style={[styles.current, { backgroundColor: colors.secondary, borderRadius: radius.xl, padding: spacing.xl }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <AppIcon name="diamond" size={22} color={colors.accent} />
            <AppText variant="h2" style={{ marginLeft: spacing.sm, flex: 1 }}>
              {subscription.plan_name ?? 'Premium'} member
            </AppText>
            <PremiumBadge size="md" />
          </View>
          <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
            {subscription.expires_at
              ? `Valid until ${new Date(subscription.expires_at).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })}`
              : 'Your membership is active.'}
          </AppText>
        </View>
      ) : (
        <View style={[styles.current, { backgroundColor: colors.surface, borderRadius: radius.xl, padding: spacing.xl }]}>
          <AppText variant="h2">You are on the Free plan</AppText>
          <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
            Upgrade for unlimited swipes, unlimited messages and advanced filters.
          </AppText>
        </View>
      )}

      <AppText variant="overline" style={{ marginTop: spacing.xl, marginBottom: spacing.md }}>
        Choose Your Plan
      </AppText>

      {ordered.map((plan) => (
        <View key={plan.id} style={{ marginBottom: spacing.lg }}>
          <SubscriptionCard
            plan={plan}
            highlighted={Boolean(premiumPlus && plan.id === premiumPlus.id)}
            onSelect={() => openCheckout(plan)}
            ctaLabel={plan.name.toLowerCase().includes('free') ? 'Continue Free' : 'Upgrade Now'}
            loading={checkout.isPending}
          />
        </View>
      ))}

      <AppText variant="overline" style={{ marginTop: spacing.xl, marginBottom: spacing.md }}>
        One-Time Service
      </AppText>

      <View style={{ backgroundColor: colors.surface, borderRadius: radius.xl, padding: spacing.xl }}>
        <View style={{ flexDirection: 'row', alignItems: 'center' }}>
          <AppIcon name="shield-checkmark" size={22} color={colors.verified} />
          <AppText variant="h2" style={{ marginLeft: spacing.sm, flex: 1 }}>
            Job Verification
          </AppText>
        </View>
        <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
          One-time employment background verification that adds the trusted badge to your profile.
        </AppText>
        <View style={{ flexDirection: 'row', marginTop: spacing.lg }}>
          <View style={{ flex: 1, marginRight: spacing.sm }}>
            <AppButton
              title={`Local · ${formatPrice(config.pricing.local_job_verification)}`}
              size="md"
              variant="outline"
              onPress={() => navigation.navigate('JobVerification')}
            />
          </View>
          <View style={{ flex: 1, marginLeft: spacing.sm }}>
            <AppButton
              title={`NRI · ${formatPrice(config.pricing.nri_job_verification)}`}
              size="md"
              variant="outline"
              onPress={() => navigation.navigate('JobVerification')}
            />
          </View>
        </View>
        {verifications && verifications.length > 0 ? (
          <View style={{ marginTop: spacing.lg }}>
            <AppText variant="caption">Your verifications</AppText>
            {verifications.map((v) => (
              <View key={v.id} style={{ flexDirection: 'row', justifyContent: 'space-between', marginTop: spacing.xs }}>
                <AppText variant="bodySmall">{v.employer_name}</AppText>
                <AppText variant="bodySmall" color={v.verification_status === 'VERIFIED' ? colors.verified : colors.textSecondary}>
                  {v.verification_status.replace(/_/g, ' ')}
                </AppText>
              </View>
            ))}
          </View>
        ) : null}
      </View>

      <Modal
        visible={Boolean(checkoutModal)}
        onClose={() => setCheckoutModal(null)}
        title={checkoutModal?.planName ?? 'Checkout'}
        message={
          checkoutModal?.url
            ? `You are being redirected to complete payment of ${formatPrice(checkoutModal.amount, checkoutModal.currency)}.`
            : `Payment of ${formatPrice(checkoutModal?.amount ?? 0, checkoutModal?.currency)} is being processed. Your plan will activate automatically once confirmed.`
        }
        actions={[{ label: 'OK', onPress: () => undefined }]}
      />

      <Modal
        visible={Boolean(errorModal)}
        onClose={() => setErrorModal(null)}
        title="Payment unavailable"
        message={errorModal ?? undefined}
        actions={[{ label: 'OK', onPress: () => undefined }]}
      />
    </ScreenContainer>
  );
}

const styles = {
  current: {
    marginTop: 8,
  },
};
