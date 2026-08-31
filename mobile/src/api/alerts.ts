import { apiRequest } from './client';
import { AppNotification } from '../types/models';

export const alertsApi = {
  list(limit = 50, offset = 0): Promise<AppNotification[]> {
    return apiRequest<{ data: AppNotification[] }>('/notifications', {
      query: { limit, offset },
    }).then((res) => res.data);
  },

  unreadCount(): Promise<number> {
    return apiRequest<{ data: { count: number } }>('/notifications/unread-count').then((res) => res.data.count);
  },

  markRead(id: string): Promise<{ status: string }> {
    return apiRequest<{ data: { status: string } }>(`/notifications/${id}/read`, { method: 'POST' }).then(
      (res) => res.data,
    );
  },

  markAllRead(): Promise<{ status: string; count: number }> {
    return apiRequest<{ data: { status: string; count: number } }>('/notifications/read-all', {
      method: 'POST',
    }).then((res) => res.data);
  },
};
