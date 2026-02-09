"use client";

import { RequireAuth } from "@/components/RequireAuth";

export default function BookingsPage() {
  return (
    <RequireAuth>
      <div className="max-w-6xl mx-auto px-6 py-12">
        <h1 className="font-display font-bold text-3xl text-secondary mb-4">
          My bookings
        </h1>
        <p className="text-neutral-600">
          Your bookings will appear here. (Phase 3)
        </p>
      </div>
    </RequireAuth>
  );
}
