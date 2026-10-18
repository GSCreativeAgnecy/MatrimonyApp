import { NextRequest, NextResponse } from "next/server";

import { API_PREFIX, COOKIE_NAME, cookieOptions, readJson, rejectCrossOrigin, serverApiUrl } from "@/lib/bff";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const csrf = rejectCrossOrigin(request);
  if (csrf) return csrf;

  const payload = await readJson(request);
  if (!payload || !payload.mfa_token || !payload.code) {
    return NextResponse.json({ error: { code: "VALIDATION", message: "mfa_token and code are required" } }, { status: 422 });
  }

  const resp = await fetch(`${serverApiUrl()}${API_PREFIX}/auth/totp/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mfa_token: payload.mfa_token, code: payload.code }),
  });
  const body = await resp.json();

  if (!resp.ok) {
    return NextResponse.json(body, { status: resp.status });
  }

  const data = body.data ?? {};
  const response = NextResponse.json({
    data: { access_token: data.access_token, expires_in: data.expires_in },
  });
  const refreshMaxAge: number = data.refresh_expires_in ?? 60 * 60 * 24 * 30;
  response.cookies.set(COOKIE_NAME, data.refresh_token, cookieOptions(refreshMaxAge));
  return response;
}
