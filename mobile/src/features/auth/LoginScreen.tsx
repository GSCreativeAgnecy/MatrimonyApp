import React, { useState } from 'react';
import { Alert, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppInput } from '../../components/AppInput';
import { AppButton } from '../../components/AppButton';
import { ScreenContainer } from '../../components/ScreenContainer';
import { ErrorState } from '../../components/ErrorState';
import { authApi, MfaRequired } from '../../api/auth';
import { useAuth } from '../../auth/AuthContext';
import { ApiError } from '../../types/api';
import { AuthTokens } from '../../types/models';
import { AuthStackParamList } from '../../navigation/types';
import { useTheme } from '../../theme/ThemeProvider';

export function LoginScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AuthStackParamList>>();
  const { signIn } = useAuth();
  const { colors } = useTheme();

  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mfaRequired, setMfaRequired] = useState<MfaRequired | null>(null);
  const [mfaCode, setMfaCode] = useState('');

  const canSubmit = identifier.trim().length > 0 && password.length > 0 && !loading;

  const submit = async () => {
    setError(null);
    setLoading(true);
    try {
      const result = await authApi.login({
        email: identifier.includes('@') ? identifier.trim() : undefined,
        phone_number: identifier.includes('@') ? undefined : identifier.trim(),
        password,
      });
      if ((result as MfaRequired).requires_2fa) {
        setMfaRequired(result as MfaRequired);
        return;
      }
      await signIn(result as AuthTokens);
    } catch (e) {
      const err = e as ApiError;
      setError(err.code === 'RATE_LIMIT_EXCEEDED' ? 'Too many attempts. Please try again shortly.' : err.message);
    } finally {
      setLoading(false);
    }
  };

  const submitMfa = async () => {
    if (!mfaRequired || mfaCode.trim().length < 4) {
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const tokens = await authApi.totpVerify(mfaRequired.mfa_token, mfaCode.trim());
      await signIn(tokens);
    } catch (e) {
      setError((e as ApiError).message);
    } finally {
      setLoading(false);
    }
  };

  if (mfaRequired) {
    return (
      <ScreenContainer scroll keyboardAvoiding>
        <AppText variant="h1" style={{ marginTop: 24 }}>
          Two-Factor Authentication
        </AppText>
        <AppText variant="body" style={{ marginTop: 8 }}>
          Enter the 6-digit code from your authenticator app.
        </AppText>
        <View style={{ marginTop: 24 }}>
          <AppInput
            label="Verification code"
            keyboardType="number-pad"
            maxLength={6}
            value={mfaCode}
            onChangeText={setMfaCode}
            placeholder="000000"
          />
          {error ? <ErrorState compact message={error} /> : null}
          <AppButton title="Verify & Continue" onPress={submitMfa} loading={loading} />
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scroll keyboardAvoiding>
      <AppText variant="display" style={{ marginTop: 24 }}>
        Welcome back
      </AppText>
      <AppText variant="body" style={{ marginTop: 8, marginBottom: 24 }}>
        Log in to continue your journey
      </AppText>

      <AppInput
        label="Email or Phone"
        value={identifier}
        onChangeText={setIdentifier}
        placeholder="you@example.com"
        autoCapitalize="none"
        keyboardType="email-address"
        leftIcon="mail-outline"
      />
      <AppInput
        label="Password"
        value={password}
        onChangeText={setPassword}
        secureTextEntry
        secureToggle
        placeholder="Your password"
        leftIcon="lock-closed-outline"
        onSubmitEditing={submit}
      />

      {error ? <ErrorState compact message={error} /> : null}

      <AppButton title="Log In" onPress={submit} loading={loading} disabled={!canSubmit} />

      <View style={{ alignItems: 'center', marginTop: 20 }}>
        <AppText
          variant="label"
          color={colors.primary}
          onPress={() => navigation.navigate('ForgotPassword')}
          accessibilityRole="link"
        >
          Forgot password?
        </AppText>
      </View>

      <View style={{ alignItems: 'center', marginTop: 32 }}>
        <AppText variant="body">
          New to the app?{' '}
          <AppText variant="label" color={colors.primary} onPress={() => navigation.navigate('Register')}>
            Create a profile
          </AppText>
        </AppText>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
