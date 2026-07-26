import { AccountBookingsPanel } from "./account-bookings-panel";

export default function BookingsPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
        My bookings
      </h1>
      <p className="mb-8 text-neutral-600">
        Upcoming sessions, past visits, and cancellations — in one place.
      </p>
      <AccountBookingsPanel />
    </div>
  );
}
