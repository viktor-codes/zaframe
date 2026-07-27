"use client";

import { useState } from "react";
import Link from "next/link";

import type { StudioResponse } from "@entities/studio";
import { Button } from "@shared/ui";

import {
  emptyStudioProfileForm,
  type StudioProfileFormValues,
} from "../model/studio-profile-form";
import { parseUpdateStudio } from "../model/studio-profile-schema";
import { useUpdateStudio } from "../model/use-update-studio";
import { StudioProfileFields } from "./studio-profile-fields";

export interface EditStudioFormProps {
  studio: StudioResponse;
}

function toFormValues(studio: StudioResponse): StudioProfileFormValues {
  return emptyStudioProfileForm({
    name: studio.name,
    slug: studio.slug ?? "",
    description: studio.description ?? "",
    city: studio.city ?? "",
    email: studio.email ?? "",
    phone: studio.phone ?? "",
    address: studio.address ?? "",
    timezone: studio.timezone,
    cancel_before_hours: String(studio.cancel_before_hours),
  });
}

export function EditStudioForm({ studio }: EditStudioFormProps) {
  const { updateStudio, isSaving } = useUpdateStudio(studio.id);
  const [values, setValues] = useState<StudioProfileFormValues>(() =>
    toFormValues(studio),
  );
  const [errors, setErrors] = useState<
    Partial<Record<keyof StudioProfileFormValues, string>>
  >({});

  return (
    <form
      className="space-y-6"
      data-testid="edit-studio-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = parseUpdateStudio(values);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        updateStudio(parsed.data);
      }}
    >
      <StudioProfileFields
        values={values}
        errors={errors}
        requireStorefrontFields
        onChange={(key, value) =>
          setValues((prev) => ({ ...prev, [key]: value }))
        }
      />

      <div className="flex justify-end gap-3">
        <Button variant="outline" asChild type="button">
          <Link href={`/dashboard/studios/${studio.id}`}>Cancel</Link>
        </Button>
        <Button type="submit" isLoading={isSaving}>
          Save profile
        </Button>
      </div>
    </form>
  );
}
