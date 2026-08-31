// Types mirroring backend schemas (app/schemas).

export interface ApiEnvelope<T> {
  data: T;
  meta: Record<string, any>;
}

export interface ApiErrorBody {
  error?: { code: string; message: string; details?: Record<string, any> };
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface MfaRequiredResponse {
  requires_2fa: boolean;
  mfa_token: string;
  expires_in: number;
}

export interface UserAccount {
  id: string;
  email?: string | null;
  phone_number?: string | null;
  account_status: string;
  role: string;
  is_banned: boolean;
  email_verified: boolean;
  phone_verified: boolean;
  created_at?: string | null;
}

export interface PublicProfile {
  id: string;
  user_id: string;
  first_name?: string | null;
  gender?: string | null;
  age?: number | null;
  marital_status?: string | null;
  religion?: string | null;
  caste?: string | null;
  mother_tongue?: string | null;
  education?: string | null;
  occupation?: string | null;
  job_title?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  distance_km?: number | null;
  bio?: string | null;
  intent?: string | null;
  diet?: string | null;
  drinking?: string | null;
  smoking?: string | null;
  height_cm?: number | null;
  body_type?: string | null;
  profile_photo?: string | null;
  last_seen?: string | null;
  is_online: boolean;
  is_verified_photo: boolean;
  is_verified_job: boolean;
}

export interface RecommendationItem {
  candidate_user_id: string;
  score: number;
  reason_codes: string[];
}

export interface RecommendationFeed {
  items: RecommendationItem[];
  next_cursor?: string | null;
  has_more: boolean;
}

export interface SwipeResponse {
  id: string;
  from_user_id: string;
  to_user_id: string;
  action: string;
  created_at: string;
  match_created: boolean;
  match_id?: string | null;
}

export interface MatchResponse {
  id: string;
  user_id: string;
  first_name?: string | null;
  age?: number | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  occupation?: string | null;
  profile_photo?: string | null;
  status: string;
  matched_at?: string | null;
}

export interface Conversation {
  id: string;
  other_user_id: string;
  other_user_name?: string | null;
  other_user_photo?: string | null;
  last_message_preview?: string | null;
  last_message_at?: string | null;
  unread_count: number;
}

export interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  message_type: string;
  body?: string | null;
  media_url?: string | null;
  created_at: string;
  read_at?: string | null;
}

export interface Photo {
  id: string;
  url: string;
  thumbnail_url?: string | null;
  position: number;
  is_profile_photo: boolean;
  verification_status: string;
  visibility: string;
  uploaded_at?: string | null;
}

export interface OwnProfile {
  id: string;
  user_id: string;
  first_name?: string | null;
  last_name?: string | null;
  date_of_birth?: string | null;
  gender?: string | null;
  bio?: string | null;
  intent?: string | null;
  marital_status?: string | null;
  height_cm?: number | null;
  mother_tongue?: string | null;
  religion?: string | null;
  caste?: string | null;
  education?: string | null;
  occupation?: string | null;
  job_title?: string | null;
  city?: string | null;
  state?: string | null;
  country?: string | null;
  profilePhoto?: string | null;
}