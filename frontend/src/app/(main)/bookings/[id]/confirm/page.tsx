import { BookingConfirmView } from "./booking-confirm-view";

interface BookingConfirmPageProps {
  params: Promise<{ id: string }>;
}

export default async function BookingConfirmPage({
  params,
}: BookingConfirmPageProps) {
  const { id } = await params;
  return <BookingConfirmView routeId={id} />;
}
