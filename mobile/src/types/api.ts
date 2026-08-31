/**
 * API layer contracts.
 *
 * The backend always responds with either:
 *   { "data": ..., "meta": {...} }
 * or an error envelope:
 *   { "error": { "code": "...", "message": "...", "details": {...} } }
 *
 * All error paths in the app consume `ApiError`. Never render raw responses.
 */
export interface ApiSuccess<T> {
  data: T;
  meta: Record<string, unknown>;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;

  constructor(message: string, code: string, status: number, details?: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }

  get isNetworkError(): boolean {
    return this.code === 'NETWORK_ERROR';
  }

  /** Codes the app maps to a premium upgrade flow (see backend monetization rules). */
  get isPremiumGated(): boolean {
    return ['PREMIUM_REQUIRED', 'MESSAGE_LIMIT_REACHED', 'UPGRADE_REQUIRED'].includes(this.code);
  }

  get isUnauthorized(): boolean {
    return this.status === 401;
  }
}

/** Known backend error codes surfaced by the app (from app/api/errors.py + services). */
export const ERROR_CODES = {
  UNAUTHORIZED: 'UNAUTHORIZED',
  TOKEN_REVOKED: 'TOKEN_REVOKED',
  FORBIDDEN: 'FORBIDDEN',
  NOT_FOUND: 'NOT_FOUND',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',
  CONFLICT: 'CONFLICT',
  DUPLICATE_SWIPE: 'DUPLICATE_SWIPE',
  ALREADY_MATCHED: 'ALREADY_MATCHED',
  NOT_MATCHED: 'NOT_MATCHED',
  BLOCKED: 'BLOCKED',
  USER_NOT_FOUND: 'USER_NOT_FOUND',
  USER_BANNED: 'USER_BANNED',
  USER_UNAVAILABLE: 'USER_UNAVAILABLE',
  SELF_SWIPE: 'SELF_SWIPE',
  PROFILE_NOT_FOUND: 'PROFILE_NOT_FOUND',
  CONVERSATION_NOT_FOUND: 'CONVERSATION_NOT_FOUND',
  PHOTO_NOT_FOUND: 'PHOTO_NOT_FOUND',
  PLAN_NOT_FOUND: 'PLAN_NOT_FOUND',
  PREMIUM_REQUIRED: 'PREMIUM_REQUIRED',
  MESSAGE_LIMIT_REACHED: 'MESSAGE_LIMIT_REACHED',
  UPGRADE_REQUIRED: 'UPGRADE_REQUIRED',
  CONFIG_KEY_EXISTS: 'CONFIG_KEY_EXISTS',
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  NETWORK_ERROR: 'NETWORK_ERROR',
} as const;
