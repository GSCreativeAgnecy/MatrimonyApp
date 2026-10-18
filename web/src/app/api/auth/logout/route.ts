import { NextRequest, NextResponse } from "next/server";

import { API_PREFIX, COOKIE_NAME, cookieOptions, rejectCrossOrigin, serverApiUrl } from "@/lib/bff";

export const runtime = "nodejs";

export async function POST(request: NextRequest) {
  const csrf = rejectCrossOrigin(request);
  if (csrf) return csrf;

  const refreshToken = request.cookies.get(COOKIE_NAME)?.value;
  if (refreshToken) {
    try {
      await fetch(`${serverApiUrl()}${API_PREFIX}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
    } catch {
      // Best-effort server-side revoke; the cookie is cleared regardless.
    }
  }

  const response = NextResponse.json({ data: { status: "logged_out" } });
  response.cookies.set(COOKIE_NAME, "", { ...cookieOptions(0), maxAge: 0 });
  return response;
}
