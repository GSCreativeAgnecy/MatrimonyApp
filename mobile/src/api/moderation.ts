import { apiRequest } from './client';

export const moderationApi = {
  block(userId: string): Promise<{ id: string; blocked_user_id: string }> {
    return apiRequest<{ data: { id: string; blocked_user_id: string } }>(`/blocks/${userId}`, {
      method: 'POST',
    }).then((res) => res.data);
  },

  unblock(userId: string): Promise<{ status: string }> {
    return apiRequest<{ data: { status: string } }>(`/blocks/${userId}`, { method: 'DELETE' }).then((res) => res.data);
  },

  report(userId: string, reason: string, description?: string) {
    return apiRequest<{ data: unknown }>('/reports', {
      method: 'POST',
      body: { reported_user_id: userId, reason, description },
    }).then((res) => res.data);
  },
};
