import { apiRequest } from './client';
import { Conversation, Message } from '../types/models';

export const chatApi = {
  listConversations(): Promise<Conversation[]> {
    return apiRequest<{ data: Conversation[] }>('/conversations').then((res) => res.data);
  },

  startConversation(userId: string): Promise<Conversation> {
    return apiRequest<{ data: Conversation }>('/conversations', {
      method: 'POST',
      body: { user_id: userId },
    }).then((res) => res.data);
  },

  listMessages(conversationId: string, limit = 50, before?: string | null): Promise<Message[]> {
    return apiRequest<{ data: Message[] }>(`/conversations/${conversationId}/messages`, {
      query: { limit, before: before ?? undefined },
    }).then((res) => res.data);
  },

  sendMessage(
    conversationId: string,
    payload: { message_type?: string; body?: string; media_url?: string },
  ): Promise<Message> {
    return apiRequest<{ data: Message }>(`/conversations/${conversationId}/messages`, {
      method: 'POST',
      body: payload,
    }).then((res) => res.data);
  },

  markRead(conversationId: string): Promise<{ status: string }> {
    return apiRequest<{ data: { status: string } }>(`/conversations/${conversationId}/read`, {
      method: 'POST',
    }).then((res) => res.data);
  },
};
