import Link from "next/link";

export interface TodayQuickActionsProps {
  studioId: number;
}

interface QuickAction {
  label: string;
  href: string;
  testId: string;
}

export function TodayQuickActions({ studioId }: TodayQuickActionsProps) {
  const base = `/dashboard/studios/${studioId}`;
  const actions: QuickAction[] = [
    {
      label: "Calendar",
      href: `${base}/calendar`,
      testId: "today-action-calendar",
    },
    {
      label: "Services",
      href: `${base}/services`,
      testId: "today-action-services",
    },
    {
      label: "Bookings",
      href: `${base}/bookings`,
      testId: "today-action-bookings",
    },
    {
      label: "Profile",
      href: `${base}/profile`,
      testId: "today-action-profile",
    },
  ];

  return (
    <nav aria-label="Quick actions" data-testid="today-quick-actions">
      <p className="mb-2 text-xs font-semibold tracking-wide text-neutral-500 uppercase">
        Quick actions
      </p>
      <ul className="flex flex-wrap gap-2">
        {actions.map((action) => (
          <li key={action.href}>
            <Link
              href={action.href}
              data-testid={action.testId}
              className="inline-flex rounded-lg border border-neutral-200 bg-white px-3 py-2 text-sm font-medium text-neutral-800 hover:border-neutral-300 hover:bg-neutral-50"
            >
              {action.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
