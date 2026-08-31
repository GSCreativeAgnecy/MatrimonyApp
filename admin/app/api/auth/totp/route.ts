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
  // Same-origin check by HOST only (scheme-insensitive) — works behind a
  // TLS-terminating reverse proxy (see login route).
  const origin = request.headers.get("origin");
  if (origin) {
    try {
      if (new URL(origin).host !== request.nextUrl.host) {
        return NextResponse.json({ error: { code: "CSRF", message: "Cross-origin request rejected" } }, { status: 403 });
      }
    } catch {
      return NextResponse.json({ error: { code: "CSRF", message: "Invalid origin" } }, { status: 403 });
    }
  }

  let payload: { mfa_token?: string; code?: string };
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: { code: "VALIDATION", message: "Invalid body" } }, { status: 422 });
  }

  const resp = await fetch(`${API_URL}${API_PREFIX}/auth/totp/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mfa_token: payload.mfa_token, code: payload.code }),
  });
  const body = await resp.json();
  if (!resp.ok) {
    return NextResponse.json(body, { status: resp.status });
  }

  const data = body.data ?? {};
  const response = NextResponse.json({ data: { access_token: data.access_token, expires_in: data.expires_in } });
  response.cookies.set(COOKIE_NAME, data.refresh_token, cookieOptions(data.expires_in * 2));
  return response;
}
