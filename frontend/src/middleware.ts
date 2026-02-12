import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * В режиме «только лендинг» (NEXT_PUBLIC_API_URL не задан) перенаправляем
 * все маршруты приложения (студии, дашборд, брони, авторизация) на главную.
 * Доступна только статичная главная страница.
 */
const APP_PATHS = ["/studios", "/dashboard", "/bookings", "/auth"];

export function middleware(request: NextRequest) {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim() ?? "";
  if (apiUrl.length > 0) {
    return NextResponse.next();
  }

  const pathname = request.nextUrl.pathname;
  const isAppRoute = APP_PATHS.some((p) => pathname === p || pathname.startsWith(`${p}/`));
  if (isAppRoute) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/studios/:path*", "/dashboard/:path*", "/bookings/:path*", "/auth/:path*"],
};
