import Link from "next/link";
import { Alert, Button, Card } from "@shared/ui";

import type { OrderPaymentConfirmationFailureReason } from "../model/resolve-order-payment-confirmation";

export function OrderPaymentProcessingState({
  isWebhookSlow,
}: {
  isWebhookSlow: boolean;
}) {
  return (
    <Card
      className="py-12 text-center"
      data-testid="order-payment-success-processing"
    >
      <div
        className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-sky-100 text-sky-700"
        aria-hidden
      >
        <span className="h-8 w-8 animate-spin rounded-full border-2 border-sky-300 border-t-sky-700" />
      </div>
      <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
        Payment processing…
      </h1>
      <p className="mb-4 text-neutral-600">
        Stripe confirmed the checkout. We are waiting for the final course
        confirmation — this usually takes a few seconds.
      </p>
      {isWebhookSlow ? (
        <Alert variant="info" title="Still confirming">
          This is taking longer than usual. Keep this page open — we will update
          it automatically. You can also check your email shortly.
        </Alert>
      ) : null}
    </Card>
  );
}

export function OrderPaymentWebhookTimeoutState({
  orderId,
}: {
  orderId: number | null;
}) {
  return (
    <Card
      className="py-12 text-center"
      data-testid="order-payment-success-webhook-timeout"
    >
      <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
        Still confirming your payment
      </h1>
      <p className="mb-6 text-neutral-600">
        Confirmation is taking longer than expected. Check your email for the
        course receipt, or open your orders — the status updates when the
        payment clears.
      </p>
      <div className="flex flex-col justify-center gap-4 sm:flex-row">
        {orderId != null ? (
          <Button asChild>
            <Link href="/account/orders">View my orders</Link>
          </Button>
        ) : null}
        <Button variant="outline" asChild>
          <Link href="/studios">Browse studios</Link>
        </Button>
      </div>
    </Card>
  );
}

export function OrderPaymentConfirmedState() {
  return (
    <Card
      className="py-12 text-center"
      data-testid="order-payment-success-confirmed"
    >
      <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-green-100 text-green-600">
        <svg
          className="h-8 w-8"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>
      <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
        You&apos;re enrolled
      </h1>
      <p className="mb-8 text-neutral-600">
        Payment is confirmed. We&apos;ll send the course details to your email.
      </p>
      <div className="flex flex-col justify-center gap-4 sm:flex-row">
        <Button asChild>
          <Link
            href="/account/orders"
            data-testid="order-payment-success-view-orders"
          >
            View my orders
          </Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/account/bookings">View my bookings</Link>
        </Button>
      </div>
    </Card>
  );
}

export function OrderPaymentManualReviewState() {
  return (
    <Card
      className="py-12 text-center"
      data-testid="order-payment-success-manual-review"
    >
      <h1 className="text-secondary mb-2 font-display text-2xl font-bold">
        Payment is being verified
      </h1>
      <p className="mb-8 text-neutral-600">
        Your payment was received, but some sessions need studio confirmation.
        We&apos;ll email you when it&apos;s resolved — or contact support if you
        need help sooner.
      </p>
      <div className="flex flex-col justify-center gap-4 sm:flex-row">
        <Button asChild>
          <Link href="/account/orders">View my orders</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/studios">Browse studios</Link>
        </Button>
      </div>
    </Card>
  );
}

function failureCopy(reason: OrderPaymentConfirmationFailureReason): {
  title: string;
  body: string;
} {
  switch (reason) {
    case "expired":
      return {
        title: "Payment window expired",
        body: "Your course hold timed out before payment was confirmed. Purchase the course again to continue.",
      };
    case "cancelled":
      return {
        title: "Order cancelled",
        body: "This course order is no longer active. Browse studios to find another class.",
      };
    case "refunded":
      return {
        title: "Payment refunded",
        body: "This course order was refunded. Check your email or contact the studio if you need help.",
      };
    default:
      return {
        title: "Something went wrong",
        body: "We could not confirm this course order. Please open your orders or contact the studio.",
      };
  }
}

export function OrderPaymentFailedState({
  reason,
}: {
  reason: OrderPaymentConfirmationFailureReason;
}) {
  const copy = failureCopy(reason);
  return (
    <Card
      className="py-12 text-center"
      data-testid="order-payment-success-failed"
    >
      <Alert variant="error" title={copy.title} className="mb-8 text-left">
        {copy.body}
      </Alert>
      <div className="flex flex-col justify-center gap-4 sm:flex-row">
        <Button asChild>
          <Link href="/account/orders">View my orders</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/studios">Browse studios</Link>
        </Button>
      </div>
    </Card>
  );
}

export function OrderPaymentLoadErrorState({
  errorMessage,
}: {
  errorMessage: string | null;
}) {
  return (
    <Card
      className="py-12 text-center"
      data-testid="order-payment-success-error"
    >
      <Alert
        variant="error"
        title="Could not load order"
        className="mb-8 text-left"
      >
        {errorMessage ?? "Something went wrong. Please try again."}
      </Alert>
      <div className="flex flex-col justify-center gap-4 sm:flex-row">
        <Button asChild>
          <Link href="/account/orders">View my orders</Link>
        </Button>
        <Button variant="outline" asChild>
          <Link href="/studios">Browse studios</Link>
        </Button>
      </div>
    </Card>
  );
}
