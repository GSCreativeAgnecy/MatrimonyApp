import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { alertsApi } from '../../api/alerts';
import { queryKeys } from '../../query/keys';

export function useNotifications() {
  return useQuery({
    queryKey: queryKeys.alerts.list,
    queryFn: () => alertsApi.list(50, 0),
  });
}

export function useUnreadCount() {
  return useQuery({
    queryKey: queryKeys.alerts.unread,
    queryFn: () => alertsApi.unreadCount(),
    refetchInterval: 30_000,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => alertsApi.markRead(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.list });
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.unread });
    },
  });
}

export function useMarkAllRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => alertsApi.markAllRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.list });
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.unread });
    },
  });
}
