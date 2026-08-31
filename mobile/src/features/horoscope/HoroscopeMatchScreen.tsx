import React, { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useQuery } from '@tanstack/react-query';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppButton } from '../../components/AppButton';
import { AppHeader } from '../../components/AppHeader';
import { ScreenContainer } from '../../components/ScreenContainer';
import { useTheme } from '../../theme/ThemeProvider';
import { astrologyApi } from '../../api/family';
import { queryKeys } from '../../query/keys';

interface Answer {
  label: string;
  score: number;
}

interface Question {
  key: string;
  title: string;
  prompt: string;
  options: Answer[];
}

const QUESTIONS: Question[] = [
  {
    key: 'in_laws',
    title: 'Family Setup',
    prompt: 'Comfortable living with in-laws?',
    options: [
      { label: 'Yes', score: 10 },
      { label: 'No', score: 6 },
    ],
  },
  {
    key: 'family_type',
    title: 'Family Type',
    prompt: 'What family setup do you prefer?',
    options: [
      { label: 'Orthodox', score: 6 },
      { label: 'Moderate', score: 10 },
      { label: 'Conservative', score: 8 },
      { label: 'Liberal', score: 6 },
    ],
  },
  {
    key: 'dual_income',
    title: 'Dual Income Expectations',
    prompt: 'Do you expect both partners to work?',
    options: [
      { label: 'Yes', score: 10 },
      { label: 'No', score: 6 },
    ],
  },
  {
    key: 'relocate',
    title: 'Geographical Flexibility',
    prompt: 'Are you willing to relocate for your partner?',
    options: [
      { label: 'Yes', score: 10 },
      { label: 'No', score: 6 },
      { label: 'Within my state', score: 8 },
    ],
  },
  {
    key: 'finances',
    title: 'Financial Management',
    prompt: 'How do you prefer to manage finances?',
    options: [
      { label: 'Split', score: 8 },
      { label: 'Joint Account', score: 10 },
    ],
  },
  {
    key: 'diet',
    title: 'Dietary Preference',
    prompt: 'What is your dietary preference?',
    options: [
      { label: 'Veg', score: 8 },
      { label: 'Non-Veg', score: 8 },
    ],
  },
  {
    key: 'habits',
    title: 'Drinking / Smoking',
    prompt: 'Your drinking / smoking preference?',
    options: [
      { label: 'Yes', score: 4 },
      { label: 'No', score: 10 },
      { label: 'Occasional', score: 8 },
    ],
  },
  {
    key: 'children',
    title: 'Children',
    prompt: 'Do you want children?',
    options: [
      { label: 'Yes, want children', score: 8 },
      { label: 'No', score: 8 },
      { label: 'Maybe after 2 years', score: 10 },
    ],
  },
];

