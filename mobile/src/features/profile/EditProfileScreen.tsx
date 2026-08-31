import React, { useEffect, useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppInput } from '../../components/AppInput';
import { AppButton } from '../../components/AppButton';
import { AppHeader } from '../../components/AppHeader';
import { CollapsibleSection } from '../../components/CollapsibleSection';
import { BottomSheet } from '../../components/BottomSheet';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import {
  BODY_TYPE_OPTIONS,
  CASTES,
  CITIES,
  COMPLEXION_OPTIONS,
  COUNTRIES,
  DIET_OPTIONS,
  DRINKING_OPTIONS,
  EMPLOYMENT_STATUS_OPTIONS,
  FAMILY_TYPE_OPTIONS,
  FAMILY_VALUES_OPTIONS,
  GENDER_OPTIONS,
  HEIGHT_OPTIONS,
  INTENT_OPTIONS,
  MARITAL_STATUS_OPTIONS,
  MOTHER_TONGUES,
  OCCUPATIONS,
  PHYSICAL_STATUS_OPTIONS,
  RELIGIONS,
  SMOKING_OPTIONS,
  STATES,
} from './editOptions';
import { useOwnProfile, useUpdateProfile } from './hooks';
import { ApiError } from '../../types/api';
import { AppStackParamList } from '../../navigation/types';

type SheetKind =
  | 'gender'
  | 'marital_status'
  | 'height'
  | 'body_type'
  | 'complexion'
  | 'physical_status'
  | 'diet'
  | 'drinking'
  | 'smoking'
  | 'employment_status'
  | 'occupation'
  | 'religion'
  | 'caste'
  | 'mother_tongue'
  | 'country'
  | 'state'
  | 'city'
  | 'intent'
  | 'family_type'
  | 'family_values'
  | null;

interface FormState {
  first_name: string;
  last_name: string;
  gender: string | null;
  date_of_birth: string;
  bio: string;
  marital_status: string | null;
  height_cm: number | null;
  body_type: string | null;
  complexion: string | null;
  physical_status: string | null;
  diet: string | null;
  drinking: string | null;
  smoking: string | null;
  mother_tongue: string | null;
  preferred_language: string;
  religion: string | null;
  caste: string | null;
  sub_caste: string;
  education: string;
  college: string;
  field_of_study: string;
  graduation_year: string;
  employment_status: string | null;
  occupation: string | null;
  job_title: string;
  workplace: string;
  industry: string;
  annual_income: string;
  income_currency: string;
  country: string | null;
  state: string | null;
  city: string | null;
  hometown: string;
  intent: string | null;
  profile_created_by: string;
  family_type: string | null;
  family_values: string | null;
}

function initForm(profile: NonNullable<ReturnType<typeof useOwnProfile>['data']>): FormState {
  return {
    first_name: profile.first_name ?? '',
    last_name: profile.last_name ?? '',
    gender: profile.gender ?? null,
    date_of_birth: profile.date_of_birth ?? '',
    bio: profile.bio ?? '',
    marital_status: profile.marital_status ?? null,
    height_cm: profile.height_cm ?? null,
    body_type: profile.body_type ?? null,
    complexion: profile.complexion ?? null,
    physical_status: profile.physical_status ?? null,
    diet: profile.diet ?? null,
    drinking: profile.drinking ?? null,
    smoking: profile.smoking ?? null,
    mother_tongue: profile.mother_tongue ?? null,
    preferred_language: profile.preferred_language ?? '',
    religion: profile.religion ?? null,
    caste: profile.caste ?? null,
    sub_caste: profile.sub_caste ?? '',
    education: profile.education ?? '',
    college: profile.college ?? '',
    field_of_study: profile.field_of_study ?? '',
    graduation_year: profile.graduation_year ? String(profile.graduation_year) : '',
    employment_status: profile.employment_status ?? null,
    occupation: profile.occupation ?? null,
    job_title: profile.job_title ?? '',
    workplace: profile.workplace ?? '',
    industry: profile.industry ?? '',
    annual_income: profile.annual_income != null ? String(profile.annual_income) : '',
    income_currency: profile.income_currency ?? 'INR',
    country: profile.country ?? null,
    state: profile.state ?? null,
    city: profile.city ?? null,
    hometown: profile.hometown ?? '',
    intent: profile.intent ?? null,
    profile_created_by: profile.profile_created_by ?? '',
    family_type: null,
    family_values: null,
  };
}

