import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { chatApi } from '../../api/chat';
import { queryKeys } from '../../query/keys';
import { Message } from '../../types/models';

export function useConversations() {
  return useQuery({
    queryKey: queryKeys.chat.conversations,
    queryFn: () => chatApi.listConversations(),
  });
}

export function useMessages(conversationId: string) {
  return useInfiniteQuery({
    queryKey: queryKeys.chat.messages(conversationId),
    enabled: Boolean(conversationId),
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) => chatApi.listMessages(conversationId, 50, pageParam),
    getNextPageParam: (lastPage) => (lastPage.length >= 50 ? lastPage[lastPage.length - 1].id : undefined),
  });
}

export function useSendMessage(conversationId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => chatApi.sendMessage(conversationId, { message_type: 'TEXT', body }),
    onMutate: async (body) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.chat.messages(conversationId) });
      const previous = queryClient.getQueryData<{ pages: Message[][]; pageParams: unknown[] }>(
        queryKeys.chat.messages(conversationId),
      );
      // Optimistic bubble.
      const optimistic: Message = {
        id: `temp-${Date.now()}`,
        conversation_id: conversationId,
        sender_id: 'me',
        message_type: 'TEXT',
        body,
        media_url: null,
        created_at: new Date().toISOString(),
        read_at: null,
      };
      queryClient.setQueryData(queryKeys.chat.messages(conversationId), {
        ...(previous ?? { pages: [[]], pageParams: [] }),
        pages: previous ? [...previous.pages, [optimistic]] : [[optimistic]],
      });
      return { previous };
    },
    onError: (_err, _var, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.chat.messages(conversationId), context.previous);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.messages(conversationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.conversations });
    },
  });
}

export function useStartConversation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => chatApi.startConversation(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.chat.conversations });
    },
  });
}
