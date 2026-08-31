export const queryKeys = {
  remoteConfig: ['remoteConfig'] as const,
  auth: {
    me: ['auth', 'me'] as const,
  },
  profile: {
    mine: ['profile', 'mine'] as const,
    photos: ['profile', 'photos'] as const,
    privacy: ['profile', 'privacy'] as const,
    preferences: ['profile', 'preferences'] as const,
    family: ['profile', 'family'] as const,
    familyMembers: ['profile', 'family', 'members'] as const,
    astrology: ['profile', 'astrology'] as const,
  },
  discovery: {
    feed: ['discovery', 'feed'] as const,
    profile: (userId: string) => ['discovery', 'profile', userId] as const,
  },
  matches: {
    list: ['matches', 'list'] as const,
  },
  chat: {
    conversations: ['chat', 'conversations'] as const,
    messages: (conversationId: string) => ['chat', 'messages', conversationId] as const,
  },
  alerts: {
    list: ['alerts', 'list'] as const,
    unread: ['alerts', 'unread'] as const,
  },
  subscription: {
    mine: ['subscription', 'mine'] as const,
    plans: ['subscription', 'plans'] as const,
  },
  verification: {
    mine: ['verification', 'mine'] as const,
  },
};
