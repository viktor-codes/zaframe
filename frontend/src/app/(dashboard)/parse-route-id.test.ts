import { describe, expect, it } from "vitest";

import { parsePositiveRouteId } from "./parse-route-id";

describe("parsePositiveRouteId", () => {
  it("parses a numeric string segment", () => {
    expect(parsePositiveRouteId("12")).toBe(12);
  });

  it("uses the first segment when the param is an array", () => {
    expect(parsePositiveRouteId(["9", "ignored"])).toBe(9);
  });

  it("rejects missing, zero, and non-numeric values", () => {
    expect(parsePositiveRouteId(undefined)).toBeNull();
    expect(parsePositiveRouteId("")).toBeNull();
    expect(parsePositiveRouteId("0")).toBeNull();
    expect(parsePositiveRouteId("abc")).toBeNull();
  });

  it("rejects floats and scientific notation", () => {
    expect(parsePositiveRouteId("1.5")).toBeNull();
    expect(parsePositiveRouteId("1e2")).toBeNull();
    expect(parsePositiveRouteId("-3")).toBeNull();
  });
});
