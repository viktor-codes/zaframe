import type { ServiceCategory } from "./types";

/**
 * Runtime enum values for OpenAPI `ServiceCategory`.
 * Bidirectional assert fails the build if OpenAPI adds/removes a category.
 */
export const SERVICE_CATEGORIES = [
  "yoga",
  "boxing",
  "dance",
  "hiit",
  "pilates",
  "martial_arts",
  "strength",
] as const;

type ServiceCategoryFromList = (typeof SERVICE_CATEGORIES)[number];

type AssertServiceCategoriesMatch =
  ServiceCategory extends ServiceCategoryFromList
    ? ServiceCategoryFromList extends ServiceCategory
      ? true
      : never
    : never;

const _assertServiceCategories: AssertServiceCategoriesMatch = true;
void _assertServiceCategories;

export function isServiceCategory(value: string): value is ServiceCategory {
  return (SERVICE_CATEGORIES as readonly string[]).includes(value);
}
