import { apiRequest } from './client';
import { Astrology, Family, FamilyMember } from '../types/models';

export const familyApi = {
  getFamily(): Promise<Family> {
    return apiRequest<{ data: Family }>('/family').then((res) => res.data);
  },

  updateFamily(payload: Partial<Pick<Family, 'family_type' | 'family_values' | 'about_family' | 'family_location'>>) {
    return apiRequest<{ data: Family }>('/family', { method: 'PUT', body: payload }).then((res) => res.data);
  },

  listMembers(): Promise<FamilyMember[]> {
    return apiRequest<{ data: FamilyMember[] }>('/family/members').then((res) => res.data);
  },

  addMember(payload: {
    relationship: string;
    name?: string;
    occupation?: string;
    education?: string;
    marital_status?: string;
  }): Promise<FamilyMember> {
    return apiRequest<{ data: FamilyMember }>('/family/members', { method: 'POST', body: payload }).then(
      (res) => res.data,
    );
  },
};

export const astrologyApi = {
  get(): Promise<Astrology> {
    return apiRequest<{ data: Astrology }>('/astrology').then((res) => res.data);
  },

  update(
    payload: Partial<{
      time_of_birth: string;
      place_of_birth: string;
      birth_lat: number;
      birth_lng: number;
      birth_timezone: string;
      rashi: string;
      nakshatra: string;
      gothram: string;
      dosham: string;
    }>,
  ): Promise<Astrology> {
    return apiRequest<{ data: Astrology }>('/astrology', { method: 'PUT', body: payload }).then((res) => res.data);
  },

  calculate(): Promise<Astrology> {
    return apiRequest<{ data: Astrology }>('/astrology/calculate', { method: 'POST' }).then((res) => res.data);
  },
};
