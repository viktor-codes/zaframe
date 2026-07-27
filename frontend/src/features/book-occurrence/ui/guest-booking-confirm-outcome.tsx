import Link from "next/link";
import { isBookingPaymentSucceeded } from "@entities/booking";
import { Alert, Button } from "@shared/ui";

export interface GuestBookingConfirmOutcomeProps {
  bookingStatus: string;
  paymentStatus: string | null | undefined;
  needsPayment: boolean;
  canPay: boolean;
  isHoldExpired: boolean;
  isPaid: boolean;
  isFreeUnpaid: boolean;
  isPaying: boolean;
  onPay: () => void;
}

/** Pay CTAs and confirmation alerts below the booking summary. */
export function GuestBookingConfirmOutcome({
  bookingStatus,
  paymentStatus,
  needsPayment,
  canPay,
  isHoldExpired,
  isPaid,
  isFreeUnpaid,
  isPaying,
  onPay,
}: GuestBookingConfirmOutcomeProps) {
  return (
    <>
      {needsPayment && canPay ? (
        <div className="mb-6 flex flex-col gap-4 sm:flex-row">
          <Button
            onClick={onPay}
            isLoading={isPaying}
            data-testid="pay-booking-button"
          >
            Complete payment
          </Button>
          <Button variant="outline" asChild>
            <Link href="/studios">Browse studios</Link>
          </Button>
        </div>
      ) : null}

      {needsPayment && isHoldExpired ? (
        <div className="mb-6 flex flex-col gap-4 sm:flex-row">
          <Button asChild data-testid="rebook-after-hold-expired">
            <Link href="/studios">Book another class</Link>
          </Button>
        </div>
      ) : null}

      {isPaid ? (
        <Alert variant="success" title="Confirmed" className="mb-6">
          Your booking is confirmed
          {isBookingPaymentSucceeded({ payment_status: paymentStatus })
            ? " and paid"
            : ""}
          .
        </Alert>
      ) : null}

      {isFreeUnpaid ? (
        <Alert variant="success" title="Free session" className="mb-6">
          No payment required. Your seat is reserved
          {bookingStatus === "confirmed" ? " and confirmed" : ""}— check your
          email for details.
        </Alert>
      ) : null}
    </>
  );
}
