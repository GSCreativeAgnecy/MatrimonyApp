import React from 'react';
import { StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { LinearGradient } from 'expo-linear-gradient';

import { AppText } from '../../components/AppText';
import { AppButton } from '../../components/AppButton';
import { AppIcon } from '../../components/AppIcon';
import { useTheme } from '../../theme/ThemeProvider';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';
import { AuthStackParamList } from '../../navigation/types';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export function WelcomeScreen() {
  const { colors, radius, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const insets = useSafeAreaInsets();
  const navigation = useNavigation<NativeStackNavigationProp<AuthStackParamList>>();

  return (
    <LinearGradient colors={[colors.primary, colors.primaryDark]} style={styles.container}>
      <View style={[styles.content, { paddingTop: insets.top + 40, paddingBottom: Math.max(insets.bottom, 24) }]}>
        <View style={[styles.logoCircle, { backgroundColor: colors.accent, borderRadius: radius.pill }]}>
          <AppIcon name="heart" size={40} color={colors.textInverse} />
        </View>
        <AppText variant="display" color={colors.textInverse} center style={{ marginTop: spacing.xl }}>
          {config.branding.app_name}
        </AppText>
        <AppText variant="bodyLarge" color={colors.secondary} center style={{ marginTop: spacing.sm }}>
          {config.branding.tagline}
        </AppText>

        <View style={{ marginTop: spacing.xxl }}>
          <AppButton
            title="Create Your Profile"
            variant="gold"
            onPress={() => navigation.navigate('Register')}
          />
          <View style={{ marginTop: spacing.lg }}>
            <AppButton
              title="Already have an account? Log In"
              variant="ghost"
              onPress={() => navigation.navigate('Login')}
              style={{ borderWidth: 1, borderColor: colors.secondary, borderRadius: radius.lg }}
            />
          </View>
        </View>

        <View style={{ marginTop: 'auto', paddingTop: spacing.xl }}>
          <AppText variant="caption" color={colors.secondary} center>
            Trusted, verified matches for a lifetime together
          </AppText>
        </View>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  content: {
    flex: 1,
    paddingHorizontal: 24,
  },
  logoCircle: {
    width: 80,
    height: 80,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
  },
});
