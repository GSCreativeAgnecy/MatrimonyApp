import { apiRequest } from './client';
import { OwnProfile, PrivacySettings } from '../types/models';

export type ProfileUpdatePayload = Partial<
  Pick<
    OwnProfile,
    | 'first_name'
    | 'last_name'
    | 'date_of_birth'
    | 'gender'
    | 'bio'
    | 'intent'
    | 'marital_status'
    | 'height_cm'
    | 'body_type'
    | 'complexion'
    | 'physical_status'
    | 'diet'
    | 'drinking'
    | 'smoking'
    | 'mother_tongue'
    | 'preferred_language'
    | 'religion'
    | 'caste'
    | 'sub_caste'
    | 'education'
    | 'college'
    | 'field_of_study'
    | 'graduation_year'
    | 'employment_status'
    | 'occupation'
    | 'job_title'
    | 'workplace'
    | 'industry'
    | 'annual_income'
    | 'income_currency'
    | 'country'
    | 'state'
    | 'city'
    | 'hometown'
    | 'profile_created_by'
  >
>;

export const profileApi = {
  getMine(): Promise<OwnProfile> {
    return apiRequest<{ data: OwnProfile }>('/profile/me').then((res) => res.data);
  },

  create(payload: ProfileUpdatePayload): Promise<OwnProfile> {
    return apiRequest<{ data: OwnProfile }>('/profile', { method: 'POST', body: payload }).then((res) => res.data);
  },

  update(payload: ProfileUpdatePayload): Promise<OwnProfile> {
    return apiRequest<{ data: OwnProfile }>('/profile', { method: 'PATCH', body: payload }).then((res) => res.data);
  },

  deleteAccount(): Promise<{ status: string }> {
    return apiRequest<{ data: { status: string } }>('/profile', { method: 'DELETE' }).then((res) => res.data);
  },

  getPrivacy(): Promise<PrivacySettings> {
    return apiRequest<{ data: PrivacySettings }>('/profile/privacy').then((res) => res.data);
  },

  updatePrivacy(payload: Partial<PrivacySettings>): Promise<PrivacySettings> {
    return apiRequest<{ data: PrivacySettings }>('/profile/privacy', { method: 'PATCH', body: payload }).then(
      (res) => res.data,
    );
  },
};
