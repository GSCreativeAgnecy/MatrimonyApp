"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { RequireAuth } from "@/components/require-auth";
import { apiFetch } from "@/lib/api";
import type { ApiEnvelope, PublicProfile } from "@/lib/types";
import { Briefcase, MapPin, GraduationCap } from "lucide-react";

export default function ProfileViewPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;

  const { data, isLoading, error } = useQuery({
    queryKey: ["profile", id],
    queryFn: () => apiFetch<ApiEnvelope<PublicProfile>>(`/profiles/${id}`),
    enabled: !!id,
  });

  const p = data?.data;

  return (
    <RequireAuth>
      <AppShell>
        {isLoading && (
          <div className="flex h-48 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-primary" />
          </div>
        )}
        {error && <p className="text-sm text-red-600">{(error as any)?.message}</p>}
        {p && (
          <div className="space-y-4">
            <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
              <div className="aspect-[4/5] w-full bg-gray-200">
                {p.profile_photo ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={p.profile_photo} alt={p.first_name || "profile"} className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-6xl text-gray-300">
                    {p.gender === "female" ? "👩" : "👨"}
                  </div>
                )}
              </div>
              <div className="p-4">
                <h1 className="text-2xl font-bold">
                  {p.first_name || "Member"}
                  {p.age ? `, ${p.age}` : ""}
                </h1>
                {p.bio && <p className="mt-2 text-gray-600">{p.bio}</p>}
                <div className="mt-3 space-y-1.5 text-sm text-gray-600">
                  {p.occupation && (
                    <p className="flex items-center gap-2">
                      <Briefcase size={15} /> {p.occupation}
                      {p.job_title ? ` · ${p.job_title}` : ""}
                    </p>
                  )}
                  {p.education && (
                    <p className="flex items-center gap-2">
                      <GraduationCap size={15} /> {p.education}
                    </p>
                  )}
                  {(p.city || p.state || p.country) && (
                    <p className="flex items-center gap-2">
                      <MapPin size={15} /> {[p.city, p.state, p.country].filter(Boolean).join(", ")}
                    </p>
                  )}
                </div>
                <div className="mt-3 flex flex-wrap gap-1.5 text-xs">
                  {p.marital_status && <Badge>{p.marital_status}</Badge>}
                  {p.religion && <Badge>{p.religion}</Badge>}
                  {p.caste && <Badge>{p.caste}</Badge>}
                  {p.mother_tongue && <Badge>{p.mother_tongue}</Badge>}
                  {p.height_cm && <Badge>{p.height_cm} cm</Badge>}
                  {p.intent && <Badge>{p.intent}</Badge>}
                </div>
              </div>
            </div>
          </div>
        )}
      </AppShell>
    </RequireAuth>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="rounded-full bg-gray-100 px-2.5 py-1 text-gray-600">{children}</span>;
}