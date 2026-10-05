import { type NextRequest, NextResponse } from "next/server";

import { updateSession } from "@/lib/supabase/middleware";

const PROTECTED_ROUTES = ["/", "/inbox", "/packages", "/contacts", "/settings"];

function isProtected(pathname: string): boolean {
  return PROTECTED_ROUTES.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

export async function middleware(request: NextRequest): Promise<NextResponse> {
  if (!isProtected(request.nextUrl.pathname)) {
    return NextResponse.next();
  }
  if (!process.env.NEXT_PUBLIC_SUPABASE_URL || !process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    // Supabase is not configured (local UI work and tests): allow through.
    return NextResponse.next();
  }

  const { response, user } = await updateSession(request);
  if (!user) {
    const signInUrl = request.nextUrl.clone();
    signInUrl.pathname = "/auth/sign-in";
    return NextResponse.redirect(signInUrl);
  }
  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp|mp4)$).*)"],
};
