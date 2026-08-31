import { cookies } from "next/headers";
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
  // Same-origin check: the refresh cookie is only ever set/read by this BFF.
  // Compare by HOST only (not full origin): behind a TLS-terminating reverse
  // proxy (nginx->here) the request's scheme is http while the browser sends
  // https, so a full-origin compare would 403 every login. Hostname must match.
  const origin = request.headers.get("origin");
  if (origin) {
    try {
      const originHost = new URL(origin).host;
      if (originHost !== request.nextUrl.host) {
        return NextResponse.json({ error: { code: "CSRF", message: "Cross-origin request rejected" } }, { status: 403 });
      }
    } catch {
      return NextResponse.json({ error: { code: "CSRF", message: "Invalid origin" } }, { status: 403 });
    }
  }

  let payload: { email?: string; phone_number?: string; password?: string };
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ error: { code: "VALIDATION", message: "Invalid body" } }, { status: 422 });
  }

  const resp = await fetch(`${API_URL}${API_PREFIX}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email: payload.email,
      phone_number: payload.phone_number,
      password: payload.password,
    }),
  });
  const body = await resp.json();

  if (!resp.ok) {
    return NextResponse.json(body, { status: resp.status });
  }

  const data = body.data ?? {};

  // Two-factor required: hand the short-lived mfa token back so the client can
  // complete the second step. Nothing is stored in a cookie yet.
  if (data.requires_2fa) {
    return NextResponse.json({ data: { requires_2fa: true, mfa_token: data.mfa_token, expires_in: data.expires_in } });
  }

  const refreshToken = data.refresh_token;
  const response = NextResponse.json({ data: { access_token: data.access_token, expires_in: data.expires_in } });
  response.cookies.set(COOKIE_NAME, refreshToken, cookieOptions(data.expires_in * 2));
  return response;
}
