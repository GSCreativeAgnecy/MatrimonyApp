import * as ImagePicker from 'expo-image-picker';
import React, { useState } from 'react';
import { Image, Pressable, StyleSheet, View } from 'react-native';

import { AppText } from '../../components/AppText';
import { AppIcon } from '../../components/AppIcon';
import { AppButton } from '../../components/AppButton';
import { AppHeader } from '../../components/AppHeader';
import { Modal } from '../../components/Modal';
import { ScreenContainer } from '../../components/ScreenContainer';
import { LoadingState } from '../../components/LoadingState';
import { EmptyState } from '../../components/EmptyState';
import { ErrorState } from '../../components/ErrorState';
import { useTheme } from '../../theme/ThemeProvider';
import { useRemoteConfig } from '../../config/RemoteConfigProvider';
import { photosApi } from '../../api/photos';
import { uploadFileToUrl } from '../../utils/upload';
import { useQueryClient } from '@tanstack/react-query';
import { queryKeys } from '../../query/keys';
import { usePhotos } from './hooks';
import { imageUrl } from '../../utils/imageUrl';
import { Photo } from '../../types/models';

const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/heic'];

export function PhotosScreen() {
  const { colors, spacing } = useTheme();
  const { config } = useRemoteConfig();
  const queryClient = useQueryClient();

  const { data: photos, isLoading, error, refetch } = usePhotos();
  const maxPhotos = config.limits.max_photos;

  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [confirmPhoto, setConfirmPhoto] = useState<Photo | null>(null);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.profile.photos });
    queryClient.invalidateQueries({ queryKey: queryKeys.profile.mine });
  };

  const pickAndUpload = async () => {
    if (uploading) return;
    setUploadError(null);

    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setUploadError('Photo library permission is required to add photos.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ['images'],
      allowsEditing: true,
      aspect: [3, 4],
      quality: 0.85,
    });

    if (result.canceled || result.assets.length === 0) {
      return;
    }

    const asset = result.assets[0];
    const mime = asset.mimeType && ALLOWED_TYPES.includes(asset.mimeType) ? asset.mimeType : 'image/jpeg';
    const filename = asset.fileName ?? `photo-${Date.now()}.jpg`;

    setUploading(true);
    setProgress(0);
    try {
      const upload = await photosApi.requestUploadUrl(filename, mime);
      await uploadFileToUrl(asset.uri, mime, upload.upload_url, ({ loaded, total }) => {
        setProgress(total > 0 ? Math.round((loaded / total) * 100) : 0);
      });
      const photo = await photosApi.confirmUpload(upload.object_key, mime);
      invalidate();
      setConfirmPhoto(photo);
    } catch (e) {
      setUploadError(e instanceof Error ? 'Upload failed. Please try again.' : 'Upload failed. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const setPrimary = async (photo: Photo) => {
    try {
      await photosApi.update(photo.id, { is_profile_photo: true });
      invalidate();
    } catch {
      setUploadError('Could not update the primary photo.');
    }
  };

  const deletePhoto = async (photo: Photo) => {
    try {
      await photosApi.delete(photo.id);
      invalidate();
    } catch {
      setUploadError('Could not delete the photo.');
    }
  };

  const move = async (photo: Photo, direction: -1 | 1) => {
    if (!photos) return;
    const index = photos.findIndex((p) => p.id === photo.id);
    const target = index + direction;
    if (target < 0 || target >= photos.length) return;
    const other = photos[target];
    try {
      await Promise.all([
        photosApi.update(photo.id, { position: other.position }),
        photosApi.update(other.id, { position: photo.position }),
      ]);
      invalidate();
    } catch {
      setUploadError('Could not reorder photos.');
    }
  };

  if (isLoading) {
    return <ScreenContainer><LoadingState message="Loading your photos…" /></ScreenContainer>;
  }
  if (error) {
    return (
      <ScreenContainer>
        <AppHeader title="Photos" showBack />
        <ErrorState onRetry={refetch} />
      </ScreenContainer>
    );
  }

  const list = photos ?? [];
  const canAdd = list.length < maxPhotos;

  return (
    <ScreenContainer scroll>
      <AppHeader title="My Photos" showBack />

      {uploadError ? <ErrorState compact message={uploadError} /> : null}

      {uploading ? (
        <View style={[styles.progressCard, { backgroundColor: colors.surface, borderRadius: 16, padding: spacing.lg }]}>
          <AppText variant="label">Uploading photo… {progress}%</AppText>
          <View style={[styles.progressTrack, { backgroundColor: colors.border, borderRadius: 4, marginTop: spacing.sm }]}>
            <View style={[styles.progressFill, { backgroundColor: colors.primary, width: `${progress}%` }]} />
          </View>
        </View>
      ) : null}

      {list.length === 0 && !uploading ? (
        <EmptyState
          icon="images-outline"
          title="No photos yet"
          message="Add photos to let potential matches see you. Your first photo becomes your profile picture."
        >
          <AppButton title="Add Photo" onPress={pickAndUpload} />
        </EmptyState>
      ) : (
        <View style={styles.grid}>
          {list.map((photo) => {
            const uri = imageUrl(photo.url);
            return (
              <View key={photo.id} style={[styles.photoWrap, { backgroundColor: colors.surface, borderRadius: 16 }]}>
                {uri ? (
                  <Image source={{ uri }} style={styles.photo} />
                ) : (
                  <View style={[styles.photo, styles.fallback, { backgroundColor: colors.secondary }]}>
                    <AppIcon name="image-outline" size={32} color={colors.textSecondary} />
                  </View>
                )}
                {photo.is_profile_photo ? (
                  <View style={[styles.primaryBadge, { backgroundColor: colors.primary, borderRadius: 10 }]}>
                    <AppText variant="caption" color={colors.textInverse} style={{ fontSize: 10, fontWeight: '700' }}>
                      PRIMARY
                    </AppText>
                  </View>
                ) : null}
                <View style={styles.photoActions}>
                  <IconButton icon="move-outline" onPress={() => move(photo, -1)} label="Move earlier" disabled={false} />
                  <IconButton icon="move-outline" onPress={() => move(photo, 1)} label="Move later" disabled={false} />
                  <IconButton
                    icon={photo.is_profile_photo ? 'star' : 'star-outline'}
                    onPress={() => setPrimary(photo)}
                    label="Set as primary"
                    accent
                  />
                  <IconButton icon="trash-outline" onPress={() => deletePhoto(photo)} label="Delete photo" danger />
                </View>
              </View>
            );
          })}
        </View>
      )}

      {list.length > 0 ? (
        <View style={{ marginTop: spacing.xl }}>
          <AppButton title={canAdd ? 'Add Photo' : `Maximum ${maxPhotos} photos reached`} onPress={pickAndUpload} disabled={!canAdd} loading={uploading} />
        </View>
      ) : null}

      <Modal
        visible={Boolean(confirmPhoto)}
        onClose={() => setConfirmPhoto(null)}
        title="Photo uploaded"
        message="Your photo has been added. Would you like to make it your primary photo?"
        actions={[
          { label: 'Make Primary', onPress: () => confirmPhoto && setPrimary(confirmPhoto) },
          { label: 'Not Now', onPress: () => undefined, variant: 'ghost' },
        ]}
      />
    </ScreenContainer>
  );
}

function IconButton({
  icon,
  label,
  onPress,
  danger = false,
  accent = false,
}: {
  icon: 'move-outline' | 'star' | 'star-outline' | 'trash-outline';
  label: string;
  onPress: () => void;
  danger?: boolean;
  accent?: boolean;
  disabled?: boolean;
}) {
  const { colors, spacing } = useTheme();
  const tint = danger ? colors.error : accent ? colors.accent : colors.primary;
  return (
    <Pressable onPress={onPress} hitSlop={6} accessibilityRole="button" accessibilityLabel={label} style={{ alignItems: 'center' }}>
      <AppIcon name={icon} size={18} color={tint} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  photoWrap: {
    width: '48.5%',
    marginBottom: 12,
    overflow: 'hidden',
    paddingBottom: 8,
  },
  photo: {
    width: '100%',
    aspectRatio: 3 / 3.4,
  },
  fallback: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  primaryBadge: {
    position: 'absolute',
    top: 8,
    left: 8,
    paddingHorizontal: 8,
    paddingVertical: 3,
  },
  photoActions: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    alignItems: 'center',
    paddingTop: 8,
  },
  progressCard: {
    marginBottom: 16,
  },
  progressTrack: {
    height: 6,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
  },
});
