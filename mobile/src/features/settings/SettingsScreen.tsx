import React, { useState } from 'react';
import { Pressable, StyleSheet, Switch, View } from 'react-native';
import { useMutation } from '@tanstack/react-query';
import { apiRequest } from '../../api/client';

import { AppText } from '../../components/AppText';
import { AppIcon, IconName } from '../../components/AppIcon';
import { AppHeader } from '../../components/AppHeader';
import { AppButton } from '../../components/AppButton';
import { AppInput } from '../../components/AppInput';
import { Modal } from '../../components/Modal';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { useOwnProfile } from '../profile/hooks';
import { useAuth } from '../../auth/AuthContext';
import { profileApi } from '../../api/profile';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { AppStackParamList } from '../../navigation/types';

export function SettingsScreen() {
  const { colors, radius, spacing } = useTheme();
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { user, signOut } = useAuth();

  const { data: profile, isLoading, error, refetch } = useOwnProfile();
  const [passwordOpen, setPasswordOpen] = useState(false);

  const changePassword = useMutation({
    mutationFn: ({ old_password, new_password }: { old_password: string; new_password: string }) =>
      apiRequest('/auth/change-password', { method: 'POST', body: { old_password, new_password } }),
  });

  const privacy = profile?.privacy;

  const updatePrivacy = async (key: keyof NonNullable<typeof privacy>, value: boolean | string) => {
    try {
      await profileApi.updatePrivacy({ [key]: value } as never);
      refetch();
    } catch {
      // Non-fatal UI error; backend remains authoritative.
    }
  };

  if (isLoading) {
    return <ScreenContainer><LoadingState /></ScreenContainer>;
  }
  if (error) {
    return (
      <ScreenContainer>
        <AppHeader title="Settings" showBack />
        <ErrorState onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scroll>
      <AppHeader title="Settings" showBack />

      <AppText variant="overline" style={{ marginBottom: 12 }}>Privacy</AppText>
      <View style={styles.group}>
        <ToggleRow
          label="Show online status"
          value={privacy?.show_online_status ?? false}
          onChange={(v) => updatePrivacy('show_online_status', v)}
        />
        <ToggleRow
          label="Show distance"
          value={privacy?.show_distance ?? false}
          onChange={(v) => updatePrivacy('show_distance', v)}
        />
        <ToggleRow
          label="Show last seen"
          value={privacy?.show_last_seen ?? false}
          onChange={(v) => updatePrivacy('show_last_seen', v)}
        />
        <ToggleRow
          label="Allow match requests"
          value={privacy?.allow_match_requests ?? false}
          onChange={(v) => updatePrivacy('allow_match_requests', v)}
        />
      </View>

      <AppText variant="overline" style={{ marginTop: 24, marginBottom: 12 }}>Account</AppText>
      <View style={styles.group}>
        <RowItem icon="key-outline" label="Change Password" onPress={() => setPasswordOpen(true)} />
        <RowItem icon="person-outline" label="Profile" onPress={() => navigation.navigate('EditProfile')} />
        <RowItem icon="images-outline" label="Manage Photos" onPress={() => navigation.navigate('Photos')} />
        <RowItem icon="help-buoy-outline" label="Help & Support" onPress={() => navigation.navigate('HelpSupport')} />
        <RowItem icon="log-out-outline" label="Logout" danger onPress={() => signOut()} />
      </View>

      <AppText variant="caption" center style={{ marginTop: 24 }}>
        {user?.email ?? ''} · Member since {user?.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
      </AppText>

      <Modal
        visible={passwordOpen}
        onClose={() => setPasswordOpen(false)}
        title="Change Password"
      >
        <ChangePasswordForm
          loading={changePassword.isPending}
          error={changePassword.error ? 'Could not change password. Please check your current password.' : undefined}
          onSubmit={(old_password, new_password) => changePassword.mutate({ old_password, new_password })}
        />
      </Modal>
    </ScreenContainer>
  );
}

function ChangePasswordForm({
  onSubmit,
  loading,
  error,
}: {
  onSubmit: (old_password: string, new_password: string) => void;
  loading: boolean;
  error?: string;
}) {
  const { spacing } = useTheme();
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirm, setConfirm] = useState('');

  const valid = oldPassword.length >= 6 && newPassword.length >= 8 && newPassword === confirm;

  return (
    <View>
      <AppInput label="Current password" value={oldPassword} onChangeText={setOldPassword} secureTextEntry />
      <AppInput label="New password" value={newPassword} onChangeText={setNewPassword} secureTextEntry helper="At least 8 characters with one uppercase letter and one digit." />
      <AppInput label="Confirm new password" value={confirm} onChangeText={setConfirm} secureTextEntry />
      {error ? <AppText variant="bodySmall" color="#C62828" style={{ marginBottom: spacing.sm }}>{error}</AppText> : null}
      <AppButton title="Update Password" onPress={() => onSubmit(oldPassword, newPassword)} disabled={!valid} loading={loading} size="md" />
    </View>
  );
}

function ToggleRow({ label, value, onChange }: { label: string; value: boolean; onChange: (v: boolean) => void }) {
  const { colors, spacing } = useTheme();
  return (
    <View style={styles.toggleRow}>
      <AppText variant="body" style={{ flex: 1 }}>{label}</AppText>
      <Switch value={value} onValueChange={onChange} trackColor={{ true: colors.primary, false: colors.border }} thumbColor={colors.surface} />
    </View>
  );
}

function RowItem({ icon, label, onPress, danger = false }: { icon: IconName; label: string; onPress: () => void; danger?: boolean }) {
  const { colors, spacing } = useTheme();
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={({ pressed }) => [styles.toggleRow, { opacity: pressed ? 0.7 : 1 }]}>
      <AppIcon name={icon} size={20} color={danger ? colors.error : colors.primary} />
      <AppText variant="body" color={danger ? colors.error : colors.text} style={{ marginLeft: spacing.md, flex: 1 }}>
        {label}
      </AppText>
      <AppIcon name="chevron-forward" size={18} color={colors.textSecondary} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  group: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    overflow: 'hidden',
  },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 16,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: '#EADFCE',
  },
});
