import { NextRequest, NextResponse } from "next/server";

import { API_PREFIX, COOKIE_NAME, cookieOptions, readJson, rejectCrossOrigin, serverApiUrl } from "@/lib/bff";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const csrf = rejectCrossOrigin(request);
  if (csrf) return csrf;

  const payload = await readJson(request);
  if (!payload) {
    return NextResponse.json({ error: { code: "VALIDATION", message: "Invalid body" } }, { status: 422 });
  }

  const resp = await fetch(`${serverApiUrl()}${API_PREFIX}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: payload.email, password: payload.password }),
  });
  const body = await resp.json();

  if (!resp.ok) {
    return NextResponse.json(body, { status: resp.status });
  }

  const data = body.data ?? {};

  // Two-factor required: hand the short-lived mfa token back; nothing stored yet.
  if (data.requires_2fa) {
    return NextResponse.json({
      data: { requires_2fa: true, mfa_token: data.mfa_token, expires_in: data.expires_in },
    });
  }

  const response = NextResponse.json({
    data: { access_token: data.access_token, expires_in: data.expires_in },
  });
  const refreshMaxAge: number = data.refresh_expires_in ?? 60 * 60 * 24 * 30;
  response.cookies.set(COOKIE_NAME, data.refresh_token, cookieOptions(refreshMaxAge));
  return response;
}
