import { apiRequest } from './client';
import { CheckoutResult, JobVerification, Subscription, SubscriptionPlan } from '../types/models';

export const subscriptionsApi = {
  listPlans(): Promise<SubscriptionPlan[]> {
    return apiRequest<{ data: SubscriptionPlan[] }>('/subscription/plans').then((res) => res.data);
  },

  mySubscription(): Promise<Subscription> {
    return apiRequest<{ data: Subscription }>('/subscription').then((res) => res.data);
  },

  checkout(planId: string): Promise<CheckoutResult> {
    return apiRequest<{ data: CheckoutResult }>('/subscription/checkout', {
      method: 'POST',
      body: { plan_id: planId },
    }).then((res) => res.data);
  },
};

export interface JobVerificationCheckoutResult {
  verification_id: string;
  checkout_url: string | null;
  payment_id: string;
  amount: number;
  currency: string;
}

export const verificationApi = {
  submitJob(payload: {
    employment_type: 'LOCAL' | 'NRI';
    employer_name: string;
    job_title?: string;
    country?: string;
  }): Promise<JobVerificationCheckoutResult> {
    return apiRequest<{ data: JobVerificationCheckoutResult }>('/verifications/job', {
      method: 'POST',
      body: payload,
    }).then((res) => res.data);
  },

  listMine(): Promise<JobVerification[]> {
    return apiRequest<{ data: JobVerification[] }>('/verifications').then((res) => res.data);
  },
};
