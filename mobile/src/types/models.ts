import { ApiError } from './api';
import { PhotoVerificationStatus, PhotoVisibility } from './enums';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserAccount {
  id: string;
  email: string | null;
  phone_number: string | null;
  account_status: string;
  role: string;
  is_banned: boolean;
  email_verified: boolean;
  phone_verified: boolean;
  created_at: string | null;
}

/** Matches backend OwnProfileResponse. */
export interface OwnProfile {
  id: string;
  user_id: string;
  first_name: string | null;
  last_name: string | null;
  date_of_birth: string | null;
  gender: string | null;
  bio: string | null;
  intent: string | null;
  marital_status: string | null;
  height_cm: number | null;
  body_type: string | null;
  complexion: string | null;
  physical_status: string | null;
  diet: string | null;
  drinking: string | null;
  smoking: string | null;
  mother_tongue: string | null;
  preferred_language: string | null;
  religion: string | null;
  caste: string | null;
  sub_caste: string | null;
  education: string | null;
  college: string | null;
  field_of_study: string | null;
  graduation_year: number | null;
  employment_status: string | null;
  occupation: string | null;
  job_title: string | null;
  workplace: string | null;
  industry: string | null;
  annual_income: number | null;
  income_currency: string | null;
  country: string | null;
  state: string | null;
  city: string | null;
  hometown: string | null;
  profile_created_by: string | null;
  location_lat: number | null;
  location_lng: number | null;
  location_updated_at: string | null;
  privacy: PrivacySettings | null;
  profile_photo: string | null;
  photo_count: number;
  created_at: string | null;
}

export interface PrivacySettings {
  show_online_status: boolean;
  show_distance: boolean;
  show_last_seen: boolean;
  profile_visibility: string;
  photo_visibility: string;
  phone_visibility: string;
  email_visibility: string;
  allow_messages_from: string;
  allow_match_requests: boolean;
}

/** Public profile shown to non-matched users. */
export interface PublicProfile {
  id: string;
  user_id: string;
  first_name: string | null;
  gender: string | null;
  age: number | null;
  marital_status: string | null;
  religion: string | null;
  caste: string | null;
  mother_tongue: string | null;
  education: string | null;
  occupation: string | null;
  job_title: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  distance_km: number | null;
  bio: string | null;
  intent: string | null;
  diet: string | null;
  drinking: string | null;
  smoking: string | null;
  height_cm: number | null;
  body_type: string | null;
  profile_photo: string | null;
  last_seen: string | null;
  is_online: boolean;
  is_verified_photo: boolean;
  is_verified_job: boolean;
}

/** Matched-profile adds contact fields. */
export interface MatchedProfile extends PublicProfile {
  phone_number?: string | null;
  email?: string | null;
  workplace?: string | null;
}

export interface RecommendationItem {
  candidate_user_id: string;
  score: number;
  reason_codes: string[];
}

export interface RecommendationFeed {
  items: RecommendationItem[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface SwipeResult {
  id: string;
  from_user_id: string;
  to_user_id: string;
  action: string;
  created_at: string;
  match_created: boolean;
  match_id: string | null;
}

export interface MatchItem {
  id: string;
  user_id: string;
  first_name: string | null;
  age: number | null;
  city: string | null;
  state: string | null;
  country: string | null;
  occupation: string | null;
  profile_photo: string | null;
  status: string;
  matched_at: string | null;
}

export interface Conversation {
  id: string;
  other_user_id: string;
  other_user_name: string | null;
  other_user_photo: string | null;
  last_message_preview: string | null;
  last_message_at: string | null;
  unread_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  message_type: string;
  body: string | null;
  media_url: string | null;
  created_at: string;
  read_at: string | null;
}

export interface AppNotification {
  id: string;
  type: string;
  title: string | null;
  body: string | null;
  data: Record<string, unknown> | null;
  is_read: boolean;
  created_at: string;
}

export interface SubscriptionPlan {
  id: string;
  name: string;
  description: string | null;
  price: number;
  currency: string;
  duration_days: number;
  features: Record<string, unknown> | null;
}

export interface Subscription {
  id: string | null;
  plan_name: string | null;
  status: string;
  starts_at: string | null;
  expires_at: string | null;
  auto_renew: boolean;
  is_premium: boolean;
}

export interface CheckoutResult {
  checkout_url: string | null;
  payment_id: string;
  provider: string;
  amount: number;
  currency: string;
}

export interface JobVerification {
  id: string;
  employment_type: string;
  employer_name: string;
  job_title: string | null;
  country: string | null;
  verification_status: string;
  amount_paid: number | null;
  currency: string | null;
  submitted_at: string | null;
  verified_at: string | null;
  expires_at: string | null;
  rejection_reason: string | null;
}

export interface Photo {
  id: string;
  url: string;
  thumbnail_url: string | null;
  position: number;
  is_profile_photo: boolean;
  verification_status: PhotoVerificationStatus;
  visibility: PhotoVisibility;
  uploaded_at: string | null;
}

export interface PhotoUploadUrl {
  upload_url: string;
  object_key: string;
  expires_in: number;
}

export interface PreferenceItem {
  value: string;
  level: string;
}

export interface PartnerPreferences {
  age_min: number | null;
  age_max: number | null;
  height_min_cm: number | null;
  height_max_cm: number | null;
  preferred_marital_status: string | null;
  preferred_physical_status: string | null;
  preferred_family_values: string | null;
  preferred_education: string | null;
  preferred_employed_in: string | null;
  preferred_religions: PreferenceItem[];
  preferred_castes: PreferenceItem[];
  preferred_languages: PreferenceItem[];
  preferred_countries: PreferenceItem[];
  preferred_states: PreferenceItem[];
  preferred_diets: PreferenceItem[];
}

export interface Family {
  id: string;
  user_id: string;
  family_type: string | null;
  family_values: string | null;
  about_family: string | null;
  family_location: string | null;
}

export interface FamilyMember {
  id: string;
  relationship: string;
  name: string | null;
  occupation: string | null;
  education: string | null;
  marital_status: string | null;
}

export interface Astrology {
  id: string;
  user_id: string;
  time_of_birth: string | null;
  place_of_birth: string | null;
  rashi: string | null;
  nakshatra: string | null;
  gothram: string | null;
  dosham: string | null;
  horoscope_verified: boolean;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: Record<string, unknown>;
}

export type { ApiError };
