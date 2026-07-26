import {
  SERVICE_CATEGORIES,
  SERVICE_TYPE,
  type ServiceCategory,
} from "@entities/service";

export type ServiceFormValues = {
  name: string;
  description: string;
  type: string;
  category: ServiceCategory;
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
    category: SERVICE_CATEGORIES[0],
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
