import { NextRequest, NextResponse } from "next/server";

import { API_PREFIX, COOKIE_NAME, cookieOptions, rejectCrossOrigin, serverApiUrl } from "@/lib/bff";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const csrf = rejectCrossOrigin(request);
  if (csrf) return csrf;

  const refreshToken = request.cookies.get(COOKIE_NAME)?.value;
  if (!refreshToken) {
    return NextResponse.json({ error: { code: "NO_SESSION", message: "No session" } }, { status: 401 });
  }

  const resp = await fetch(`${serverApiUrl()}${API_PREFIX}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  const body = await resp.json();

  if (!resp.ok) {
    // Revoked/expired session: clear the cookie.
    const response = NextResponse.json(body, { status: resp.status });
    response.cookies.set(COOKIE_NAME, "", { ...cookieOptions(0), maxAge: 0 });
    return response;
  }

  const data = body.data ?? {};
  const response = NextResponse.json({
    data: { access_token: data.access_token, expires_in: data.expires_in },
  });
  // Refresh-token rotation: keep the cookie alive for the new token's lifetime.
  const refreshMaxAge: number = data.refresh_expires_in ?? 60 * 60 * 24 * 30;
  response.cookies.set(COOKIE_NAME, data.refresh_token, cookieOptions(refreshMaxAge));
  return response;
}
