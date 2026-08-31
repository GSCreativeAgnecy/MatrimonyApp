import React, { useMemo, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppButton } from '../../components/AppButton';
import { AppHeader } from '../../components/AppHeader';
import { BottomSheet } from '../../components/BottomSheet';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { PremiumBadge } from '../../components/PremiumBadge';
import { useTheme } from '../../theme/ThemeProvider';
import { CASTES, COUNTRIES, MARITAL_STATUS_OPTIONS, OCCUPATIONS, RELIGIONS } from '../../api/lookups';
import { usePreferences, useUpdatePreferences } from '../profile/hooks';
import { useSubscription } from '../premium/hooks';
import { AppStackParamList } from '../../navigation/types';
import { ApiError } from '../../types/api';
import { PartnerPreferences } from '../../types/models';

type SheetKind = 'marital' | 'age' | 'height' | 'occupation' | 'country' | 'caste' | 'religion' | null;

interface LocalFilters {
  preferred_marital_status: string | null;
  age_min: number | null;
  age_max: number | null;
  height_min_cm: number | null;
  height_max_cm: number | null;
  preferred_employed_in: string | null;
  countries: string[];
  castes: string[];
  religions: string[];
}

const HEIGHT_OPTIONS = Array.from({ length: 61 }, (_, i) => 120 + i); // 120–180 cm

function toLocal(data: PartnerPreferences | null | undefined): LocalFilters {
  return {
    preferred_marital_status: data?.preferred_marital_status ?? null,
    age_min: data?.age_min ?? null,
    age_max: data?.age_max ?? null,
    height_min_cm: data?.height_min_cm ?? null,
    height_max_cm: data?.height_max_cm ?? null,
    preferred_employed_in: data?.preferred_employed_in ?? null,
    countries: (data?.preferred_countries ?? []).map((c) => c.value),
    castes: (data?.preferred_castes ?? []).map((c) => c.value),
    religions: (data?.preferred_religions ?? []).map((c) => c.value),
  };
}

export function MatchFiltersScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, radius, spacing } = useTheme();

  const { data, isLoading, error, refetch } = usePreferences();
  const updateMutation = useUpdatePreferences();
  const { data: subscription } = useSubscription();

  const [filters, setFilters] = useState<LocalFilters | null>(null);
  const [sheet, setSheet] = useState<SheetKind>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  const isPremium = subscription?.is_premium === true;

  useMemo(() => {
    if (data && !filters) {
      setFilters(toLocal(data));
    }
  }, [data, filters]);

  const set = (patch: Partial<LocalFilters>) => {
    setFilters((prev) => (prev ? { ...prev, ...patch } : prev));
  };

  const toggleMulti = (key: 'countries' | 'castes' | 'religions', value: string) => {
    setFilters((prev) => {
      if (!prev) return prev;
      const list = prev[key];
      const next = list.includes(value) ? list.filter((v) => v !== value) : [...list, value];
      return { ...prev, [key]: next };
    });
  };

  const save = async () => {
    if (!filters) {
      return;
    }
    setSaving(true);
    setSaveError(null);
    try {
      await updateMutation.mutateAsync({
        preferred_marital_status: filters.preferred_marital_status,
        age_min: filters.age_min,
        age_max: filters.age_max,
        height_min_cm: filters.height_min_cm,
        height_max_cm: filters.height_max_cm,
        preferred_employed_in: filters.preferred_employed_in,
        preferred_countries: filters.countries.map((value) => ({ value, level: 'REQUIRED' })),
        preferred_castes: filters.castes.map((value) => ({ value, level: 'REQUIRED' })),
        preferred_religions: filters.religions.map((value) => ({ value, level: 'REQUIRED' })),
      });
      navigation.goBack();
    } catch (e) {
      setSaveError((e as ApiError).message);
    } finally {
      setSaving(false);
    }
  };

  if (isLoading || !filters) {
    return <ScreenContainer><LoadingState message="Loading your search preferences…" /></ScreenContainer>;
  }

  if (error) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={refetch} />
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scroll>
      <AppHeader title="Match Filters" showBack />

      {!isPremium ? (
        <View style={[styles.lockBanner, { backgroundColor: colors.secondary, borderRadius: radius.lg, padding: spacing.lg }]}>
          <View style={{ flexDirection: 'row', alignItems: 'center' }}>
            <AppIcon name="lock-closed" size={20} color={colors.primary} />
            <AppText variant="h3" style={{ marginLeft: spacing.sm, flex: 1 }}>
              Filters are a premium feature
            </AppText>
          </View>
          <AppText variant="bodySmall" style={{ marginTop: spacing.sm }}>
            Free users cannot apply filters. Upgrade to Basic or Premium Plus for advanced search filters.
          </AppText>
          <View style={{ marginTop: spacing.md }}>
            <AppButton title="View Plans" size="md" onPress={() => navigation.navigate('MainTabs', { screen: 'PremiumTab' })} />
          </View>
        </View>
      ) : null}

      <AppText variant="overline" style={{ marginTop: spacing.xl }}>
        Partner Criteria
      </AppText>

      <Row
        label="Marital Status"
        value={labelFor(MARITAL_STATUS_OPTIONS, filters.preferred_marital_status)}
        onPress={() => setSheet('marital')}
        disabled={!isPremium}
      />
      <Row
        label="Age"
        value={rangeText(filters.age_min, filters.age_max, 'yrs')}
        onPress={() => setSheet('age')}
        disabled={!isPremium}
      />
      <Row
        label="Height"
        value={rangeText(filters.height_min_cm, filters.height_max_cm, 'cm')}
        onPress={() => setSheet('height')}
        disabled={!isPremium}
      />
      <Row
        label="Occupation"
        value={filters.preferred_employed_in ?? 'Any'}
        onPress={() => setSheet('occupation')}
        disabled={!isPremium}
      />
      <Row
        label="Country"
        value={filters.countries.length ? filters.countries.join(', ') : 'Any'}
        onPress={() => setSheet('country')}
        disabled={!isPremium}
      />
      <Row
        label="Caste"
        value={filters.castes.length ? filters.castes.join(', ') : 'Any'}
        onPress={() => setSheet('caste')}
        disabled={!isPremium}
      />
      <Row
        label="Religion"
        value={filters.religions.length ? filters.religions.join(', ') : 'Any'}
        onPress={() => setSheet('religion')}
        disabled={!isPremium}
      />

      <View style={[styles.comingSoon, { borderColor: colors.border, borderRadius: radius.lg }]}>
        <AppText variant="label">Coming soon</AppText>
        <AppText variant="bodySmall" style={{ marginTop: 4 }}>
          City, Colour, Salary, Own House and Siblings filters will be available once the backend exposes them.
        </AppText>
      </View>

      {saveError ? <ErrorState compact message={saveError} /> : null}

      <View style={{ marginTop: spacing.xl }}>
        <AppButton
          title={isPremium ? 'Save Filters' : 'Upgrade to Save Filters'}
          onPress={isPremium ? save : () => navigation.navigate('MainTabs', { screen: 'PremiumTab' })}
          loading={saving}
        />
      </View>

      <Sheet
        kind={sheet}
        onClose={() => setSheet(null)}
        filters={filters}
        set={set}
        toggleMulti={toggleMulti}
      />
    </ScreenContainer>
  );
}

