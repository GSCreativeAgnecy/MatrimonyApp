import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";

const API_URL = process.env.ADMIN_API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_PREFIX = "/api/v1";
const COOKIE_NAME = "mm_admin_refresh";
const SECURE = process.env.NODE_ENV === "production";

function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: "strict" as const,
    secure: SECURE,
    path: "/",
    maxAge,
  };
}

export async function POST(request: NextRequest) {
  const refreshToken = request.cookies.get(COOKIE_NAME)?.value;
  if (!refreshToken) {
    return NextResponse.json({ error: { code: "NO_SESSION", message: "No session" } }, { status: 401 });
  }

  const resp = await fetch(`${API_URL}${API_PREFIX}/auth/refresh`, {
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
  const response = NextResponse.json({ data: { access_token: data.access_token, expires_in: data.expires_in } });
  // Refresh-token rotation: the backend issued a new refresh token; keep the
  // cookie alive for the refresh token's full lifetime.
  const refreshMaxAge = data.refresh_expires_in ?? 60 * 60 * 24 * 30;
  response.cookies.set(COOKIE_NAME, data.refresh_token, cookieOptions(refreshMaxAge));
  return response;
}
