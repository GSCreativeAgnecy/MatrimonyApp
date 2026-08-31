import React from 'react';
import { StyleSheet, View } from 'react-native';

import { AppText } from './AppText';
import { AppButton } from './AppButton';
import { PremiumBadge } from './PremiumBadge';
import { useTheme } from '../theme/ThemeProvider';
import { SubscriptionPlan } from '../types/models';
import { formatPrice } from '../utils/format';

interface SubscriptionCardProps {
  plan: SubscriptionPlan;
  highlighted?: boolean;
  onSelect?: () => void;
  ctaLabel?: string;
  loading?: boolean;
}

export function SubscriptionCard({ plan, highlighted = false, onSelect, ctaLabel = 'Upgrade Now', loading = false }: SubscriptionCardProps) {
  const { colors, radius, spacing } = useTheme();

  const featureList: string[] = (() => {
    const raw = plan.features;
    if (raw && Array.isArray(raw)) {
      return (raw as string[]).map(String);
    }
    if (raw && typeof raw === 'object') {
      return Object.entries(raw)
        .filter(([, v]) => v === true || (typeof v === 'string' && v.length > 0))
        .map(([k]) => k.replace(/_/g, ' '));
    }
    return [];
  })();

  return (
    <View
      style={{
        borderRadius: radius.xl,
        padding: spacing.xl,
        backgroundColor: highlighted ? colors.primary : colors.surface,
        borderWidth: highlighted ? 0 : 1,
        borderColor: colors.border,
      }}
    >
      <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
        <AppText variant="h2" color={highlighted ? colors.textInverse : colors.text}>
          {plan.name}
        </AppText>
        {highlighted ? <PremiumBadge size="md" /> : null}
      </View>
      <View style={{ flexDirection: 'row', alignItems: 'baseline', marginTop: spacing.sm }}>
        <AppText
          variant="display"
          color={highlighted ? colors.accent : colors.primary}
          style={{ fontSize: 34, lineHeight: 40 }}
        >
          {formatPrice(plan.price, plan.currency)}
        </AppText>
        <AppText variant="caption" color={highlighted ? colors.secondary : colors.textSecondary} style={{ marginLeft: spacing.sm }}>
          / {plan.duration_days} days
        </AppText>
      </View>
      {plan.description ? (
        <AppText
          variant="bodySmall"
          color={highlighted ? colors.secondary : colors.textSecondary}
          style={{ marginTop: spacing.sm }}
        >
          {plan.description}
        </AppText>
      ) : null}
      {featureList.length > 0 ? (
        <View style={{ marginTop: spacing.lg }}>
          {featureList.map((feature) => (
            <View key={feature} style={styles.featureRow}>
              <AppText variant="caption" color={highlighted ? colors.accent : colors.success}>
                ✓
              </AppText>
              <AppText
                variant="bodySmall"
                color={highlighted ? colors.textInverse : colors.text}
                style={{ marginLeft: spacing.sm, textTransform: 'capitalize' }}
              >
                {feature}
              </AppText>
            </View>
          ))}
        </View>
      ) : null}
      {onSelect ? (
        <View style={{ marginTop: spacing.xl }}>
          <AppButton
            title={ctaLabel}
            onPress={onSelect}
            variant={highlighted ? 'gold' : 'primary'}
            loading={loading}
          />
        </View>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
});
