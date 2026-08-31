import AsyncStorage from '@react-native-async-storage/async-storage';

import { DEFAULT_REMOTE_CONFIG, RemoteConfig } from '../types/remoteConfig';

const CONFIG_CACHE_KEY = 'ardhang:remote_config:v1';

/** Last-known remote config is cached so the UI renders before a network fetch. */
export async function loadCachedRemoteConfig(): Promise<RemoteConfig | null> {
  try {
    const raw = await AsyncStorage.getItem(CONFIG_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed === 'object') {
      return normalizeConfig(parsed);
    }
    return null;
  } catch {
    return null;
  }
}

export async function saveCachedRemoteConfig(config: RemoteConfig): Promise<void> {
  try {
    await AsyncStorage.setItem(CONFIG_CACHE_KEY, JSON.stringify(config));
  } catch {
    // Non-fatal.
  }
}

/** Deep-merge a possibly-partial backend payload over local defaults. */
export function normalizeConfig(raw: Record<string, unknown>): RemoteConfig {
  const src = raw as Partial<RemoteConfig>;
  const defaults = DEFAULT_REMOTE_CONFIG;

  const brand = { ...defaults.branding, ...(src.branding ?? {}) };
  const app = { ...defaults.app, ...(src.app ?? {}) };
  const features = { ...defaults.features, ...(src.features ?? {}) };
  const limits = { ...defaults.limits, ...(src.limits ?? {}) };
  const pricing = { ...defaults.pricing, ...(src.pricing ?? {}) };
  const versions = { ...defaults.versions, ...(src.versions ?? {}) };
  const legal = { ...defaults.legal, ...(src.legal ?? {}) };
  const support = { ...defaults.support, ...(src.support ?? {}) };

  return {
    branding: {
      app_name: typeof brand.app_name === 'string' ? brand.app_name : defaults.branding.app_name,
      tagline: typeof brand.tagline === 'string' ? brand.tagline : defaults.branding.tagline,
      logo_url: brand.logo_url ?? null,
      dark_logo_url: brand.dark_logo_url ?? null,
      primary_color: typeof brand.primary_color === 'string' ? brand.primary_color : defaults.branding.primary_color,
      secondary_color:
        typeof brand.secondary_color === 'string' ? brand.secondary_color : defaults.branding.secondary_color,
      background_color:
        typeof brand.background_color === 'string' ? brand.background_color : defaults.branding.background_color,
      text_color: typeof brand.text_color === 'string' ? brand.text_color : defaults.branding.text_color,
      accent_color: typeof brand.accent_color === 'string' ? brand.accent_color : defaults.branding.accent_color,
    },
    app: {
      maintenance_mode: Boolean(app.maintenance_mode),
      maintenance_message: typeof app.maintenance_message === 'string' ? app.maintenance_message : null,
    },
    features: {
      registration: Boolean(features.registration),
      swiping: Boolean(features.swiping),
      messaging: Boolean(features.messaging),
      astrology: Boolean(features.astrology),
      job_verification: Boolean(features.job_verification),
      family_sharing: Boolean(features.family_sharing),
      video_calls: Boolean(features.video_calls),
      premium: Boolean(features.premium),
    },
    limits: {
      max_photos: Number.isFinite(limits.max_photos) ? Number(limits.max_photos) : defaults.limits.max_photos,
      max_daily_swipes: Number.isFinite(limits.max_daily_swipes)
        ? Number(limits.max_daily_swipes)
        : defaults.limits.max_daily_swipes,
      max_profile_images: Number.isFinite(limits.max_profile_images)
        ? Number(limits.max_profile_images)
        : defaults.limits.max_profile_images,
    },
    pricing: {
      local_job_verification: Number.isFinite(pricing.local_job_verification)
        ? Number(pricing.local_job_verification)
        : defaults.pricing.local_job_verification,
      nri_job_verification: Number.isFinite(pricing.nri_job_verification)
        ? Number(pricing.nri_job_verification)
        : defaults.pricing.nri_job_verification,
    },
    versions: {
      minimum_ios_version:
        typeof versions.minimum_ios_version === 'string'
          ? versions.minimum_ios_version
          : defaults.versions.minimum_ios_version,
      minimum_android_version:
        typeof versions.minimum_android_version === 'string'
          ? versions.minimum_android_version
          : defaults.versions.minimum_android_version,
      latest_ios_version:
        typeof versions.latest_ios_version === 'string'
          ? versions.latest_ios_version
          : defaults.versions.latest_ios_version,
      latest_android_version:
        typeof versions.latest_android_version === 'string'
          ? versions.latest_android_version
          : defaults.versions.latest_android_version,
      force_update_ios: Boolean(versions.force_update_ios),
      force_update_android: Boolean(versions.force_update_android),
    },
    legal: {
      privacy_url: typeof legal.privacy_url === 'string' ? legal.privacy_url : null,
      terms_url: typeof legal.terms_url === 'string' ? legal.terms_url : null,
      contact_url: typeof legal.contact_url === 'string' ? legal.contact_url : null,
    },
    support: {
      email: typeof support.email === 'string' ? support.email : null,
      phone: typeof support.phone === 'string' ? support.phone : null,
    },
    version: typeof raw.version === 'string' ? raw.version : defaults.version,
  };
}
