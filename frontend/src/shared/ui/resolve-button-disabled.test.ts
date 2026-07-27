import { describe, expect, it } from "vitest";

import { resolveButtonDisabled } from "./resolve-button-disabled";

describe("resolveButtonDisabled", () => {
  it("disables while loading even when disabled prop is false", () => {
    expect(resolveButtonDisabled(false, true)).toBe(true);
  });

  it("disables when disabled prop is true", () => {
    expect(resolveButtonDisabled(true, false)).toBe(true);
  });

  it("stays enabled when neither disabled nor loading", () => {
    expect(resolveButtonDisabled(false, false)).toBe(false);
    expect(resolveButtonDisabled(undefined, false)).toBe(false);
  });

  it("disables while loading when disabled prop is omitted", () => {
    expect(resolveButtonDisabled(undefined, true)).toBe(true);
  });
});
