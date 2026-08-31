import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { photosApi } from '../../api/photos';
import { preferencesApi, PreferencesUpdatePayload } from '../../api/preferences';
import { profileApi, ProfileUpdatePayload } from '../../api/profile';
import { queryKeys } from '../../query/keys';

export function useOwnProfile() {
  return useQuery({
    queryKey: queryKeys.profile.mine,
    queryFn: () => profileApi.getMine(),
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileUpdatePayload) => profileApi.update(payload),
    onSuccess: (profile) => {
      queryClient.setQueryData(queryKeys.profile.mine, profile);
      queryClient.invalidateQueries({ queryKey: queryKeys.profile.mine });
    },
  });
}

export function useCreateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: ProfileUpdatePayload) => profileApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile.mine });
    },
  });
}

export function usePhotos() {
  return useQuery({
    queryKey: queryKeys.profile.photos,
    queryFn: () => photosApi.list(),
  });
}

export function usePreferences() {
  return useQuery({
    queryKey: queryKeys.profile.preferences,
    queryFn: () => preferencesApi.get(),
  });
}

export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: PreferencesUpdatePayload) => preferencesApi.update(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.profile.preferences });
      queryClient.invalidateQueries({ queryKey: queryKeys.discovery.feed });
    },
  });
}
