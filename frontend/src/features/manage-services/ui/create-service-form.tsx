"use client";

import { useState } from "react";
import Link from "next/link";

import { Button } from "@shared/ui";

import { parseCreateService } from "../model/service-form-schema";
import {
  emptyServiceForm,
  type ServiceFormValues,
} from "../model/service-form-values";
import { useCreateService } from "../model/use-service-mutations";
import { ServiceFormFields } from "./service-form-fields";

export interface CreateServiceFormProps {
  studioId: number;
}

export function CreateServiceForm({ studioId }: CreateServiceFormProps) {
  const { createService, isSaving } = useCreateService(studioId);
  const [values, setValues] = useState<ServiceFormValues>(() =>
    emptyServiceForm(),
  );
  const [errors, setErrors] = useState<
    Partial<Record<keyof ServiceFormValues, string>>
  >({});

  return (
    <form
      className="space-y-6"
      data-testid="create-service-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = parseCreateService(values, studioId);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        createService(parsed.data);
      }}
    >
      <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
        New services start as <strong>draft</strong> — not visible on the
        storefront until you publish.
      </p>

      <ServiceFormFields
        values={values}
        errors={errors}
        onChange={(key, value) =>
          setValues((prev) => ({ ...prev, [key]: value }))
        }
      />

      <div className="flex justify-end gap-3">
        <Button variant="outline" asChild type="button">
          <Link href={`/dashboard/studios/${studioId}/services`}>Cancel</Link>
        </Button>
        <Button type="submit" isLoading={isSaving}>
          Create draft
        </Button>
      </div>
    </form>
  );
}
