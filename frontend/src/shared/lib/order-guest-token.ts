/**
 * Guest checkout token from course POST /bookings (`CourseBookingResponse`).
 * Stored in sessionStorage for Stripe order checkout retries.
 */

import { z } from "zod";

import { removeSessionStorageByPrefixes } from "./remove-session-storage-by-prefixes";

const TOKEN_PREFIX = "zeeframe_order_access_token_";
const SNAPSHOT_PREFIX = "zeeframe_order_snapshot_";

const GuestOrderSnapshotSchema = z.object({
  id: z.number().int().positive(),
  service_id: z.number().int().positive().nullable(),
  guest_name: z.string().nullable(),
  guest_email: z.string().nullable(),
  status: z.string().min(1),
  total_amount_cents: z.number().int().nonnegative(),
  currency: z.string().min(1),
});

export type GuestOrderSnapshot = z.infer<typeof GuestOrderSnapshotSchema>;

export function storeGuestOrderAccess(
  orderId: number,
  accessToken: string,
  snapshot: GuestOrderSnapshot,
): void {
  if (typeof window === "undefined") return;
  const parsed = GuestOrderSnapshotSchema.safeParse({
    ...snapshot,
    id: orderId,
  });
  if (!parsed.success) return;

  sessionStorage.setItem(`${TOKEN_PREFIX}${orderId}`, accessToken);
  sessionStorage.setItem(
    `${SNAPSHOT_PREFIX}${orderId}`,
    JSON.stringify(parsed.data),
  );
}

export function persistGuestOrderAccessToken(
  orderId: number,
  accessToken: string,
): void {
  if (typeof window === "undefined") return;
  const trimmed = accessToken.trim();
  if (!trimmed) return;
  sessionStorage.setItem(`${TOKEN_PREFIX}${orderId}`, trimmed);
}

export function getGuestOrderAccessToken(orderId: number): string | null {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(`${TOKEN_PREFIX}${orderId}`);
}

export function getGuestOrderSnapshot(
  orderId: number,
): GuestOrderSnapshot | null {
  if (typeof window === "undefined") return null;
  const raw = sessionStorage.getItem(`${SNAPSHOT_PREFIX}${orderId}`);
  if (!raw) return null;
  try {
    const parsed = GuestOrderSnapshotSchema.safeParse(JSON.parse(raw));
    return parsed.success ? parsed.data : null;
  } catch {
    return null;
  }
}

/** Remove all guest order tokens and PII snapshots (logout / session invalidate). */
export function clearAllGuestOrderAccess(): void {
  removeSessionStorageByPrefixes([TOKEN_PREFIX, SNAPSHOT_PREFIX]);
}
