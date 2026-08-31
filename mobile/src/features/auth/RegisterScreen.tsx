import React, { useMemo, useState } from 'react';
import { View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppInput } from '../../components/AppInput';
import { AppButton } from '../../components/AppButton';
import { ScreenContainer } from '../../components/ScreenContainer';
import { ErrorState } from '../../components/ErrorState';
import { PasswordStrengthIndicator } from '../../components/PasswordStrengthIndicator';
import { authApi } from '../../api/auth';
import { useAuth } from '../../auth/AuthContext';
import { ApiError } from '../../types/api';
import { isEmailValid, isBackendValidPassword, passwordStrength } from '../../utils/validators';
import { AuthStackParamList } from '../../navigation/types';
import { useTheme } from '../../theme/ThemeProvider';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';

type FieldName = 'firstName' | 'lastName' | 'email' | 'password' | 'confirm';

interface Errors {
  firstName?: string;
  lastName?: string;
  email?: string;
  password?: string;
  confirm?: string;
}

export function RegisterScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AuthStackParamList>>();
  const { signIn } = useAuth();
  const { colors } = useTheme();
  const { config } = useRemoteConfig();

  const [form, setForm] = useState({
    firstName: '',
    lastName: '',
    email: '',
    password: '',
    confirm: '',
  });
  const [errors, setErrors] = useState<Errors>({});
  const [loading, setLoading] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const strength = useMemo(() => passwordStrength(form.password), [form.password]);

  const setField = (field: FieldName) => (value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => ({ ...prev, [field]: undefined }));
    setSubmitError(null);
  };

  const validate = (): boolean => {
    const next: Errors = {};
    if (!form.firstName.trim()) next.firstName = 'Please enter your first name';
    if (!form.email.trim()) {
      next.email = 'Please enter your email address';
    } else if (!isEmailValid(form.email)) {
      next.email = 'Please enter a valid email address';
    }
    if (!isBackendValidPassword(form.password)) {
      next.password = 'At least 8 characters with one uppercase letter and one digit';
    }
    if (form.confirm !== form.password) {
      next.confirm = 'Passwords do not match';
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submit = async () => {
    if (!validate() || loading) {
      return;
    }
    setLoading(true);
    setSubmitError(null);
    try {
      // Backend contract: register accepts email (and optional phone) + password.
      // First/last name are stored on the profile during onboarding.
      const tokens = await authApi.register({ email: form.email.trim(), password: form.password });
      await signIn(tokens);
      setSuccess(true);
    } catch (e) {
      const err = e as ApiError;
      setSubmitError(
        err.code === 'CONFLICT' || /already/i.test(err.message)
          ? 'An account with this email already exists.'
          : err.message,
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScreenContainer scroll keyboardAvoiding>
      <AppText variant="display" style={{ marginTop: 16 }}>
        Create your profile
      </AppText>
      <AppText variant="body" style={{ marginTop: 8, marginBottom: 24 }}>
        Join {config.branding.app_name} and start discovering compatible matches.
      </AppText>

      <View style={{ flexDirection: 'row', gap: 12 }}>
        <View style={{ flex: 1 }}>
          <AppInput
            label="First Name"
            value={form.firstName}
            onChangeText={setField('firstName')}
            placeholder="First name"
            autoCapitalize="words"
            error={errors.firstName}
            leftIcon="person-outline"
          />
        </View>
        <View style={{ flex: 1 }}>
          <AppInput
            label="Last Name"
            value={form.lastName}
            onChangeText={setField('lastName')}
            placeholder="Last name"
            autoCapitalize="words"
            error={errors.lastName}
          />
        </View>
      </View>

      <AppInput
        label="Email"
        value={form.email}
        onChangeText={setField('email')}
        placeholder="you@example.com"
        keyboardType="email-address"
        autoCapitalize="none"
        autoComplete="email"
        error={errors.email}
        leftIcon="mail-outline"
      />

      <AppInput
        label="Password"
        value={form.password}
        onChangeText={setField('password')}
        placeholder="Minimum 8 characters"
        secureTextEntry
        secureToggle
        error={errors.password}
        leftIcon="lock-closed-outline"
      />
      {form.password.length > 0 ? <PasswordStrengthIndicator strength={strength} /> : null}

      <AppInput
        label="Confirm Password"
        value={form.confirm}
        onChangeText={setField('confirm')}
        placeholder="Re-enter your password"
        secureTextEntry
        secureToggle
        error={errors.confirm}
        leftIcon="lock-closed-outline"
      />

      {submitError ? <ErrorState compact message={submitError} /> : null}
      {success ? (
        <AppText variant="body" color={colors.success} style={{ textAlign: 'center', marginBottom: 12 }}>
          Your account is ready!
        </AppText>
      ) : null}

      <AppButton
        title="Confirm & Register for Free"
        onPress={submit}
        loading={loading}
        disabled={loading}
      />

      <AppText variant="caption" center style={{ marginTop: 16 }}>
        By registering you agree to our Terms & Privacy Policy.
      </AppText>

      <View style={{ alignItems: 'center', marginTop: 24 }}>
        <AppText variant="body">
          Already have an account?{' '}
          <AppText variant="label" color={colors.primary} onPress={() => navigation.navigate('Login')}>
            Log In
          </AppText>
        </AppText>
      </View>
    </ScreenContainer>
  );
}
