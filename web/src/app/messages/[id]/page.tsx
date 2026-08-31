"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import { useState, FormEvent, useEffect, useRef } from "react";
import { ArrowLeft, Send } from "lucide-react";
import { AppShell } from "@/components/app-shell";
import { RequireAuth } from "@/components/require-auth";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api";
import type { ApiEnvelope, Message } from "@/lib/types";

export default function ChatPage() {
  const params = useParams<{ id: string }>();
  const conversationId = params.id;
  const router = useRouter();
  const qc = useQueryClient();
  const [draft, setDraft] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ["messages", conversationId],
    queryFn: () => apiFetch<ApiEnvelope<Message[]>>(`/messages/conversations/${conversationId}/messages`),
    enabled: !!conversationId,
    refetchInterval: 5000,
  });

  const send = useMutation({
    mutationFn: () =>
      apiFetch<ApiEnvelope<Message>>(`/messages/conversations/${conversationId}/messages`, {
        method: "POST",
        body: JSON.stringify({ message_type: "text", body: draft }),
      }),
    onSuccess: () => {
      setDraft("");
      qc.invalidateQueries({ queryKey: ["messages", conversationId] });
    },
  });

  // Resolve current user id to style my own messages.
  const { data: me } = useQuery({
    queryKey: ["me"],
    queryFn: () => apiFetch<ApiEnvelope<{ id: string }>>("/auth/me"),
  });
  const myId = me?.data?.id ?? "";

  const messages = data?.data ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!draft.trim()) return;
    send.mutate();
  }

  return (
    <RequireAuth>
      <AppShell>
        <button onClick={() => router.back()} className="mb-3 flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700">
          <ArrowLeft size={16} /> Back
        </button>

        <div className="flex h-[60vh] flex-col rounded-2xl border border-gray-200 bg-white">
          <div className="flex-1 space-y-2 overflow-y-auto p-4">
            {isLoading && <p className="text-center text-sm text-gray-400">Loading messages…</p>}
            {error && <p className="text-center text-sm text-red-600">{(error as any)?.message}</p>}
            {!isLoading && messages.length === 0 && (
              <p className="text-center text-sm text-gray-400">No messages yet. Say hello!</p>
            )}
            {messages.map((m) => (
              <MessageBubble key={m.id} message={m} myId={myId} />
            ))}
            <div ref={bottomRef} />
          </div>

          <form onSubmit={onSubmit} className="flex items-center gap-2 border-t border-gray-200 p-3">
            <input
              className="flex-1 rounded-xl border border-gray-300 px-3 py-2 text-sm outline-none focus:border-primary"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder="Type a message…"
            />
            <Button type="submit" disabled={!draft.trim() || send.isPending} className="px-3">
              <Send size={18} />
            </Button>
          </form>
        </div>
      </AppShell>
    </RequireAuth>
  );
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
function MessageBubble({ message, myId }: { message: Message; myId: string }) {
  const mine = myId === message.sender_id;
  return (
    <div className={mine ? "flex justify-end" : "flex justify-start"}>
      <div
        className={
          mine
            ? "max-w-[75%] rounded-2xl rounded-br-sm bg-primary px-3 py-2 text-sm text-white"
            : "max-w-[75%] rounded-2xl rounded-bl-sm bg-gray-100 px-3 py-2 text-sm text-gray-800"
        }
      >
        {message.body}
        <div className={"mt-0.5 text-[10px] " + (mine ? "text-white/70" : "text-gray-400")}>
          {new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </div>
      </div>
    </div>
  );
}