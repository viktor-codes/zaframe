import { SERVICE_TYPE } from "@entities/service";

export const SERVICE_CATEGORIES = [
  "yoga",
  "boxing",
  "dance",
  "hiit",
  "pilates",
  "martial_arts",
  "strength",
] as const;

export type ServiceCategoryValue = (typeof SERVICE_CATEGORIES)[number];

export type ServiceFormValues = {
  name: string;
  description: string;
  type: string;
  category: ServiceCategoryValue;
  duration_minutes: string;
  max_capacity: string;
  price_euros: string;
  price_course_euros: string;
};

export function emptyServiceForm(
  defaults?: Partial<ServiceFormValues>,
): ServiceFormValues {
  return {
    name: "",
    description: "",
    type: SERVICE_TYPE.SINGLE,
    category: "yoga",
    duration_minutes: "60",
    max_capacity: "10",
    price_euros: "25.00",
    price_course_euros: "",
    ...defaults,
  };
}

export function eurosToCents(value: string): number {
  const normalized = value.trim().replace(",", ".");
  const amount = Number(normalized);
  if (!Number.isFinite(amount) || amount < 0) {
    throw new Error("Invalid amount");
  }
  return Math.round(amount * 100);
}

export function centsToEurosInput(cents: number): string {
  return (cents / 100).toFixed(2);
}
