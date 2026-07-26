import { describe, expect, it } from "vitest";

import { getSafeNextPath } from "./safe-next-path";

describe("getSafeNextPath", () => {
  it("accepts relative app paths", () => {
    expect(getSafeNextPath("/s/yoga/book/1")).toBe("/s/yoga/book/1");
    expect(getSafeNextPath("/bookings/3/confirm")).toBe("/bookings/3/confirm");
  });

  it("rejects absolute and protocol-relative URLs", () => {
    expect(getSafeNextPath("https://evil.example")).toBeNull();
    expect(getSafeNextPath("//evil.example")).toBeNull();
    expect(getSafeNextPath("http://localhost/phish")).toBeNull();
  });

  it("rejects empty values", () => {
    expect(getSafeNextPath(null)).toBeNull();
    expect(getSafeNextPath("")).toBeNull();
    expect(getSafeNextPath("   ")).toBeNull();
  });
});
