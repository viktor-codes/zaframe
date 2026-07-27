import { describe, expect, it } from "vitest";

import { parsePositiveIdString } from "./parse-positive-id";

describe("parsePositiveIdString", () => {
  it("parses digit strings", () => {
    expect(parsePositiveIdString("42")).toBe(42);
    expect(parsePositiveIdString(" 7 ")).toBe(7);
  });

  it("rejects empty, zero, floats, and scientific notation", () => {
    expect(parsePositiveIdString(null)).toBeNull();
    expect(parsePositiveIdString(undefined)).toBeNull();
    expect(parsePositiveIdString("")).toBeNull();
    expect(parsePositiveIdString("0")).toBeNull();
    expect(parsePositiveIdString("1.5")).toBeNull();
    expect(parsePositiveIdString("1e2")).toBeNull();
    expect(parsePositiveIdString("-3")).toBeNull();
    expect(parsePositiveIdString("abc")).toBeNull();
  });
});
