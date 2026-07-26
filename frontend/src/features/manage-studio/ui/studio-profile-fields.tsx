"use client";

import { Input, Textarea } from "@shared/ui";

import type { StudioProfileFormValues } from "../model/studio-profile-form";
import { listStudioTimezones } from "../model/studio-timezones";

export interface StudioProfileFieldsProps {
  values: StudioProfileFormValues;
  errors: Partial<Record<keyof StudioProfileFormValues, string>>;
  onChange: <K extends keyof StudioProfileFormValues>(
    key: K,
    value: StudioProfileFormValues[K],
  ) => void;
  /** Edit form requires storefront-ready slug/city/description. */
  requireStorefrontFields: boolean;
}

export function StudioProfileFields({
  values,
  errors,
  onChange,
  requireStorefrontFields,
}: StudioProfileFieldsProps) {
  const timezones = [...listStudioTimezones()];
  if (values.timezone && !timezones.includes(values.timezone)) {
    timezones.unshift(values.timezone);
  }

  return (
    <div className="space-y-4">
      <Input
        label="Studio name"
        required
        value={values.name}
        onChange={(event) => onChange("name", event.target.value)}
        error={errors.name}
        maxLength={200}
        placeholder="Yoga Hub Dublin"
      />

      <Input
        label="Public slug"
        required={requireStorefrontFields}
        value={values.slug}
        onChange={(event) => onChange("slug", event.target.value)}
        error={errors.slug}
        maxLength={255}
        placeholder="yoga-hub-dublin"
        helper="Used in your storefront URL: /s/your-slug"
      />

      <Textarea
        label="Description"
        required={requireStorefrontFields}
        value={values.description}
        onChange={(event) => onChange("description", event.target.value)}
        error={errors.description}
        rows={4}
        placeholder="A bright loft for small photo and video classes."
      />

      <Input
        label="City"
        required={requireStorefrontFields}
        value={values.city}
        onChange={(event) => onChange("city", event.target.value)}
        error={errors.city}
        maxLength={100}
        placeholder="Dublin"
      />

      <div>
        <label
          htmlFor="studio-timezone"
          className="mb-2 block text-sm font-medium text-neutral-700"
        >
          Timezone <span className="text-red-500">*</span>
        </label>
        <select
          id="studio-timezone"
          value={values.timezone}
          onChange={(event) => onChange("timezone", event.target.value)}
          className="w-full rounded-lg border-2 border-neutral-200 bg-white px-4 py-3 text-sm outline-none focus:border-primary"
          aria-invalid={!!errors.timezone}
        >
          {timezones.map((zone) => (
            <option key={zone} value={zone}>
              {zone}
            </option>
          ))}
        </select>
        {errors.timezone ? (
          <p className="mt-1 text-sm text-red-600">{errors.timezone}</p>
        ) : (
          <p className="mt-1 text-xs text-neutral-500">
            Cannot change after the first session is created.
          </p>
        )}
      </div>

      <Input
        label="Cancel before (hours)"
        type="number"
        required
        min={0}
        max={720}
        value={values.cancel_before_hours}
        onChange={(event) =>
          onChange("cancel_before_hours", event.target.value)
        }
        error={errors.cancel_before_hours}
        helper="How many hours before a session customers may cancel."
      />

      <Input
        label="Email"
        type="email"
        value={values.email}
        onChange={(event) => onChange("email", event.target.value)}
        error={errors.email}
        placeholder="studio@example.com"
      />

      <Input
        label="Phone"
        type="tel"
        value={values.phone}
        onChange={(event) => onChange("phone", event.target.value)}
        error={errors.phone}
        maxLength={20}
        placeholder="+353 87 123 4567"
      />

      <Input
        label="Address"
        value={values.address}
        onChange={(event) => onChange("address", event.target.value)}
        error={errors.address}
        maxLength={500}
        placeholder="12 Pearse Street"
      />
    </div>
  );
}
