import { describe, expect, it } from "vitest";

import { emptyStudioProfileForm } from "./studio-profile-form";
import { parseCreateStudio, parseUpdateStudio } from "./studio-profile-schema";

describe("parseCreateStudio", () => {
  it("accepts a minimal create payload", () => {
    const { data, errors } = parseCreateStudio(
      emptyStudioProfileForm({
        name: "Yoga Hub",
        timezone: "Europe/Dublin",
        cancel_before_hours: "24",
      }),
    );

    expect(errors).toEqual({});
    expect(data).toMatchObject({
      name: "Yoga Hub",
      timezone: "Europe/Dublin",
      cancel_before_hours: 24,
      slug: null,
      city: null,
    });
  });

  it("rejects an invalid slug on create", () => {
    const { data, errors } = parseCreateStudio(
      emptyStudioProfileForm({
        name: "Yoga Hub",
        slug: "Bad Slug",
        timezone: "Europe/Dublin",
      }),
    );

    expect(data).toBeNull();
    expect(errors.slug).toMatch(/lowercase/i);
  });
});

describe("parseUpdateStudio", () => {
  it("requires slug, city, and description for storefront readiness", () => {
    const { data, errors } = parseUpdateStudio(
      emptyStudioProfileForm({
        name: "Yoga Hub",
        timezone: "Europe/Dublin",
      }),
    );

    expect(data).toBeNull();
    expect(errors.slug).toBeTruthy();
    expect(errors.city).toBeTruthy();
    expect(errors.description).toBeTruthy();
  });

  it("parses a complete profile update", () => {
    const { data, errors } = parseUpdateStudio(
      emptyStudioProfileForm({
        name: "Yoga Hub",
        slug: "yoga-hub-dublin",
        city: "Dublin",
        description: "Bright loft for small classes",
        timezone: "Europe/Dublin",
        cancel_before_hours: "48",
        email: "hello@yoga.example",
      }),
    );

    expect(errors).toEqual({});
    expect(data).toMatchObject({
      slug: "yoga-hub-dublin",
      city: "Dublin",
      cancel_before_hours: 48,
      email: "hello@yoga.example",
    });
  });
});
