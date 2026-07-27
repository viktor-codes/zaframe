import { AccountProfilePanel } from "./account-profile-panel";

export default function AccountProfilePage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="text-secondary mb-2 font-display text-3xl font-bold">
        Profile
      </h1>
      <p className="mb-8 text-neutral-600">
        Keep your name and contact details up to date for bookings.
      </p>
      <AccountProfilePanel />
    </div>
  );
}
