import { Platform, ViewStyle } from 'react-native';

/** Subtle, restrained shadows — matrimonial app, not a gaming app. */
export const shadows = {
  card: {
    shadowColor: '#3D2B20',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.08,
    shadowRadius: 10,
    elevation: 2,
  },
  elevated: {
    shadowColor: '#3D2B20',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.12,
    shadowRadius: 16,
    elevation: 4,
  },
  none: {
    shadowOpacity: 0,
    elevation: 0,
  },
} as const;

export function cardShadow(): ViewStyle {
  return Platform.select<ViewStyle>({
    ios: shadows.card as ViewStyle,
    default: { elevation: 2 },
  });
}
