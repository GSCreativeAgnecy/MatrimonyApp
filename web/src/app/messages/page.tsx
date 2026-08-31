"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { MessageCircle } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { RequireAuth } from "@/components/require-auth";
import { apiFetch , photoUrl } from "@/lib/api";
import type { ApiEnvelope, Conversation } from "@/lib/types";

export default function MessagesPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["conversations"],
    queryFn: () => apiFetch<ApiEnvelope<Conversation[]>>("/messages/conversations"),
  });

  const conversations = data?.data ?? [];

  return (
    <RequireAuth>
      <AppShell>
        <h1 className="mb-4 text-xl font-bold">Messages</h1>

        {isLoading && (
          <div className="flex h-48 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-primary" />
          </div>
        )}
        {error && <p className="text-sm text-red-600">{(error as any)?.message}</p>}

        {!isLoading && conversations.length === 0 && (
          <div className="py-12 text-center text-gray-500">
            <MessageCircle className="mx-auto mb-3 text-gray-300" size={40} />
            <p>No conversations yet.</p>
          </div>
        )}

        <div className="space-y-2">
          {conversations.map((c) => (
            <Link
              key={c.id}
              href={`/messages/${c.id}`}
              className="flex items-center gap-3 rounded-2xl border border-gray-200 bg-white p-3"
            >
              <div className="h-12 w-12 overflow-hidden rounded-full bg-gray-200">
                {c.other_user_photo ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={photoUrl(c.other_user_photo)} alt="" className="h-full w-full object-cover" />
                ) : (
                  <div className="flex h-full items-center justify-center text-gray-300">
                    <MessageCircle size={20} />
                  </div>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between">
                  <p className="font-semibold">{c.other_user_name || "Member"}</p>
                  {c.unread_count > 0 && (
                    <span className="rounded-full bg-primary px-2 py-0.5 text-xs text-white">{c.unread_count}</span>
                  )}
                </div>
                <p className="truncate text-sm text-gray-500">
                  {c.last_message_preview || "Start a conversation"}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </AppShell>
    </RequireAuth>
  );
}