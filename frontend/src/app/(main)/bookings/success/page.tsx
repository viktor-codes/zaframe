import { OrderPaymentSuccessPanel } from "@features/book-course";
import { PaymentSuccessPanel } from "@features/book-occurrence";

interface BookingSuccessPageProps {
  searchParams: Promise<{ order?: string; booking?: string }>;
}

export default async function BookingSuccessPage({
  searchParams,
}: BookingSuccessPageProps) {
  const { order: orderIdParam, booking: bookingIdParam } = await searchParams;

  // WHY: course checkout redirects with ?order=; drop-in uses ?booking=.
  if (orderIdParam != null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <OrderPaymentSuccessPanel orderIdParam={orderIdParam} />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-12">
      <PaymentSuccessPanel bookingIdParam={bookingIdParam ?? null} />
    </div>
  );
}
