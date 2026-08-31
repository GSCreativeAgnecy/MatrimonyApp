import { apiRequest } from './client';
import { PartnerPreferences } from '../types/models';

export interface PreferenceItemInput {
  value: string;
  level: string;
}

export interface PreferencesUpdatePayload {
  age_min?: number | null;
  age_max?: number | null;
  height_min_cm?: number | null;
  height_max_cm?: number | null;
  preferred_marital_status?: string | null;
  preferred_physical_status?: string | null;
  preferred_family_values?: string | null;
  preferred_education?: string | null;
  preferred_employed_in?: string | null;
  preferred_religions?: PreferenceItemInput[];
  preferred_castes?: PreferenceItemInput[];
  preferred_languages?: PreferenceItemInput[];
  preferred_countries?: PreferenceItemInput[];
  preferred_states?: PreferenceItemInput[];
  preferred_diets?: PreferenceItemInput[];
}

export const preferencesApi = {
  get(): Promise<PartnerPreferences> {
    return apiRequest<{ data: PartnerPreferences }>('/preferences').then((res) => res.data);
  },

  update(payload: PreferencesUpdatePayload): Promise<PartnerPreferences> {
    return apiRequest<{ data: PartnerPreferences }>('/preferences', { method: 'PUT', body: payload }).then(
      (res) => res.data,
    );
  },
};
