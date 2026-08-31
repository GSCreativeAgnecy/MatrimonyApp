import React from 'react';
import { Linking, Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppHeader } from '../../components/AppHeader';
import { ScreenContainer } from '../../components/ScreenContainer';
import { useTheme } from '../../theme/ThemeProvider';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';

export function HelpSupportScreen() {
  const { colors, radius, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const { legal, support } = config;

  return (
    <ScreenContainer scroll>
      <AppHeader title="Help & Support" showBack />

      <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.xl }]}>
        <AppText variant="h3">Contact Us</AppText>
        {support.email ? (
          <ContactRow icon="mail-outline" label="Email" value={support.email} onPress={() => Linking.openURL(`mailto:${support.email}`)} />
        ) : null}
        {support.phone ? (
          <ContactRow icon="call-outline" label="Phone" value={support.phone} onPress={() => Linking.openURL(`tel:${support.phone}`)} />
        ) : null}
        {!support.email && !support.phone ? (
          <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
            Support contact details are configured by the backend. Please check back soon.
          </AppText>
        ) : null}
      </View>

      <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.xl }]}>
        <AppText variant="h3">Resources</AppText>
        <LinkRow label="Privacy Policy" url={legal.privacy_url} />
        <LinkRow label="Terms of Service" url={legal.terms_url} />
        <LinkRow label="Contact Page" url={legal.contact_url} />
      </View>

      <View style={[styles.card, { backgroundColor: colors.surface, borderRadius: radius.xl }]}>
        <AppText variant="h3">FAQ</AppText>
        <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
          • How do I verify my profile? — Use the Job Verification service under Premium.
        </AppText>
        <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
          • Why can't I send messages? — Free members can send two message templates. Upgrade for unlimited messaging.
        </AppText>
        <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
          • How do filters work? — Filters apply to your discovery feed based on your membership plan.
        </AppText>
      </View>
    </ScreenContainer>
  );
}

function ContactRow({ icon, label, value, onPress }: { icon: 'mail-outline' | 'call-outline'; label: string; value: string; onPress: () => void }) {
  const { colors, spacing } = useTheme();
  return (
    <Pressable accessibilityRole="button" onPress={onPress} style={[styles.row, { borderBottomColor: colors.border }]}>
      <AppIcon name={icon} size={20} color={colors.primary} />
      <View style={{ marginLeft: spacing.md, flex: 1 }}>
        <AppText variant="caption">{label}</AppText>
        <AppText variant="body">{value}</AppText>
      </View>
      <AppIcon name="open-outline" size={18} color={colors.textSecondary} />
    </Pressable>
  );
}

function LinkRow({ label, url }: { label: string; url: string | null }) {
  const { colors, spacing } = useTheme();
  return (
    <Pressable
      accessibilityRole="link"
      disabled={!url}
      onPress={() => url && Linking.openURL(url)}
      style={[styles.row, { borderBottomColor: colors.border, opacity: url ? 1 : 0.5 }]}
    >
      <AppIcon name="document-text-outline" size={20} color={colors.primary} />
      <AppText variant="body" style={{ marginLeft: spacing.md, flex: 1 }}>
        {label}
      </AppText>
      {url ? <AppIcon name="open-outline" size={18} color={colors.textSecondary} /> : null}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 20,
    marginBottom: 16,
  },
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
});