export function EditProfileScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, spacing } = useTheme();

  const { data: profile, isLoading, error, refetch } = useOwnProfile();
  const updateMutation = useUpdateProfile();

  const [form, setForm] = useState<FormState | null>(null);
  const [sheet, setSheet] = useState<SheetKind>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (profile && !form) {
      setForm(initForm(profile));
    }
  }, [profile, form]);

  if (isLoading || !form) {
    return <ScreenContainer><LoadingState message="Loading profile…" /></ScreenContainer>;
  }
  if (error) {
    return (
      <ScreenContainer>
        <ErrorState onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => (prev ? { ...prev, [key]: value } : prev));
    setSaveError(null);
  };

  const save = async () => {
    if (!form) return;
    setSaving(true);
    setSaveError(null);
    setSaved(false);
    try {
      await updateMutation.mutateAsync({
        first_name: form.first_name.trim() || undefined,
        last_name: form.last_name.trim() || undefined,
        gender: form.gender ?? undefined,
        date_of_birth: form.date_of_birth || undefined,
        bio: form.bio || undefined,
        marital_status: form.marital_status ?? undefined,
        height_cm: form.height_cm ?? undefined,
        body_type: form.body_type ?? undefined,
        complexion: form.complexion ?? undefined,
        physical_status: form.physical_status ?? undefined,
        diet: form.diet ?? undefined,
        drinking: form.drinking ?? undefined,
        smoking: form.smoking ?? undefined,
        mother_tongue: form.mother_tongue ?? undefined,
        preferred_language: form.preferred_language || undefined,
        religion: form.religion ?? undefined,
        caste: form.caste ?? undefined,
        sub_caste: form.sub_caste || undefined,
        education: form.education || undefined,
        college: form.college || undefined,
        field_of_study: form.field_of_study || undefined,
        graduation_year: form.graduation_year ? Number(form.graduation_year) : undefined,
        employment_status: form.employment_status ?? undefined,
        occupation: form.occupation ?? undefined,
        job_title: form.job_title || undefined,
        workplace: form.workplace || undefined,
        industry: form.industry || undefined,
        annual_income: form.annual_income ? Number(form.annual_income) : undefined,
        income_currency: form.income_currency || undefined,
        country: form.country ?? undefined,
        state: form.state ?? undefined,
        city: form.city ?? undefined,
        hometown: form.hometown || undefined,
        intent: form.intent ?? undefined,
        profile_created_by: form.profile_created_by || undefined,
      });
      setSaved(true);
    } catch (e) {
      setSaveError((e as ApiError).message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <ScreenContainer scroll>
      <AppHeader title="Edit Profile" showBack />

      <CollapsibleSection title="Basic Information" defaultOpen>
        <AppInput label="First Name" value={form.first_name} onChangeText={(v) => set('first_name', v)} placeholder="First name" autoCapitalize="words" />
        <AppInput label="Last Name" value={form.last_name} onChangeText={(v) => set('last_name', v)} placeholder="Last name" autoCapitalize="words" />
        <SelectField label="Gender" value={form.gender} options={GENDER_OPTIONS} onPress={() => setSheet('gender')} />
        <AppInput
          label="Date of Birth (YYYY-MM-DD)"
          value={form.date_of_birth}
          onChangeText={(v) => set('date_of_birth', v)}
          placeholder="1995-06-15"
        />
      </CollapsibleSection>

      <CollapsibleSection title="Personal Details" defaultOpen={false}>
        <SelectField label="Marital Status" value={form.marital_status} options={MARITAL_STATUS_OPTIONS} onPress={() => setSheet('marital_status')} />
        <SelectField label="Height" value={form.height_cm != null ? `${form.height_cm} cm` : null} options={HEIGHT_OPTIONS} onPress={() => setSheet('height')} />
        <SelectField label="Mother Tongue" value={form.mother_tongue} options={MOTHER_TONGUES} onPress={() => setSheet('mother_tongue')} />
        <AppInput label="Preferred Language" value={form.preferred_language} onChangeText={(v) => set('preferred_language', v)} placeholder="e.g. Hindi" />
        <SelectField label="Intent" value={form.intent} options={INTENT_OPTIONS} onPress={() => setSheet('intent')} />
      </CollapsibleSection>

      <CollapsibleSection title="Appearance" defaultOpen={false}>
        <SelectField label="Body Type" value={form.body_type} options={BODY_TYPE_OPTIONS} onPress={() => setSheet('body_type')} />
        <SelectField label="Colour" value={form.complexion} options={COMPLEXION_OPTIONS} onPress={() => setSheet('complexion')} />
        <SelectField label="Physical Status" value={form.physical_status} options={PHYSICAL_STATUS_OPTIONS} onPress={() => setSheet('physical_status')} />
      </CollapsibleSection>

      <CollapsibleSection title="Education & Career" defaultOpen={false}>
        <AppInput label="Education" value={form.education} onChangeText={(v) => set('education', v)} placeholder="e.g. B.Tech" />
        <AppInput label="College" value={form.college} onChangeText={(v) => set('college', v)} placeholder="College name" />
        <AppInput label="Field of Study" value={form.field_of_study} onChangeText={(v) => set('field_of_study', v)} placeholder="e.g. Computer Science" />
        <AppInput label="Graduation Year" value={form.graduation_year} onChangeText={(v) => set('graduation_year', v)} keyboardType="number-pad" maxLength={4} />
        <SelectField label="Employment Status" value={form.employment_status} options={EMPLOYMENT_STATUS_OPTIONS} onPress={() => setSheet('employment_status')} />
        <SelectField label="Occupation" value={form.occupation} options={OCCUPATIONS} onPress={() => setSheet('occupation')} />
        <AppInput label="Job Title" value={form.job_title} onChangeText={(v) => set('job_title', v)} placeholder="e.g. Senior Engineer" />
        <AppInput label="Workplace" value={form.workplace} onChangeText={(v) => set('workplace', v)} placeholder="Company name" />
        <AppInput label="Industry" value={form.industry} onChangeText={(v) => set('industry', v)} placeholder="e.g. IT Services" />
      </CollapsibleSection>

      <CollapsibleSection title="Family" defaultOpen={false}>
        <SelectField label="Family Type" value={form.family_type} options={FAMILY_TYPE_OPTIONS} onPress={() => setSheet('family_type')} />
        <SelectField label="Family Values" value={form.family_values} options={FAMILY_VALUES_OPTIONS} onPress={() => setSheet('family_values')} />
      </CollapsibleSection>

      <CollapsibleSection title="Lifestyle" defaultOpen={false}>
        <SelectField label="Diet" value={form.diet} options={DIET_OPTIONS} onPress={() => setSheet('diet')} />
        <SelectField label="Drinking" value={form.drinking} options={DRINKING_OPTIONS} onPress={() => setSheet('drinking')} />
        <SelectField label="Smoking" value={form.smoking} options={SMOKING_OPTIONS} onPress={() => setSheet('smoking')} />
      </CollapsibleSection>

      <CollapsibleSection title="Location" defaultOpen={false}>
        <SelectField label="Country" value={form.country} options={COUNTRIES} onPress={() => setSheet('country')} />
        <SelectField label="State" value={form.state} options={STATES} onPress={() => setSheet('state')} />
        <SelectField label="City" value={form.city} options={CITIES} onPress={() => setSheet('city')} />
        <AppInput label="Hometown" value={form.hometown} onChangeText={(v) => set('hometown', v)} placeholder="Hometown" />
      </CollapsibleSection>

      <CollapsibleSection title="Financial Information" defaultOpen={false}>
        <AppInput
          label="Annual Income (INR)"
          value={form.annual_income}
          onChangeText={(v) => set('annual_income', v)}
          keyboardType="number-pad"
          placeholder="e.g. 1200000"
        />
        <AppInput label="Currency" value={form.income_currency} onChangeText={(v) => set('income_currency', v)} maxLength={3} />
      </CollapsibleSection>

      <CollapsibleSection title="About Me" defaultOpen={false}>
        <AppInput
          label="Bio"
          value={form.bio}
          onChangeText={(v) => set('bio', v)}
          placeholder="Tell potential matches a little about yourself…"
          multiline
          style={{ height: 96, textAlignVertical: 'top' }}
        />
      </CollapsibleSection>

      <CollapsibleSection title="Partner Preferences" defaultOpen={false}>
        <AppText variant="bodySmall" style={{ marginBottom: spacing.md }}>
          Partner preferences control your discovery filters and are set on the Match Filters screen.
        </AppText>
        <AppButton title="Open Match Filters" size="md" variant="outline" onPress={() => navigation.navigate('MatchFilters')} />
      </CollapsibleSection>

      {saveError ? <ErrorState compact message={saveError} /> : null}
      {saved ? (
        <AppText variant="body" color={colors.success} center style={{ marginVertical: 8 }}>
          Profile saved successfully.
        </AppText>
      ) : null}

      <AppButton title="Save Profile" onPress={save} loading={saving} />

      <Sheet kind={sheet} onClose={() => setSheet(null)} form={form} set={set} />
    </ScreenContainer>
  );
}

function SelectField({
  label,
  value,
  options,
  onPress,
}: {
  label: string;
  value: string | number | null;
  options: { value: string; label: string }[] | string[];
  onPress: () => void;
}) {
  const { colors, radius, spacing } = useTheme();
  const normalized: { value: string; label: string }[] = Array.isArray(options)
    ? options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o))
    : options;
  const labelText = labelFor(normalized, value) ?? (value != null ? String(value) : 'Select');
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      style={[
        styles.select,
        { backgroundColor: colors.surface, borderColor: colors.border, borderRadius: radius.md, marginBottom: spacing.lg },
      ]}
    >
      <AppText variant="label">{label}</AppText>
      <View style={{ flexDirection: 'row', alignItems: 'center' }}>
        <AppText variant="body" color={value != null ? colors.text : colors.textSecondary} style={{ marginRight: 8 }}>
          {labelText}
        </AppText>
      </View>
    </Pressable>
  );
}

