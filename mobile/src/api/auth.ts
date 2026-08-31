import { apiRequest } from './client';
import { AuthTokens, UserAccount } from '../types/models';

export interface RegisterPayload {
  email?: string;
  phone_number?: string;
  password: string;
}

export interface LoginPayload {
  email?: string;
  phone_number?: string;
  password: string;
}

export interface MfaRequired {
  requires_2fa: boolean;
  mfa_token: string;
  expires_in: number;
}

export const authApi = {
  register(payload: RegisterPayload) {
    return apiRequest<{ data: AuthTokens }>('/auth/register', {
      method: 'POST',
      body: payload,
      auth: false,
    }).then((res) => res.data);
  },

  login(payload: LoginPayload) {
    return apiRequest<{ data: AuthTokens | MfaRequired }>('/auth/login', {
      method: 'POST',
      body: payload,
      auth: false,
    }).then((res) => res.data);
  },

  totpVerify(mfaToken: string, code: string) {
    return apiRequest<{ data: AuthTokens }>('/auth/totp/verify', {
      method: 'POST',
      body: { mfa_token: mfaToken, code },
      auth: false,
    }).then((res) => res.data);
  },

  me() {
    return apiRequest<{ data: UserAccount }>('/auth/me').then((res) => res.data);
  },

  forgotPassword(email?: string, phone_number?: string) {
    return apiRequest<{ data: { status: string } }>('/auth/forgot-password', {
      method: 'POST',
      body: { email, phone_number },
      auth: false,
    }).then((res) => res.data);
  },

  resetPassword(token: string, newPassword: string) {
    return apiRequest<{ data: { status: string } }>('/auth/reset-password', {
      method: 'POST',
      body: { token, new_password: newPassword },
      auth: false,
    }).then((res) => res.data);
  },
};
