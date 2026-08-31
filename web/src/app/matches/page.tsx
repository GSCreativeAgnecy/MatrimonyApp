"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Heart } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { RequireAuth } from "@/components/require-auth";
import { apiFetch , photoUrl } from "@/lib/api";
import type { ApiEnvelope, MatchResponse } from "@/lib/types";

export default function MatchesPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["matches"],
    queryFn: () => apiFetch<ApiEnvelope<MatchResponse[]>>("/matches"),
  });

  const matches = data?.data ?? [];

  return (
    <RequireAuth>
      <AppShell>
        <h1 className="mb-4 text-xl font-bold">Your matches</h1>

        {isLoading && (
          <div className="flex h-48 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-primary" />
          </div>
        )}

        {isError && <p className="text-sm text-red-600">{(error as any)?.message || "Could not load matches."}</p>}

        {!isLoading && matches.length === 0 && (
          <div className="text-center text-gray-500">No matches yet. Keep swiping!</div>
        )}

        <div className="grid grid-cols-2 gap-3">
          {matches.map((m) => (
            <Link key={m.id} href={`/profile/${m.user_id}`} className="block">
              <div className="overflow-hidden rounded-2xl border border-gray-200 bg-white">
                <div className="aspect-square w-full bg-gray-200">
                  {m.profile_photo ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={photoUrl(m.profile_photo)} alt={m.first_name || "match"} className="h-full w-full object-cover" />
                  ) : (
                    <div className="flex h-full items-center justify-center text-4xl text-gray-300">
                      <Heart />
                    </div>
                  )}
                </div>
                <div className="p-3">
                  <p className="font-semibold">
                    {m.first_name || "Member"}
                    {m.age ? `, ${m.age}` : ""}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(m.city || m.state || m.occupation || "")}
                  </p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </AppShell>
    </RequireAuth>
  );
}