function labelFor(options: { value: string; label: string }[], value: string | number | null): string | null {
  if (value === null || value === undefined) return null;
  const match = options.find((o) => o.value === String(value));
  return match ? match.label : null;
}

interface SheetProps {
  kind: SheetKind;
  onClose: () => void;
  form: FormState;
  set: (key: keyof FormState, value: FormState[keyof FormState]) => void;
}

function Sheet({ kind, onClose, form, set }: SheetProps) {
  const { colors, radius, spacing } = useTheme();

  const optionDefs: Partial<Record<Exclude<SheetKind, null>, { value: string; label: string }[] | string[]>> = {
    gender: GENDER_OPTIONS,
    marital_status: MARITAL_STATUS_OPTIONS,
    body_type: BODY_TYPE_OPTIONS,
    complexion: COMPLEXION_OPTIONS,
    physical_status: PHYSICAL_STATUS_OPTIONS,
    diet: DIET_OPTIONS,
    drinking: DRINKING_OPTIONS,
    smoking: SMOKING_OPTIONS,
    employment_status: EMPLOYMENT_STATUS_OPTIONS,
    intent: INTENT_OPTIONS,
    family_type: FAMILY_TYPE_OPTIONS,
    family_values: FAMILY_VALUES_OPTIONS,
  };

  const listOptions: Partial<Record<Exclude<SheetKind, null>, { value: string; label: string }[] | string[]>> = {
    height: HEIGHT_OPTIONS,
    occupation: OCCUPATIONS,
    religion: RELIGIONS,
    caste: CASTES,
    mother_tongue: MOTHER_TONGUES,
    country: COUNTRIES,
    state: STATES,
    city: CITIES,
  };

  const fieldKey: Record<string, keyof FormState> = {
    gender: 'gender',
    marital_status: 'marital_status',
    height: 'height_cm',
    body_type: 'body_type',
    complexion: 'complexion',
    physical_status: 'physical_status',
    diet: 'diet',
    drinking: 'drinking',
    smoking: 'smoking',
    employment_status: 'employment_status',
    occupation: 'occupation',
    religion: 'religion',
    caste: 'caste',
    mother_tongue: 'mother_tongue',
    country: 'country',
    state: 'state',
    city: 'city',
    intent: 'intent',
    family_type: 'family_type',
    family_values: 'family_values',
  };

  const title =
    kind === 'height'
      ? 'Height'
      : kind === 'occupation'
        ? 'Occupation'
        : kind === 'religion'
          ? 'Religion'
          : kind === 'caste'
            ? 'Caste'
            : kind === 'mother_tongue'
              ? 'Mother Tongue'
              : kind === 'country'
                ? 'Country'
                : kind === 'state'
                  ? 'State'
                  : kind === 'city'
                    ? 'City'
                    : kind
                      ? kind.replace(/_/g, ' ')
                      : '';

  const rawOptions = kind ? optionDefs[kind] ?? listOptions[kind] ?? [] : [];
  const options: { value: string; label: string }[] = rawOptions.map((o) =>
    typeof o === 'string' ? { value: o, label: o } : o,
  );
  const key = kind ? fieldKey[kind] : null;

  return (
    <BottomSheet visible={Boolean(kind)} onClose={onClose} title={title}>
      <View style={{ flexDirection: 'row', flexWrap: 'wrap' }}>
        {options.map((option) => {
          const current = key ? form[key] : null;
          const isSelected = String(current ?? '').toUpperCase() === option.value.toUpperCase();
          return (
            <Pressable
              key={option.value}
              onPress={() => {
                if (!key) {
                  return;
                }
                if (key === 'height_cm') {
                  set(key, Number(option.value));
                } else {
                  set(key, option.value);
                }
                onClose();
              }}
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
    </BottomSheet>
  );
}

const styles = StyleSheet.create({
  select: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    height: 52,
    paddingHorizontal: 14,
    borderWidth: 1.5,
  },
  optionChip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
  },
});
