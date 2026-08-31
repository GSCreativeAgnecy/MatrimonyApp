import { apiRequest } from './client';
import {
  MatchedProfile,
  MatchItem,
  PublicProfile,
  RecommendationFeed,
  SwipeResult,
} from '../types/models';

export const matchesApi = {
  /** Recommendation feed — returns candidate IDs + scores; profiles are fetched individually. */
  getFeed(limit = 20, cursor?: string | null): Promise<RecommendationFeed> {
    return apiRequest<{ data: RecommendationFeed }>('/recommendations', {
      query: { limit, cursor: cursor ?? undefined },
    }).then((res) => res.data);
  },

  /** Full public (or matched) profile for a candidate. */
  getProfile(userId: string): Promise<PublicProfile | MatchedProfile> {
    return apiRequest<{ data: PublicProfile | MatchedProfile }>(`/profiles/${userId}`).then((res) => res.data);
  },

  /** Contact details — only available when matched. */
  getContact(userId: string): Promise<MatchedProfile> {
    return apiRequest<{ data: MatchedProfile }>(`/profiles/${userId}/contact`).then((res) => res.data);
  },

  swipe(targetUserId: string, action: 'LIKE' | 'PASS' | 'SUPER_LIKE'): Promise<SwipeResult> {
    return apiRequest<{ data: SwipeResult }>('/swipes', {
      method: 'POST',
      body: { target_user_id: targetUserId, action },
    }).then((res) => res.data);
  },

  listMatches(): Promise<MatchItem[]> {
    return apiRequest<{ data: MatchItem[] }>('/matches').then((res) => res.data);
  },

  unmatch(matchId: string): Promise<{ status: string }> {
    return apiRequest<{ data: { status: string } }>(`/matches/${matchId}`, { method: 'DELETE' }).then(
      (res) => res.data,
    );
  },
};
