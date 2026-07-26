export interface GuestConfirmCancelContext {
  bookingId: number;
  booking: { status: string; cancelled_at: string | null };
  occurrence: { start_time: string };
  studio: { cancel_before_hours: number };
  accessToken: string | null;
  now: Date;
}