export function HoroscopeMatchScreen() {
  const { colors, radius, spacing } = useTheme();

  const { data: astrology } = useQuery({
    queryKey: queryKeys.profile.astrology,
    queryFn: () => astrologyApi.get(),
  });

  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [completed, setCompleted] = useState(false);

  const total = QUESTIONS.length;
  const current = QUESTIONS[step];
  const selected = answers[current?.key];

  const choose = (label: string) => {
    setAnswers((prev) => ({ ...prev, [current.key]: label }));
    if (step + 1 < total) {
      setStep((s) => s + 1);
    } else {
      setCompleted(true);
    }
  };

  const score = () => {
    let earned = 0;
    let max = 0;
    QUESTIONS.forEach((q) => {
      const label = answers[q.key];
      const option = q.options.find((o) => o.label === label);
      earned += option?.score ?? 0;
      max += Math.max(...q.options.map((o) => o.score));
    });
    return Math.round((earned / max) * 100);
  };

  const result = completed ? score() : 0;

  const restart = () => {
    setAnswers({});
    setStep(0);
    setCompleted(false);
  };

  if (completed) {
    const verdict = result >= 80 ? 'Excellent Match' : result >= 60 ? 'Good Match' : 'Needs Conversation';
    return (
      <ScreenContainer scroll>
        <AppHeader title="Horoscope Match" showBack />
        <View style={[styles.resultCard, { backgroundColor: colors.surface, borderRadius: radius.xxl, padding: spacing.xxl }]}>
          <View style={[styles.scoreCircle, { backgroundColor: colors.secondary, borderRadius: radius.pill, width: 140, height: 140 }]}>
            <AppText variant="display" color={colors.primary} style={{ fontSize: 40, lineHeight: 48 }}>
              {result}%
            </AppText>
          </View>
          <AppText variant="h2" center style={{ marginTop: spacing.xl }}>
            Compatibility: {verdict}
          </AppText>
          <AppText variant="body" center style={{ marginTop: spacing.sm }}>
            Based on your preferences, you have strong alignment across family values, lifestyle and long-term goals.
          </AppText>
        </View>

        {astrology?.rashi || astrology?.nakshatra ? (
          <View style={{ backgroundColor: colors.surface, borderRadius: 16, padding: spacing.lg, marginTop: spacing.lg }}>
            <AppText variant="h3">Your horoscope profile</AppText>
            <View style={styles.astroRow}>
              <AppText variant="bodySmall" style={{ flex: 1 }}>Rashi</AppText>
              <AppText variant="body">{astrology.rashi ?? '—'}</AppText>
            </View>
            <View style={styles.astroRow}>
              <AppText variant="bodySmall" style={{ flex: 1 }}>Nakshatra</AppText>
              <AppText variant="body">{astrology.nakshatra ?? '—'}</AppText>
            </View>
            <View style={styles.astroRow}>
              <AppText variant="bodySmall" style={{ flex: 1 }}>Dosham</AppText>
              <AppText variant="body">{astrology.dosham ?? '—'}</AppText>
            </View>
          </View>
        ) : null}

        <AppText variant="caption" center style={{ marginTop: spacing.lg }}>
          This is a self-assessment preview. Full astrological compatibility requires backend-provided matching.
        </AppText>

        <View style={{ marginTop: spacing.xl }}>
          <AppButton title="Start Over" onPress={restart} variant="outline" />
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer scroll>
      <AppHeader title="Horoscope Match" showBack />

      <View style={styles.progressRow}>
        {QUESTIONS.map((q, i) => (
          <View
            key={q.key}
            style={[
              styles.progressDot,
              {
                backgroundColor: i < step ? colors.primary : i === step ? colors.accent : colors.border,
                borderRadius: 4,
              },
            ]}
          />
        ))}
      </View>

      <View style={{ marginTop: spacing.xl }}>
        <AppText variant="overline">{current.title}</AppText>
        <AppText variant="h1" style={{ marginTop: spacing.sm, marginBottom: spacing.xl }}>
          {current.prompt}
        </AppText>

        {current.options.map((option) => {
          const isSelected = selected === option.label;
          return (
            <Pressable
              key={option.label}
              accessibilityRole="button"
              accessibilityState={{ selected: isSelected }}
              onPress={() => choose(option.label)}
              style={({ pressed }) => [
                styles.option,
                {
                  backgroundColor: isSelected ? colors.primary : colors.surface,
                  borderRadius: radius.lg,
                  borderColor: isSelected ? colors.primary : colors.border,
                  opacity: pressed ? 0.9 : 1,
                },
              ]}
            >
              <AppText variant="bodyLarge" color={isSelected ? colors.textInverse : colors.text}>
                {option.label}
              </AppText>
              <AppIcon name={isSelected ? 'checkmark-circle' : 'ellipse-outline'} size={22} color={isSelected ? colors.textInverse : colors.textSecondary} />
            </Pressable>
          );
        })}

        {step > 0 ? (
          <AppButton title="Back" variant="ghost" onPress={() => setStep((s) => s - 1)} style={{ marginTop: spacing.lg }} />
        ) : null}
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  progressRow: {
    flexDirection: 'row',
    gap: 6,
  },
  progressDot: {
    flex: 1,
    height: 6,
  },
  option: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    paddingHorizontal: 18,
    borderWidth: 1.5,
    marginBottom: 12,
  },
  resultCard: {
    alignItems: 'center',
    marginTop: 8,
  },
  scoreCircle: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  astroRow: {
    flexDirection: 'row',
    paddingVertical: 8,
  },
});
