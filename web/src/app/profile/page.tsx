"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, FormEvent } from "react";
import { AppShell } from "@/components/app-shell";
import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { apiFetch, photoUrl, uploadPhotoFile } from "@/lib/api";
import type { ApiEnvelope, OwnProfile, Photo } from "@/lib/types";

const TEXT_FIELDS: { key: keyof OwnProfile; label: string; placeholder: string }[] = [
  { key: "first_name", label: "First name", placeholder: "Your first name" },
  { key: "last_name", label: "Last name", placeholder: "Your last name" },
  { key: "gender", label: "Gender", placeholder: "male / female" },
  { key: "intent", label: "Intent", placeholder: "e.g. Marriage" },
  { key: "marital_status", label: "Marital status", placeholder: "e.g. Never Married" },
  { key: "religion", label: "Religion", placeholder: "e.g. Hindu" },
  { key: "caste", label: "Caste", placeholder: "e.g. Brahmin" },
  { key: "mother_tongue", label: "Mother tongue", placeholder: "e.g. Hindi" },
  { key: "education", label: "Education", placeholder: "e.g. B.Tech" },
  { key: "occupation", label: "Occupation", placeholder: "e.g. Software Engineer" },
  { key: "job_title", label: "Job title", placeholder: "e.g. Senior Engineer" },
  { key: "city", label: "City", placeholder: "City" },
  { key: "state", label: "State", placeholder: "State" },
  { key: "country", label: "Country", placeholder: "Country" },
];

export default function OwnProfilePage() {
  const qc = useQueryClient();
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [values, setValues] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState(false);
  const [photoError, setPhotoError] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["own-profile"],
    queryFn: async () => {
      const res = await apiFetch<ApiEnvelope<OwnProfile>>("/profile/me");
      if (res.data) setValues(pickFields(res.data));
      return res;
    },
  });
  const profile = data?.data;

  const photos = useQuery({
    queryKey: ["photos"],
    queryFn: () => apiFetch<ApiEnvelope<Photo[]>>("/profile/photos"),
  });

  function pickFields(p: OwnProfile): Record<string, string> {
    const out: Record<string, string> = {};
    for (const f of TEXT_FIELDS) out[f.key] = (p[f.key] as any) ?? "";
    return out;
  }

  const saveProfile = useMutation({
    mutationFn: () => apiFetch<ApiEnvelope<OwnProfile>>("/profile", { method: "PATCH", body: JSON.stringify(values) }),
    onSuccess: () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      qc.invalidateQueries({ queryKey: ["own-profile"] });
    },
    onError: (e: any) => setError(e?.message || "Failed to save profile."),
  });

  const createProfile = useMutation({
    mutationFn: () => apiFetch<ApiEnvelope<OwnProfile>>("/profile", { method: "POST", body: JSON.stringify(values) }),
    onSuccess: () => {
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
      qc.invalidateQueries({ queryKey: ["own-profile"] });
    },
    onError: (e: any) => setError(e?.message || "Failed to create profile."),
  });

  function set(field: string, val: string) {
    setValues((v) => ({ ...v, [field]: val }));
  }

  async function uploadPhoto(file: File) {
    setPhotoError(null);
    setUploading(true);
    try {
      await uploadPhotoFile(file);
      photos.refetch();
    } catch (e: any) {
      setPhotoError(e?.message || "Photo upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <RequireAuth>
      <AppShell>
        <h1 className="mb-4 text-xl font-bold">Your profile</h1>
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}
        {saved && <p className="mb-3 text-sm text-green-600">Saved.</p>}

        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
              <CardDescription>These fields power your discovery profile.</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex h-24 items-center justify-center">
                  <div className="h-7 w-7 animate-spin rounded-full border-2 border-gray-300 border-t-primary" />
                </div>
              ) : (
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {TEXT_FIELDS.map((f) => (
                    <div key={f.key} className="space-y-1">
                      <label className="text-xs font-medium text-gray-600">{f.label}</label>
                      <Input value={values[f.key] ?? ""} onChange={(e) => set(f.key, e.target.value)} placeholder={f.placeholder} />
                    </div>
                  ))}
                </div>
              )}
              <div className="mt-4 flex gap-2">
                {profile?.first_name ? (
                  <Button onClick={() => saveProfile.mutate()} disabled={saveProfile.isPending}>
                    Save
                  </Button>
                ) : (
                  <Button onClick={() => createProfile.mutate()} disabled={createProfile.isPending}>
                    Create profile
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          <PhotoSection photos={photos.data?.data ?? []} uploading={uploading} photoError={photoError} onUpload={uploadPhoto} />
        </div>
      </AppShell>
    </RequireAuth>
  );
}

function PhotoSection({
  photos,
  uploading,
  photoError,
  onUpload,
}: {
  photos: Photo[];
  uploading: boolean;
  photoError: string | null;
  onUpload: (f: File) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Photos</CardTitle>
        <CardDescription>Add photos to appear in discovery.</CardDescription>
      </CardHeader>
      <CardContent>
        {photoError && <p className="mb-2 text-sm text-red-600">{photoError}</p>}
        <div className="flex gap-3">
          {photos.map((p) => (
            <div key={p.id} className="h-24 w-24 overflow-hidden rounded-xl border border-gray-200">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={photoUrl(p.url)} alt="" className="h-full w-full object-cover" />
            </div>
          ))}
          <label className="flex h-24 w-24 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 text-xs text-gray-400 hover:border-primary">
            <span>{uploading ? "Uploading…" : "Add photo"}</span>
            <input type="file" accept="image/*" className="hidden" disabled={uploading} onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])} />
          </label>
        </div>
      </CardContent>
    </Card>
  );
}