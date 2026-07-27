import {
  BookingStatus,
  type BookingStatus as BookingStatusValue,
} from "@shared/lib";

export type StudioBookingsStatusFilter = "all" | BookingStatusValue;

export const STUDIO_BOOKINGS_PAGE_SIZE = 20;

export const STUDIO_BOOKINGS_STATUS_TABS: {
  id: StudioBookingsStatusFilter;
  label: string;
}[] = [
  { id: "all", label: "All" },
  { id: BookingStatus.PENDING, label: "Pending" },
  { id: BookingStatus.CONFIRMED, label: "Confirmed" },
  { id: BookingStatus.CANCELLED, label: "Cancelled" },
  { id: BookingStatus.COMPLETED, label: "Completed" },
  { id: BookingStatus.EXPIRED, label: "Expired" },
  { id: BookingStatus.NO_SHOW, label: "No-show" },
];
