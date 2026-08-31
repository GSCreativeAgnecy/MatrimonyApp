import { apiRequest } from './client';
import { RemoteConfig } from '../types/remoteConfig';

/**
 * Public, unauthenticated app configuration endpoint.
 * Response: `{ data: { branding, app, features, limits, pricing, versions, legal, support }, meta: { version } }`
 */
export const appConfigApi = {
  getPublic(): Promise<RemoteConfig> {
    return apiRequest<{ data: Record<string, unknown>; meta: Record<string, unknown> }>('/app/config', {
      auth: false,
    }).then((res) => {
      const data = res.data ?? {};
      const version = (res.meta?.version as string | undefined) ?? '';
      return { ...data, version } as unknown as RemoteConfig;
    });
  },
};
