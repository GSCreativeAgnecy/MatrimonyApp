import React, { useState } from 'react';
import { Pressable, StyleSheet, View } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { AppText } from '../../components/AppText';
import { AppIcon, IconName } from '../../components/AppIcon';
import { AppInput } from '../../components/AppInput';
import { AppHeader } from '../../components/AppHeader';
import { ScreenContainer } from '../../components/ScreenContainer';
import { Modal } from '../../components/Modal';
import { useTheme } from '../../theme/ThemeProvider';
import { AppStackParamList } from '../../navigation/types';
import { useDebounce } from '../../hooks/useDebounce';

interface ServiceItem {
  key: string;
  title: string;
  description: string;
  icon: IconName;
  screen?: keyof AppStackParamList;
  available: boolean;
}

const SERVICES: ServiceItem[] = [
  { key: 'astro', title: 'Astro Matching', description: 'Horoscope & compatibility matching', icon: 'planet', screen: 'HoroscopeMatch', available: true },
  { key: 'verified', title: 'Verified Profiles', description: 'Trusted & verified members', icon: 'shield-checkmark', screen: 'MainTabs', available: true },
  { key: 'assistance', title: 'Personalised Assistance', description: 'Dedicated matchmaking help', icon: 'people', available: false },
  { key: 'events', title: 'Exclusive Events', description: 'Members-only meetups', icon: 'calendar', available: false },
];

export function ServicesScreen() {
  const navigation = useNavigation<NativeStackNavigationProp<AppStackParamList>>();
  const { colors, radius, spacing } = useTheme();
  const [query, setQuery] = useState('');
  const debouncedQuery = useDebounce(query, 250);
  const [placeholder, setPlaceholder] = useState<ServiceItem | null>(null);

  const filtered = SERVICES.filter(
    (s) =>
      s.title.toLowerCase().includes(debouncedQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(debouncedQuery.toLowerCase()),
  );

  const open = (service: ServiceItem) => {
    if (service.available && service.screen) {
      if (service.screen === 'MainTabs') {
        navigation.navigate('MainTabs', { screen: 'PremiumTab' });
      } else {
        navigation.navigate(service.screen as never);
      }
    } else {
      setPlaceholder(service);
    }
  };

  return (
    <ScreenContainer scroll>
      <AppHeader title="Services" />
      <AppInput
        value={query}
        onChangeText={setQuery}
        placeholder="Search services…"
        leftIcon="search"
        containerStyle={{ marginBottom: 8 }}
      />

      <AppText variant="overline" style={{ marginVertical: 12 }}>
        Explore Specialised Services
      </AppText>

      {filtered.map((service) => (
        <Pressable
          key={service.key}
          accessibilityRole="button"
          onPress={() => open(service)}
          style={({ pressed }) => [
            styles.card,
            { backgroundColor: colors.surface, borderRadius: radius.xl, opacity: pressed ? 0.92 : 1 },
          ]}
        >
          <View style={[styles.iconWrap, { backgroundColor: colors.secondary, borderRadius: radius.lg }]}>
            <AppIcon name={service.icon} size={26} color={colors.primary} />
          </View>
          <View style={{ flex: 1, marginLeft: spacing.lg }}>
            <AppText variant="h3">{service.title}</AppText>
            <AppText variant="bodySmall" style={{ marginTop: 2 }}>
              {service.description}
            </AppText>
          </View>
          <AppIcon name="chevron-forward" size={20} color={colors.textSecondary} />
        </Pressable>
      ))}

      {filtered.length === 0 ? (
        <AppText variant="body" center style={{ marginTop: 32 }}>
          No services found.
        </AppText>
      ) : null}

      <Modal
        visible={Boolean(placeholder)}
        onClose={() => setPlaceholder(null)}
        title={placeholder?.title}
        message={`${placeholder?.title ?? 'This service'} is not available yet in this version. It will be enabled once the backend supports it.`}
        actions={[{ label: 'OK', onPress: () => undefined }]}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 18,
    marginBottom: 12,
  },
  iconWrap: {
    width: 54,
    height: 54,
    alignItems: 'center',
    justifyContent: 'center',
  },
});
