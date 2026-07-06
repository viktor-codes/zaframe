import type { Schema } from "@shared/api/schema";

export type BookingCreate = Schema<"BookingCreate">;
export type BookingCreatedResponse = Schema<"BookingCreatedResponse">;
export type BookingSelfResponse = Schema<"BookingSelfResponse">;
export type BookingSelfListItem = Schema<"BookingSelfListItem">;
export type BookingOwnerResponse = Schema<"BookingOwnerResponse">;
export type CourseBookingCreate = Schema<"CourseBookingCreate">;
export type CourseBookingResponse = Schema<"CourseBookingResponse">;
export type PaginatedBookingSelfList =
  Schema<"PaginatedResponse_BookingSelfListItem_">;
export type PaginatedBookingOwnerList =
  Schema<"PaginatedResponse_BookingOwnerResponse_">;

export type BookingLike =
  | BookingSelfResponse
  | BookingSelfListItem
  | BookingCreatedResponse
  | BookingOwnerResponse;
