import { apiRequest } from './client';
import { Photo, PhotoUploadUrl } from '../types/models';

export const photosApi = {
  list(): Promise<Photo[]> {
    return apiRequest<{ data: Photo[] }>('/profile/photos').then((res) => res.data);
  },

  requestUploadUrl(filename: string, content_type: string): Promise<PhotoUploadUrl> {
    return apiRequest<{ data: PhotoUploadUrl }>('/profile/photos/upload-url', {
      method: 'POST',
      body: { filename, content_type },
    }).then((res) => res.data);
  },

  confirmUpload(objectKey: string, contentType?: string): Promise<Photo> {
    return apiRequest<{ data: Photo }>('/profile/photos/confirm', {
      method: 'POST',
      body: { object_key: objectKey, content_type: contentType },
    }).then((res) => res.data);
  },

  update(
    photoId: string,
    payload: { position?: number; is_profile_photo?: boolean; visibility?: string },
  ): Promise<Photo> {
    return apiRequest<{ data: Photo }>(`/profile/photos/${photoId}`, { method: 'PATCH', body: payload }).then(
      (res) => res.data,
    );
  },

  delete(photoId: string): Promise<{ status: string }> {
    return apiRequest<{ data: { status: string } }>(`/profile/photos/${photoId}`, { method: 'DELETE' }).then(
      (res) => res.data,
    );
  },
};
