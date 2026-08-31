import React, { useState } from 'react';
import { View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppInput } from '../../components/AppInput';
import { AppButton } from '../../components/AppButton';
import { ScreenContainer } from '../../components/ScreenContainer';
import { ErrorState } from '../../components/ErrorState';
import { authApi } from '../../api/auth';
import { ApiError } from '../../types/api';
import { AuthStackParamList } from '../../navigation/types';
import { useTheme } from '../../theme/ThemeProvider';

export function ForgotPasswordScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AuthStackParamList>>();
  const { colors } = useTheme();

  const [identifier, setIdentifier] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);

  const submit = async () => {
    if (identifier.trim().length < 4) {
      setError('Please enter your email address.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await authApi.forgotPassword(identifier.includes('@') ? identifier.trim() : undefined, identifier.includes('@') ? undefined : identifier.trim());
      setSent(true);
    } catch (e) {
      setError((e as ApiError).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenContainer scroll keyboardAvoiding>
      <AppText variant="display" style={{ marginTop: 24 }}>
        Forgot password
      </AppText>
      <AppText variant="body" style={{ marginTop: 8, marginBottom: 24 }}>
        Enter your email address and we will send you a link to reset your password.
      </AppText>

      <AppInput
        label="Email"
        value={identifier}
        onChangeText={(v) => {
          setIdentifier(v);
          setError(null);
        }}
        placeholder="you@example.com"
        keyboardType="email-address"
        autoCapitalize="none"
        leftIcon="mail-outline"
      />

      {error ? <ErrorState compact message={error} /> : null}

      {sent ? (
        <AppText variant="body" color={colors.success} center style={{ marginVertical: 16 }}>
          If the account exists, a password reset link has been sent to your email.
        </AppText>
      ) : null}

      <AppButton title="Send Reset Link" onPress={submit} loading={loading} />

      <View style={{ alignItems: 'center', marginTop: 24 }}>
        <AppText
          variant="label"
          color={colors.primary}
          onPress={() => navigation.navigate('Login')}
          accessibilityRole="link"
        >
          Back to Log In
        </AppText>
      </View>
    </ScreenContainer>
  );
}
