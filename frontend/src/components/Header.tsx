"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { Button } from "@/components/ui";

export function Header() {
  const { user, logout } = useAuth();

  return (
    <header className="border-b border-neutral-200 bg-white">
      <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-3">
          <div className="bg-secondary w-10 h-10 rounded flex items-center justify-center">
            <svg
              className="w-6 h-6 text-primary"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2.5}
                d="M5 13l4 4L19 7"
              />
            </svg>
          </div>
          <span className="font-display font-bold text-xl text-secondary">
            ZaFrame
          </span>
        </Link>

        <nav className="flex items-center gap-4">
          <Link
            href="/studios"
            className="text-neutral-600 hover:text-secondary font-medium"
          >
            Studios
          </Link>
          {user ? (
            <>
              <Link
                href="/dashboard"
                className="text-neutral-600 hover:text-secondary font-medium"
              >
                Dashboard
              </Link>
              <Link
                href="/bookings"
                className="text-neutral-600 hover:text-secondary font-medium"
              >
                My bookings
              </Link>
              <span className="text-sm text-neutral-500">{user.name}</span>
              <Button variant="ghost" onClick={logout} className="py-2">
                Sign out
              </Button>
            </>
          ) : (
            <Link href="/auth/login">
              <Button variant="outline" className="py-2">
                Sign in
              </Button>
            </Link>
          )}
        </nav>
      </div>
    </header>
  );
}
