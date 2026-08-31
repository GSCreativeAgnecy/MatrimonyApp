import React, { useState } from 'react';
import { View } from 'react-native';
import * as WebBrowser from 'expo-web-browser';

import { AppText } from '../../components/AppText';
import { AppInput } from '../../components/AppInput';
import { AppButton } from '../../components/AppButton';
import { AppHeader } from '../../components/AppHeader';
import { BottomSheet } from '../../components/BottomSheet';
import { Modal } from '../../components/Modal';
import { ScreenContainer } from '../../components/ScreenContainer';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';
import { verificationApi } from '../../api/subscriptions';
import { ApiError } from '../../types/api';
import { formatPrice } from '../../utils/format';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../../query/keys';

export function JobVerificationScreen() {
  const { colors, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const queryClient = useQueryClient();

  const [employmentType, setEmploymentType] = useState<'LOCAL' | 'NRI'>('LOCAL');
  const [employerName, setEmployerName] = useState('');
  const [jobTitle, setJobTitle] = useState('');
  const [country, setCountry] = useState('');
  const [typeSheet, setTypeSheet] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [checkoutModal, setCheckoutModal] = useState<{ amount: number; currency: string; url: string | null } | null>(null);

  const price = employmentType === 'LOCAL' ? config.pricing.local_job_verification : config.pricing.nri_job_verification;

  const submit = async () => {
    if (!employerName.trim()) {
      setError('Please enter your employer name.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const result = await verificationApi.submitJob({
        employment_type: employmentType,
        employer_name: employerName.trim(),
        job_title: jobTitle.trim() || undefined,
        country: country.trim() || undefined,
      });
      setCheckoutModal({ amount: result.amount, currency: result.currency, url: result.checkout_url });
      if (result.checkout_url) {
        await WebBrowser.openBrowserAsync(result.checkout_url);
      }
      queryClient.invalidateQueries({ queryKey: queryKeys.verification.mine });
    } catch (e) {
      setError((e as ApiError).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenContainer scroll keyboardAvoiding>
      <AppHeader title="Job Verification" showBack />

      <View style={{ backgroundColor: colors.surface, borderRadius: 16, padding: spacing.xl }}>
        <AppText variant="h2">Employment background verification</AppText>
        <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
          Verify your employment to unlock the verified badge on your profile. One-time service.
        </AppText>

        <View style={{ marginTop: spacing.lg }}>
          <AppText variant="label">Verification Type</AppText>
          <View style={{ flexDirection: 'row', marginTop: spacing.sm, gap: spacing.sm }}>
            {(['LOCAL', 'NRI'] as const).map((type) => {
              const active = employmentType === type;
              return (
                <View key={type} style={{ flex: 1 }}>
                  <AppButton
                    title={type === 'LOCAL' ? 'Local' : 'NRI'}
                    size="md"
                    variant={active ? 'primary' : 'outline'}
                    onPress={() => setEmploymentType(type)}
                  />
                </View>
              );
            })}
          </View>
        </View>

        <View style={{ marginTop: spacing.lg }}>
          <AppInput label="Employer Name" value={employerName} onChangeText={setEmployerName} placeholder="Current employer" />
          <AppInput label="Job Title (optional)" value={jobTitle} onChangeText={setJobTitle} placeholder="e.g. Senior Engineer" />
          <AppInput label="Country (optional)" value={country} onChangeText={setCountry} placeholder="e.g. India" />
        </View>

        <AppText variant="h2" color={colors.primary}>
          {formatPrice(price)} · one-time
        </AppText>

        {error ? <ErrorState compact message={error} /> : null}

        <View style={{ marginTop: spacing.lg }}>
          <AppButton title="Proceed to Payment" onPress={submit} loading={loading} />
        </View>
      </View>

      <BottomSheet visible={typeSheet} onClose={() => setTypeSheet(false)} title="Verification Type">
        <AppText variant="body">Local verification is for employment in India. NRI is for employment abroad.</AppText>
      </BottomSheet>

      <Modal
        visible={Boolean(checkoutModal)}
        onClose={() => setCheckoutModal(null)}
        title="Payment initiated"
        message={
          checkoutModal?.url
            ? 'You are being redirected to complete the payment.'
            : `Payment of ${formatPrice(checkoutModal?.amount ?? 0, checkoutModal?.currency)} is being processed. Your verification request will be reviewed once confirmed.`
        }
        actions={[{ label: 'OK', onPress: () => undefined }]}
      />
    </ScreenContainer>
  );
}
