/**
 * Seed bookable studio + occurrence for E2E via backend script.
 *
 * Requires: PostgreSQL migrated, backend deps installed (`uv sync` in backend/).
 * Override with E2E_STUDIO_ID + E2E_OCCURRENCE_ID + E2E_OCCURRENCE_DATE env vars
 * to skip seeding (e.g. when using pre-seeded demo data).
 */

import { execSync } from "node:child_process";
import path from "node:path";

export interface E2eSeedData {
  studioId: number;
  occurrenceId: number;
  occurrenceDate: string;
  ownerAccessToken: string;
}

function seedFromEnv(): E2eSeedData | null {
  const studioId = process.env.E2E_STUDIO_ID;
  const occurrenceId = process.env.E2E_OCCURRENCE_ID;
  const occurrenceDate = process.env.E2E_OCCURRENCE_DATE;
  const ownerAccessToken = process.env.E2E_OWNER_ACCESS_TOKEN ?? "";

  if (!studioId || !occurrenceId || !occurrenceDate) {
    return null;
  }

  return {
    studioId: Number(studioId),
    occurrenceId: Number(occurrenceId),
    occurrenceDate,
    ownerAccessToken,
  };
}

/**
 * Create a studio with a paid occurrence (or read fixed IDs from env).
 */
export function seedBookableOccurrence(): E2eSeedData {
  const fromEnv = seedFromEnv();
  if (fromEnv) {
    return fromEnv;
  }

  const backendDir = path.resolve(__dirname, "../../../backend");
  const output = execSync("uv run python -m tests.e2e.e2e_seed", {
    cwd: backendDir,
    encoding: "utf-8",
    env: process.env,
    stdio: ["ignore", "pipe", "pipe"],
  });

  const line = output.trim().split("\n").at(-1);
  if (!line) {
    throw new Error("e2e_seed produced no output");
  }

  const parsed = JSON.parse(line) as {
    studioId: number;
    occurrenceId: number;
    occurrenceDate: string;
    ownerAccessToken: string;
  };

  return parsed;
}

/**
 * Fetch booking status via owner JWT (GET /bookings/{id} requires auth).
 */
export async function fetchBookingStatusAsOwner(
  apiBaseUrl: string,
  bookingId: number,
  ownerAccessToken: string,
): Promise<{ status: string; payment_status: string | null }> {
  const base = apiBaseUrl.replace(/\/$/, "");
  const response = await fetch(`${base}/api/v1/bookings/${bookingId}`, {
    headers: { Authorization: `Bearer ${ownerAccessToken}` },
  });
  if (!response.ok) {
    throw new Error(
      `GET booking failed: ${response.status} ${response.statusText}`,
    );
  }
  const body = (await response.json()) as {
    status: string;
    payment_status: string | null;
  };
  return {
    status: body.status,
    payment_status: body.payment_status,
  };
}
