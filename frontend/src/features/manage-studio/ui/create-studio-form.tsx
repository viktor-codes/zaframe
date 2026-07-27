"use client";

import { useState } from "react";
import Link from "next/link";

import { Button } from "@shared/ui";

import {
  emptyStudioProfileForm,
  type StudioProfileFormValues,
} from "../model/studio-profile-form";
import { parseCreateStudio } from "../model/studio-profile-schema";
import { useCreateStudio } from "../model/use-create-studio";
import { StudioProfileFields } from "./studio-profile-fields";

export function CreateStudioForm() {
  const { createStudio, isSaving } = useCreateStudio();
  const [values, setValues] = useState<StudioProfileFormValues>(() =>
    emptyStudioProfileForm(),
  );
  const [errors, setErrors] = useState<
    Partial<Record<keyof StudioProfileFormValues, string>>
  >({});

  return (
    <form
      className="space-y-6"
      data-testid="create-studio-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = parseCreateStudio(values);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        createStudio(parsed.data);
      }}
    >
      <StudioProfileFields
        values={values}
        errors={errors}
        requireStorefrontFields={false}
        onChange={(key, value) =>
          setValues((prev) => ({ ...prev, [key]: value }))
        }
      />

      <div className="flex justify-end gap-3">
        <Button variant="outline" asChild type="button">
          <Link href="/dashboard">Cancel</Link>
        </Button>
        <Button type="submit" isLoading={isSaving}>
          Create studio
        </Button>
      </div>
    </form>
  );
}
