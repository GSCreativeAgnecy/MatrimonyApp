"use client";

import { useCallback, useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Heart, X, Star, ThumbsUp, MapPin, Briefcase, GraduationCap } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { apiFetch , photoUrl } from "@/lib/api";
import type { ApiEnvelope, PublicProfile, RecommendationFeed, SwipeResponse } from "@/lib/types";

export default function DiscoverPage() {
  const router = useRouter();
  const [queue, setQueue] = useState<PublicProfile[]>([]);
  const [loadingFeed, setLoadingFeed] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFeed = useCallback(async () => {
    try {
      const res = await apiFetch<ApiEnvelope<RecommendationFeed>>("/recommendations");
      const items = res.data.items;
      if (items.length === 0) {
        setQueue([]);
        return;
      }
      // Resolve each candidate into a public profile.
      const profiles = await Promise.all(
        items.slice(0, 20).map(async (it) => {
          try {
            const p = await apiFetch<ApiEnvelope<PublicProfile>>(`/profiles/${it.candidate_user_id}`);
            return p.data;
          } catch {
            return null;
          }
        }),
      );
      setQueue(profiles.filter((p): p is PublicProfile => !!p));
    } catch (e: any) {
      setError(e?.message || "Could not load recommendations.");
    } finally {
      setLoadingFeed(false);
    }
  }, []);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  const swipe = useMutation({
    mutationFn: (action: "like" | "pass" | "super_like") =>
      apiFetch<ApiEnvelope<SwipeResponse>>("/swipes", {
        method: "POST",
        body: JSON.stringify({ target_user_id: current?.user_id, action }),
      }),
    onSuccess: (res) => {
      setQueue((q) => q.slice(1));
      if (res.data.match_created) {
        router.push("/matches");
      }
    },
    onError: (e: any) => setError(e?.message || "Swipe failed."),
  });

  const current = queue[0];

  function doSwipe(action: "like" | "pass" | "super_like") {
    if (!current) return;
    swipe.mutate(action);
  }

  return (
    <RequireAuth>
      <AppShell>
        <h1 className="mb-4 text-xl font-bold">Discover</h1>
        {error && <p className="mb-3 text-sm text-red-600">{error}</p>}

        {loadingFeed && (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-primary" />
          </div>
        )}

        {!loadingFeed && queue.length === 0 && (
          <Card className="p-8 text-center">
            <p className="text-gray-500">No candidates right now. Check back later or expand your preferences.</p>
          </Card>
        )}

        {current && (
          <Card className="overflow-hidden">
            <div className="aspect-[4/5] w-full bg-gray-200">
              {current.profile_photo ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={photoUrl(current.profile_photo)} alt={current.first_name || "profile"} className="h-full w-full object-cover" />
              ) : (
                <div className="flex h-full items-center justify-center text-gray-400">
                  <span className="text-5xl">{current.gender === "female" ? "👩" : "👨"}</span>
                </div>
              )}
            </div>
            <div className="p-4">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold">
                  {current.first_name || "Member"}
                  {current.age ? <span className="font-normal text-gray-500">, {current.age}</span> : null}
                </h2>
                {current.is_verified_photo && <span className="text-xs text-green-600">✓ Verified</span>}
              </div>

              <div className="mt-2 space-y-1 text-sm text-gray-600">
                {current.occupation && (
                  <p className="flex items-center gap-2">
                    <Briefcase size={15} /> {current.occupation}
                    {current.job_title ? ` · ${current.job_title}` : ""}
                  </p>
                )}
                {current.education && (
                  <p className="flex items-center gap-2">
                    <GraduationCap size={15} /> {current.education}
                  </p>
                )}
                {(current.city || current.state || current.country) && (
                  <p className="flex items-center gap-2">
                    <MapPin size={15} />{[current.city, current.state, current.country].filter(Boolean).join(", ")}
                  </p>
                )}
              </div>

              <div className="mt-2 flex flex-wrap gap-1 text-xs">
                {current.marital_status && <Tag>{current.marital_status}</Tag>}
                {current.religion && <Tag>{current.religion}</Tag>}
                {current.caste && <Tag>{current.caste}</Tag>}
                {current.mother_tongue && <Tag>{current.mother_tongue}</Tag>}
                {current.intent && <Tag>{current.intent}</Tag>}
              </div>
            </div>

            <div className="flex items-center justify-center gap-3 p-4 pt-0">
              <Button variant="outline" size="lg" onClick={() => doSwipe("pass")} aria-label="Pass">
                <X className="text-red-500" size={24} />
              </Button>
              <Button size="lg" onClick={() => doSwipe("super_like")} aria-label="Super like" className="h-14 w-14 rounded-full bg-amber-400 hover:bg-amber-500 p-0">
                <Star size={24} />
              </Button>
              <Button variant="outline" size="lg" onClick={() => doSwipe("like")} aria-label="Like">
                <Heart className="text-green-500" size={24} />
              </Button>
            </div>
          </Card>
        )}
      </AppShell>
    </RequireAuth>
  );
}

function Tag({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full bg-gray-100 px-2 py-0.5 text-gray-600">{children}</span>;
}