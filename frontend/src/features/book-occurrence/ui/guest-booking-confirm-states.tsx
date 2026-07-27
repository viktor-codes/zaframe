import type { ReactNode } from "react";
import Link from "next/link";
import { Alert, Button, Card, Skeleton } from "@shared/ui";

export function GuestConfirmNotFound() {
  return (
    <div
      className="mx-auto max-w-2xl px-6 py-12"
      data-testid="guest-confirm-not-found"
    >
      <Alert variant="error" title="Booking not found" className="mb-4">
        This booking link is invalid or no longer available.
      </Alert>
      <Button asChild>
        <Link href="/studios">Browse studios</Link>
      </Button>
    </div>
  );
}

export function GuestConfirmLoading() {
  return (
    <div
      className="mx-auto max-w-2xl px-6 py-12"
      data-testid="guest-confirm-loading"
    >
      <Skeleton className="mb-6 h-8 w-48" />
      <Skeleton className="h-32 w-full" />
    </div>
  );
}

export function GuestConfirmInactive({
  kind,
  backHref,
  backLabel,
  rebookHref = "/studios",
  studioCancelReason = null,
  timelineSlot = null,
}: {
  kind: "cancelled" | "expired" | "studio_cancelled";
  backHref: string;
  backLabel: string;
  rebookHref?: string;
  studioCancelReason?: string | null;
  timelineSlot?: ReactNode;
}) {
  const title =
    kind === "expired"
      ? "Payment window expired"
      : kind === "studio_cancelled"
        ? "Session cancelled by the studio"
        : "Booking cancelled";
  const description =
    kind === "expired"
      ? "This hold timed out before payment. Book another slot to try again."
      : kind === "studio_cancelled"
        ? studioCancelReason?.trim() ||
          "The studio cancelled this session. Book another time if you still want a seat."
        : "This booking is no longer active.";
  const ctaLabel = kind === "expired" ? "Book again" : "Browse studios";

  return (
    <div
      className="mx-auto max-w-2xl px-6 py-12"
      data-testid="guest-confirm-inactive"
      data-inactive-kind={kind}
    >
      <Link
        href={backHref}
        className="mb-6 inline-block text-sm font-medium text-primary hover:text-primary-dark"
      >
        {backLabel}
      </Link>
      <Card className="mb-6 p-8 text-center">
        <p className="font-semibold text-neutral-700">{title}</p>
        <p className="mt-1 text-sm text-neutral-600">{description}</p>
        <div className="mt-4">
          <Button asChild>
            <Link href={rebookHref}>{ctaLabel}</Link>
          </Button>
        </div>
      </Card>
      {timelineSlot}
    </div>
  );
}
