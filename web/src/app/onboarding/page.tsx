"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { apiFetch } from "@/lib/api";
import type { ApiEnvelope, OwnProfile } from "@/lib/types";

export default function OnboardingPage() {
  const router = useRouter();
  const { logout } = useAuth();
  const [values, setValues] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const fields = [
    { key: "first_name", label: "First name", placeholder: "Your first name" },
    { key: "gender", label: "Gender", placeholder: "male / female" },
    { key: "date_of_birth", label: "Date of birth", placeholder: "YYYY-MM-DD", type: "date" },
    { key: "intent", label: "What are you looking for?", placeholder: "e.g. Marriage" },
    { key: "religion", label: "Religion", placeholder: "e.g. Hindu" },
    { key: "city", label: "City", placeholder: "City" },
    { key: "country", label: "Country", placeholder: "Country" },
  ];

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      await apiFetch<ApiEnvelope<OwnProfile>>("/profile", { method: "POST", body: JSON.stringify(values) });
      router.replace("/discover");
    } catch (err: any) {
      setError(err?.message || "Could not create your profile.");
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <div className="w-full max-w-md">
        <div className="mb-4 text-center">
          <h1 className="text-2xl font-bold text-primary">Welcome!</h1>
          <p className="text-gray-500">Tell us a little about yourself to get started.</p>
        </div>
        <form onSubmit={onSubmit} className="space-y-3 rounded-2xl border border-gray-200 bg-white p-6">
          {fields.map((f) => (
            <div key={f.key} className="space-y-1">
              <label className="text-sm font-medium" htmlFor={f.key}>
                {f.label}
              </label>
              <Input
                id={f.key}
                type={f.type || "text"}
                value={values[f.key] ?? ""}
                onChange={(e) => setValues((v) => ({ ...v, [f.key]: e.target.value }))}
                placeholder={f.placeholder}
                required={f.key === "first_name"}
              />
            </div>
          ))}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <Button type="submit" className="w-full" disabled={busy}>
            {busy ? "Saving…" : "Continue"}
          </Button>
          <button type="button" onClick={logout} className="w-full text-center text-xs text-gray-400 hover:text-gray-600">
            Sign out instead
          </button>
        </form>
      </div>
    </div>
  );
}