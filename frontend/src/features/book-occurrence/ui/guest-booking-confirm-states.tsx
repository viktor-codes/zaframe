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
}: {
  kind: "cancelled" | "expired";
  backHref: string;
  backLabel: string;
}) {
  const isExpired = kind === "expired";
  return (
    <div
      className="mx-auto max-w-2xl px-6 py-12"
      data-testid="guest-confirm-inactive"
    >
      <Link
        href={backHref}
        className="mb-6 inline-block text-sm font-medium text-primary hover:text-primary-dark"
      >
        {backLabel}
      </Link>
      <Card className="p-8 text-center">
        <p className="font-semibold text-neutral-700">
          {isExpired ? "Payment window expired" : "Booking cancelled"}
        </p>
        <p className="mt-1 text-sm text-neutral-600">
          {isExpired
            ? "This hold timed out before payment. Book another slot to try again."
            : "This booking is no longer active."}
        </p>
        <div className="mt-4">
          <Button asChild>
            <Link href="/studios">Browse studios</Link>
          </Button>
        </div>
      </Card>
    </div>
  );
}

export function GuestConfirmCancelControls({
  showConfirm,
  isCancelling,
  onAskConfirm,
  onKeep,
  onConfirmCancel,
}: {
  showConfirm: boolean;
  isCancelling: boolean;
  onAskConfirm: () => void;
  onKeep: () => void;
  onConfirmCancel: () => void;
}) {
  if (showConfirm) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <p className="mb-2 font-medium text-red-800">
          Cancel this booking? This cannot be undone.
        </p>
        <div className="flex gap-2">
          <Button
            variant="danger"
            onClick={onConfirmCancel}
            isLoading={isCancelling}
            data-testid="confirm-cancel-booking"
          >
            Yes, cancel booking
          </Button>
          <Button
            variant="outline"
            onClick={onKeep}
            disabled={isCancelling}
          >
            Keep booking
          </Button>
        </div>
      </div>
    );
  }

  return (
    <Button
      variant="ghost"
      onClick={onAskConfirm}
      className="text-red-600 hover:bg-red-50 hover:text-red-700"
      data-testid="cancel-booking-button"
    >
      Cancel booking
    </Button>
  );
}
