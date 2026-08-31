import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { subscriptionsApi, verificationApi } from '../../api/subscriptions';
import { queryKeys } from '../../query/keys';

export function usePlans() {
  return useQuery({
    queryKey: queryKeys.subscription.plans,
    queryFn: () => subscriptionsApi.listPlans(),
  });
}

export function useSubscription() {
  return useQuery({
    queryKey: queryKeys.subscription.mine,
    queryFn: () => subscriptionsApi.mySubscription(),
  });
}

export function useCheckout() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (planId: string) => subscriptionsApi.checkout(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.subscription.mine });
    },
  });
}

export function useMyVerifications() {
  return useQuery({
    queryKey: queryKeys.verification.mine,
    queryFn: () => verificationApi.listMine(),
  });
}
