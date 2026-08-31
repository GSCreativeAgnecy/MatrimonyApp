/**
 * Remote app-config model, mirroring the backend `GET /api/v1/app/config`
 * response (`PublicAppConfigResponse`). Stable fields + `extra="allow"` on the
 * backend means we should tolerate unknown keys — always read with defaults.
 */
export interface RemoteConfig {
  branding: {
    app_name: string;
    tagline: string;
    logo_url: string | null;
    dark_logo_url: string | null;
    primary_color: string;
    secondary_color: string;
    background_color: string;
    text_color: string;
    accent_color: string;
  };
  app: {
    maintenance_mode: boolean;
    maintenance_message: string | null;
  };
  features: {
    registration: boolean;
    swiping: boolean;
    messaging: boolean;
    astrology: boolean;
    job_verification: boolean;
    family_sharing: boolean;
    video_calls: boolean;
    premium: boolean;
  };
  limits: {
    max_photos: number;
    max_daily_swipes: number;
    max_profile_images: number;
  };
  pricing: {
    local_job_verification: number;
    nri_job_verification: number;
  };
  versions: {
    minimum_ios_version: string;
    minimum_android_version: string;
    latest_ios_version: string;
    latest_android_version: string;
    force_update_ios: boolean;
    force_update_android: boolean;
  };
  legal: {
    privacy_url: string | null;
    terms_url: string | null;
    contact_url: string | null;
  };
  support: {
    email: string | null;
    phone: string | null;
  };
  version: string;
}

/** Safe local defaults so the UI renders before/when remote config is unavailable. */
export const DEFAULT_REMOTE_CONFIG: RemoteConfig = {
  branding: {
    app_name: 'Ardhang Matrimony',
    tagline: 'Your search for Ardhangini (or Ardhang) starts here',
    logo_url: null,
    dark_logo_url: null,
    primary_color: '#7A1730',
    secondary_color: '#F5EAD9',
    background_color: '#FAF6EF',
    text_color: '#2B2220',
    accent_color: '#C9A24B',
  },
  app: {
    maintenance_mode: false,
    maintenance_message: null,
  },
  features: {
    registration: true,
    swiping: true,
    messaging: true,
    astrology: true,
    job_verification: true,
    family_sharing: true,
    video_calls: false,
    premium: true,
  },
  limits: {
    max_photos: 6,
    max_daily_swipes: 50,
    max_profile_images: 6,
  },
  pricing: {
    local_job_verification: 119,
    nri_job_verification: 199,
  },
  versions: {
    minimum_ios_version: '1.0.0',
    minimum_android_version: '1.0.0',
    latest_ios_version: '1.0.0',
    latest_android_version: '1.0.0',
    force_update_ios: false,
    force_update_android: false,
  },
  legal: {
    privacy_url: null,
    terms_url: null,
    contact_url: null,
  },
  support: {
    email: null,
    phone: null,
  },
  version: 'local-defaults',
};
