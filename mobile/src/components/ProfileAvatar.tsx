import React from 'react';
import { Image, StyleSheet, View, ViewStyle } from 'react-native';

import { AppText } from './AppText';
import { useTheme } from '../theme/ThemeProvider';
import { imageUrl } from '../utils/imageUrl';
import { initials } from '../utils/format';

interface ProfileAvatarProps {
  uri?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  size?: number;
  online?: boolean;
  style?: ViewStyle;
}

/** Rounded avatar with initials fallback and optional online indicator. */
export function ProfileAvatar({ uri, firstName, lastName, size = 56, online = false, style }: ProfileAvatarProps) {
  const { colors, radius } = useTheme();
  const source = imageUrl(uri);
  const radiusValue = radius.pill;

  return (
    <View style={[{ width: size, height: size }, style]}>
      {source ? (
        <Image
          source={{ uri: source }}
          style={{ width: size, height: size, borderRadius: radiusValue, backgroundColor: colors.secondary }}
          accessibilityLabel="Profile photo"
        />
      ) : (
        <View
          style={[
            styles.fallback,
            {
              width: size,
              height: size,
              borderRadius: radiusValue,
              backgroundColor: colors.secondary,
            },
          ]}
        >
          <AppText variant="h3" color={colors.primary} style={{ fontWeight: '800' }}>
            {initials(firstName, lastName)}
          </AppText>
        </View>
      )}
      {online ? (
        <View
          style={[
            styles.dot,
            {
              backgroundColor: colors.success,
              borderColor: colors.surface,
              width: size >= 40 ? 14 : 10,
              height: size >= 40 ? 14 : 10,
              borderRadius: 7,
              borderWidth: 2,
            },
          ]}
        />
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  fallback: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  dot: {
    position: 'absolute',
    right: 0,
    bottom: 0,
  },
});
