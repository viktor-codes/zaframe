import { describe, expect, it } from "vitest";

import { formatMoneyFromCents } from "./format-money";

describe("formatMoneyFromCents", () => {
  it("formats whole euros with two fraction digits", () => {
    expect(formatMoneyFromCents(1500)).toMatch(/€\s?15\.00/);
  });

  it("keeps cents when not a whole euro", () => {
    expect(formatMoneyFromCents(1550)).toMatch(/€\s?15\.50/);
  });

  it("formats zero", () => {
    expect(formatMoneyFromCents(0)).toMatch(/€\s?0\.00/);
  });
});
