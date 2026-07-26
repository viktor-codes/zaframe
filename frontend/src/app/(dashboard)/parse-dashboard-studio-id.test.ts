import { describe, expect, it } from "vitest";

import { parseDashboardStudioId } from "./parse-dashboard-studio-id";

describe("parseDashboardStudioId", () => {
  it("returns null for the studios list and create routes", () => {
    expect(parseDashboardStudioId("/dashboard")).toBeNull();
    expect(parseDashboardStudioId("/dashboard/studios/new")).toBeNull();
  });

  it("reads the studio id from nested dashboard routes", () => {
    expect(parseDashboardStudioId("/dashboard/studios/12")).toBe(12);
    expect(parseDashboardStudioId("/dashboard/studios/12/bookings")).toBe(12);
    expect(parseDashboardStudioId("/dashboard/studios/12/services/3")).toBe(12);
  });

  it("rejects non-positive ids", () => {
    expect(parseDashboardStudioId("/dashboard/studios/0")).toBeNull();
  });
});
