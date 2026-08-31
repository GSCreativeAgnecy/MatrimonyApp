import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient, useInfiniteQuery } from '@tanstack/react-query';

import { matchesApi } from '../../api/matches';
import { queryKeys } from '../../query/keys';
import { PublicProfile } from '../../types/models';

export function useFeed() {
  return useInfiniteQuery({
    queryKey: queryKeys.discovery.feed,
    initialPageParam: undefined as string | undefined,
    queryFn: ({ pageParam }) => matchesApi.getFeed(20, pageParam),
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.next_cursor : undefined),
  });
}

/**
 * Composes the recommendation feed (which returns only candidate IDs) with the
 * full public profiles fetched from the profiles endpoint.
 */
export function useFeedProfiles() {
  const feed = useFeed();
  const [profiles, setProfiles] = useState<Record<string, PublicProfile>>({});
  const [loadingProfiles, setLoadingProfiles] = useState(false);

  const items = useMemo(
    () => (feed.data?.pages ?? []).flatMap((page) => page.items ?? []),
    [feed.data],
  );

  useEffect(() => {
    const missing = items
      .map((item) => item.candidate_user_id)
      .filter((id) => !profiles[id]);

    if (missing.length === 0) {
      return;
    }

    let cancelled = false;
    setLoadingProfiles(true);

    Promise.all(missing.map((id) => matchesApi.getProfile(id).catch(() => null))).then((results) => {
      if (cancelled) {
        return;
      }
      setProfiles((prev) => {
        const next = { ...prev };
        results.forEach((profile, index) => {
          if (profile) {
            next[missing[index]] = profile;
          }
        });
        return next;
      });
      setLoadingProfiles(false);
    });

    return () => {
      cancelled = true;
    };
  }, [items, profiles]);

  return { feed, profiles, loadingProfiles };
}

export function usePublicProfile(userId: string) {
  return useQuery({
    queryKey: queryKeys.discovery.profile(userId),
    queryFn: () => matchesApi.getProfile(userId),
    enabled: Boolean(userId),
  });
}

export function useMatches() {
  return useQuery({
    queryKey: queryKeys.matches.list,
    queryFn: () => matchesApi.listMatches(),
  });
}

export function useSwipe() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, action }: { userId: string; action: 'LIKE' | 'PASS' | 'SUPER_LIKE' }) =>
      matchesApi.swipe(userId, action),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.discovery.feed });
      queryClient.invalidateQueries({ queryKey: queryKeys.matches.list });
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts.list });
    },
  });
}

export function useUnmatch() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (matchId: string) => matchesApi.unmatch(matchId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.matches.list });
    },
  });
}
