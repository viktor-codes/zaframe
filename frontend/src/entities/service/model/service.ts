import type { PublicService, ServiceResponse } from "./types";

type ServicePricing = Pick<
  ServiceResponse,
  "type" | "price_single_cents" | "price_course_cents" | "visibility"
>;

export const SERVICE_VISIBILITY = {
  DRAFT: "draft",
  PUBLISHED: "published",
  ARCHIVED: "archived",
} as const;

export const SERVICE_TYPE = {
  SINGLE: "single",
  COURSE: "course",
} as const;

export function isCourseService(
  service: Pick<ServicePricing, "type">,
): boolean {
  return service.type === SERVICE_TYPE.COURSE;
}

export function isSingleService(
  service: Pick<ServicePricing, "type">,
): boolean {
  return service.type === SERVICE_TYPE.SINGLE;
}

export function isPublishedService(
  service: Pick<ServicePricing, "visibility">,
): boolean {
  return service.visibility === SERVICE_VISIBILITY.PUBLISHED;
}

export function getServiceDropInPriceCents(
  service: Pick<ServicePricing, "price_single_cents">,
): number {
  return service.price_single_cents;
}

export function getServiceCoursePriceCents(
  service: Pick<ServicePricing, "price_course_cents">,
): number | null {
  return service.price_course_cents ?? null;
}

export function getPublicServicePriceCents(service: PublicService): number {
  if (isCourseService(service) && service.price_course_cents != null) {
    return service.price_course_cents;
  }

  return service.price_single_cents;
}