function labelFor(options: { value: string; label: string }[], value: string | null): string {
  if (!value) return 'Any';
  return options.find((o) => o.value === value)?.label ?? value;
}

function rangeText(min: number | null, max: number | null, unit: string): string {
  if (!min && !max) return 'Any';
  return `${min ?? '…'} - ${max ?? '…'} ${unit}`;
}

function Row({ label, value, onPress, disabled }: { label: string; value: string; onPress: () => void; disabled?: boolean }) {
  const { colors, radius, spacing } = useTheme();
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled }}
      disabled={disabled}
      onPress={onPress}
      style={({ pressed }) => [
        styles.row,
        {
          backgroundColor: colors.surface,
          borderRadius: radius.md,
          borderColor: colors.border,
          opacity: disabled ? 0.55 : pressed ? 0.9 : 1,
        },
      ]}
    >
      <AppText variant="label">{label}</AppText>
      <View style={{ flexDirection: 'row', alignItems: 'center', flex: 1, marginLeft: spacing.md }}>
        <AppText variant="body" numberOfLines={1} style={{ flex: 1, textAlign: 'right' }}>
          {value}
        </AppText>
        {disabled ? <AppIcon name="lock-closed" size={14} color={colors.textSecondary} /> : <AppIcon name="chevron-down" size={16} color={colors.textSecondary} />}
      </View>
    </Pressable>
  );
}

interface SheetProps {
  kind: SheetKind;
  onClose: () => void;
  filters: LocalFilters;
  set: (patch: Partial<LocalFilters>) => void;
  toggleMulti: (key: 'countries' | 'castes' | 'religions', value: string) => void;
}

