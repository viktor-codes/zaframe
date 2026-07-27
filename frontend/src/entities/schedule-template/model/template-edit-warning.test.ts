import { describe, expect, it } from "vitest";

import {
  DEFAULT_TEMPLATE_EDIT_WARNING,
  getScheduleTemplateEditWarning,
} from "./template-edit-warning";

describe("getScheduleTemplateEditWarning", () => {
  it("uses the API edit_behavior when present", () => {
    expect(
      getScheduleTemplateEditWarning({
        edit_behavior: "  From API.  ",
      }),
    ).toBe("From API.");
  });

  it("falls back to the product warning when API copy is missing", () => {
    expect(getScheduleTemplateEditWarning(null)).toBe(
      DEFAULT_TEMPLATE_EDIT_WARNING,
    );
    expect(getScheduleTemplateEditWarning({ edit_behavior: "   " })).toBe(
      DEFAULT_TEMPLATE_EDIT_WARNING,
    );
  });
});
