"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/account/bookings", label: "My bookings" },
  { href: "/account/orders", label: "Orders" },
  { href: "/account/profile", label: "Profile" },
] as const;

/** Active account section nav (pathname-driven). */
export function AccountNav() {
  const pathname = usePathname();

  return (
    <nav
      className="mx-auto flex max-w-4xl gap-6 px-6 pb-3"
      aria-label="Account"
    >
      {NAV_ITEMS.map((item) => {
        const isActive =
          pathname === item.href || pathname.startsWith(`${item.href}/`);

        return (
          <Link
            key={item.href}
            href={item.href}
            className={`text-sm font-medium ${
              isActive
                ? "text-primary"
                : "text-neutral-600 hover:text-neutral-900"
            }`}
            aria-current={isActive ? "page" : undefined}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