function Sheet({ kind, onClose, filters, set, toggleMulti }: SheetProps) {
  const { colors, radius, spacing } = useTheme();

  const optionPress = (value: string) => {
    switch (kind) {
      case 'marital':
        set({ preferred_marital_status: filters.preferred_marital_status === value ? null : value });
        break;
      case 'occupation':
        set({ preferred_employed_in: filters.preferred_employed_in === value ? null : value });
        break;
      case 'country':
        toggleMulti('countries', value);
        break;
      case 'caste':
        toggleMulti('castes', value);
        break;
      case 'religion':
        toggleMulti('religions', value);
        break;
      default:
        break;
    }
  };

  const renderOptions = (title: string, options: { value: string; label: string }[] | string[], selected: (v: string) => boolean) => {
    const list = (Array.isArray(options) && options.length > 0 && typeof options[0] === 'object'
      ? options as { value: string; label: string }[]
      : (options as string[]).map((v) => ({ value: v, label: v })));
    return (
      <>
        <AppText variant="h3" style={{ marginBottom: spacing.md }}>{title}</AppText>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
          {list.map((option) => {
            const isSelected = selected(option.value);
            return (
              <Pressable
                key={option.value}
                onPress={() => optionPress(option.value)}
                style={({ pressed }) => [
                  styles.optionChip,
                  {
                    borderRadius: radius.pill,
                    backgroundColor: isSelected ? colors.primary : colors.surface,
                    borderColor: isSelected ? colors.primary : colors.border,
                    marginRight: spacing.sm,
                    marginBottom: spacing.sm,
                    opacity: pressed ? 0.85 : 1,
                  },
                ]}
              >
                <AppText variant="pill" color={isSelected ? colors.textInverse : colors.text}>
                  {option.label}
                </AppText>
              </Pressable>
            );
          })}
        </View>
      </>
    );
  };

  const title = kind === 'marital' ? 'Marital Status' : kind === 'occupation' ? 'Occupation' : kind === 'country' ? 'Country' : kind === 'caste' ? 'Caste' : kind === 'religion' ? 'Religion' : '';

  return (
    <BottomSheet visible={Boolean(kind)} onClose={onClose} title={title}>
      {kind === 'marital' ? renderOptions('Marital Status', MARITAL_STATUS_OPTIONS, (v) => filters.preferred_marital_status === v) : null}
      {kind === 'occupation' ? renderOptions('Occupation', OCCUPATIONS, (v) => filters.preferred_employed_in === v) : null}
      {kind === 'country' ? renderOptions('Country', COUNTRIES, (v) => filters.countries.includes(v)) : null}
      {kind === 'caste' ? renderOptions('Caste', CASTES, (v) => filters.castes.includes(v)) : null}
      {kind === 'religion' ? renderOptions('Religion', RELIGIONS, (v) => filters.religions.includes(v)) : null}

      {kind === 'age' ? (
        <RangeSheet
          title="Age (years)"
          min={filters.age_min ?? 18}
          max={filters.age_max ?? 60}
          lower={18}
          upper={90}
          unit=""
          onApply={(min, max) => set({ age_min: min, age_max: max })}
        />
      ) : null}
      {kind === 'height' ? (
        <RangeSheet
          title="Height (cm)"
          min={filters.height_min_cm ?? 140}
          max={filters.height_max_cm ?? 185}
          lower={120}
          upper={220}
          unit=" cm"
          onApply={(min, max) => set({ height_min_cm: min, height_max_cm: max })}
        />
      ) : null}
    </BottomSheet>
  );
}

function RangeSheet({ title, min, max, lower, upper, unit, onApply }: { title: string; min: number; max: number; lower: number; upper: number; unit: string; onApply: (min: number, max: number) => void }) {
  const { colors, radius, spacing } = useTheme();
  const [lo, setLo] = useState(min);
  const [hi, setHi] = useState(max);
  const step = unit.includes('cm') ? 1 : 1;
  const range = Array.from({ length: Math.floor((upper - lower) / step) + 1 }, (_, i) => lower + i * step);

  const OptionPill = ({ value, selected, onSelect }: { value: number; selected: boolean; onSelect: (v: number) => void }) => (
    <Pressable
      onPress={() => onSelect(value)}
      style={({ pressed }) => [
        styles.optionChip,
        {
          borderRadius: radius.pill,
          backgroundColor: selected ? colors.primary : colors.surface,
          borderColor: selected ? colors.primary : colors.border,
          marginRight: spacing.sm,
          marginBottom: spacing.sm,
          opacity: pressed ? 0.85 : 1,
        },
      ]}
    >
      <AppText variant="pill" color={selected ? colors.textInverse : colors.text}>
        {value}{unit}
      </AppText>
    </Pressable>
  );

  return (
    <>
      <AppText variant="h3" style={{ marginBottom: spacing.sm }}>{title}</AppText>
      <AppText variant="bodySmall" style={{ marginBottom: spacing.sm }}>
        Minimum: {lo}{unit} · Maximum: {hi}{unit}
      </AppText>
      <AppText variant="caption">Select minimum</AppText>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', marginBottom: spacing.md }}>
        {range.filter((v) => v <= hi).map((v) => (
          <OptionPill key={v} value={v} selected={v === lo} onSelect={(val) => setLo(val)} />
        ))}
      </View>
      <AppText variant="caption">Select maximum</AppText>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
        {range.filter((v) => v >= lo).map((v) => (
          <OptionPill key={v} value={v} selected={v === hi} onSelect={(val) => setHi(val)} />
        ))}
      </View>
      <View style={{ marginTop: spacing.lg }}>
        <AppButton title="Apply" size="md" onPress={() => onApply(lo, hi)} />
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 14,
    borderWidth: 1,
    marginBottom: 10,
  },
  optionChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
  },
  lockBanner: {
    marginBottom: 8,
  },
  comingSoon: {
    borderWidth: 1,
    padding: 16,
    marginTop: 16,
  },
});
