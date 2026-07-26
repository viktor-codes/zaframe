"use client";

import { MyStudiosPanel } from "@features/view-my-studios";

export default function DashboardPage() {
  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6 sm:py-12">
      <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
        Dashboard
      </h1>
      <p className="mb-8 text-neutral-600">
        Your studios and the next step to start taking bookings.
      </p>
      <MyStudiosPanel />
    </div>
  );
}
