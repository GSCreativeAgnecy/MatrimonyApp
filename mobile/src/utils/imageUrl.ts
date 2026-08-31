import { Platform } from 'react-native';

import { API_BASE_URL } from '../config/env';

/**
 * Normalize an image URL returned by the backend.
 *
 * The backend can return either a full presigned/public URL or, for some
 * responses (own profile photo, matches list), a raw storage object key. When
 * running with the LOCAL storage backend the files are served from
 * `/static/{key}` on the API host — so we synthesize that URL. In production
 * with S3 the backend always returns real URLs.
 */
export function imageUrl(url: string | null | undefined): string | null {
  if (!url) {
    return null;
  }
  if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('data:')) {
    return url;
  }
  if (url.startsWith('/static/')) {
    return `${API_BASE_URL}${url}`;
  }
  // Raw object key under the local dev storage backend.
  if (Platform.OS !== 'web') {
    return `${API_BASE_URL}/static/${url.replace(/^\/+/, '')}`;
  }
  return `${API_BASE_URL}/static/${url.replace(/^\/+/, '')}`;
}
