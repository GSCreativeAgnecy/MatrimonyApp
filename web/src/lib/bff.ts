import { NextRequest, NextResponse } from "next/server";

export const COOKIE_NAME = "mm_web_refresh";

const SECURE = process.env.NODE_ENV === "production";

export function cookieOptions(maxAge: number) {
  return {
    httpOnly: true,
    sameSite: "strict" as const,
    secure: SECURE,
    path: "/",
    maxAge,
  };
}

export function serverApiUrl(): string {
  return (process.env.WEB_API_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000").replace(
    /\/+$/,
    "",
  );
}

export const API_PREFIX = "/api/v1";

/** Reject cross-origin browser requests (defense-in-depth on top of SameSite=strict). */
export function rejectCrossOrigin(request: NextRequest): NextResponse | null {
  const origin = request.headers.get("origin");
  if (origin && origin !== "null") {
    try {
      const originHost = new URL(origin).host;
      const ownHost = request.headers.get("host") ?? "";
      const allowed = ["ardhangmatrimony.com", "frontseatview.com"];
      const isSameHost =
        originHost === ownHost || (originHost && ownHost && originHost.split(":")[0] === ownHost.split(":")[0]);
      const isKnown = allowed.some((d) => originHost === d || originHost.endsWith("." + d));
      if (!isSameHost && !isKnown) {
        return NextResponse.json(
          { error: { code: "CSRF", message: "Cross-origin request rejected" } },
          { status: 403 },
        );
      }
    } catch {
      return NextResponse.json({ error: { code: "CSRF", message: "Invalid origin" } }, { status: 403 });
    }
  }
  return null;
}

/** Parse a JSON body without throwing; returns null on anything malformed. */
export async function readJson(request: NextRequest): Promise<Record<string, unknown> | null> {
  try {
    return (await request.json()) as Record<string, unknown>;
  } catch {
    return null;
  }
}
