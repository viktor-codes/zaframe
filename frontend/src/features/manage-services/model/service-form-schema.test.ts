import { describe, expect, it } from "vitest";

import { SERVICE_TYPE } from "@entities/service";
import { ServiceVisibility } from "@shared/lib";

import { parseCreateService, parseUpdateService } from "./service-form-schema";
import { emptyServiceForm } from "./service-form-values";

describe("parseCreateService", () => {
  it("creates a draft single service with prices in cents", () => {
    const { data, errors } = parseCreateService(
      emptyServiceForm({
        name: "Morning Flow",
        price_euros: "30",
      }),
      9,
    );

    expect(errors).toEqual({});
    expect(data).toMatchObject({
      studio_id: 9,
      name: "Morning Flow",
      price_single_cents: 3000,
      visibility: ServiceVisibility.DRAFT,
      type: SERVICE_TYPE.SINGLE,
    });
  });

  it("requires a course price for course offerings", () => {
    const { data, errors } = parseCreateService(
      emptyServiceForm({
        name: "Term Pass",
        type: SERVICE_TYPE.COURSE,
        price_euros: "20",
        price_course_euros: "",
      }),
      9,
    );

    expect(data).toBeNull();
    expect(errors.price_course_euros).toBeTruthy();
  });
});

describe("parseUpdateService", () => {
  it("omits visibility so lifecycle actions stay explicit", () => {
    const { data } = parseUpdateService(
      emptyServiceForm({
        name: "Morning Flow",
        price_euros: "25.50",
      }),
    );

    expect(data).not.toHaveProperty("visibility");
    expect(data?.price_single_cents).toBe(2550);
  });
});
