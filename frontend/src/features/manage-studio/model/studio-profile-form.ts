import { defaultStudioTimezone } from "./studio-timezones";

export type StudioProfileFormValues = {
  name: string;
  slug: string;
  description: string;
  city: string;
  email: string;
  phone: string;
  address: string;
  timezone: string;
  cancel_before_hours: string;
};

export const emptyStudioProfileForm = (
  defaults?: Partial<StudioProfileFormValues>,
): StudioProfileFormValues => ({
  name: "",
  slug: "",
  description: "",
  city: "",
  email: "",
  phone: "",
  address: "",
  timezone: defaultStudioTimezone(),
  cancel_before_hours: "24",
  ...defaults,
});
