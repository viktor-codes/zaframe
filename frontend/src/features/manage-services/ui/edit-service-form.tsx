"use client";

import { useState } from "react";
import Link from "next/link";

import { VisibilityBadge, type ServiceResponse } from "@entities/service";
import { ServiceVisibility } from "@shared/lib";
import { Button } from "@shared/ui";

import { parseUpdateService } from "../model/service-form-schema";
import {
  centsToEurosInput,
  emptyServiceForm,
  type ServiceFormValues,
} from "../model/service-form-values";
import {
  useServiceVisibilityActions,
  useUpdateService,
} from "../model/use-service-mutations";
import { ServiceFormFields } from "./service-form-fields";

export interface EditServiceFormProps {
  studioId: number;
  service: ServiceResponse;
}

function toFormValues(service: ServiceResponse): ServiceFormValues {
  return emptyServiceForm({
    name: service.name,
    description: service.description ?? "",
    type: service.type,
    category: service.category,
    duration_minutes: String(service.duration_minutes),
    max_capacity: String(service.max_capacity),
    price_euros: centsToEurosInput(service.price_single_cents),
    price_course_euros:
      service.price_course_cents != null
        ? centsToEurosInput(service.price_course_cents)
        : "",
  });
}

export function EditServiceForm({ studioId, service }: EditServiceFormProps) {
  const { updateService, isSaving } = useUpdateService(studioId, service.id);
  const { publish, unpublish, archive, isPending } =
    useServiceVisibilityActions(studioId, service.id);
  const [values, setValues] = useState<ServiceFormValues>(() =>
    toFormValues(service),
  );
  const [errors, setErrors] = useState<
    Partial<Record<keyof ServiceFormValues, string>>
  >({});

  return (
    <div className="space-y-6" data-testid="edit-service-form">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-neutral-200 bg-neutral-50 px-4 py-3">
        <VisibilityBadge visibility={service.visibility} />
        <div className="flex flex-wrap gap-2">
          {service.visibility !== ServiceVisibility.PUBLISHED ? (
            <Button
              type="button"
              onClick={() => publish()}
              isLoading={isPending}
            >
              Publish
            </Button>
          ) : (
            <Button
              type="button"
              variant="outline"
              onClick={() => unpublish()}
              isLoading={isPending}
            >
              Move to draft
            </Button>
          )}
          {service.visibility !== ServiceVisibility.ARCHIVED ? (
            <Button
              type="button"
              variant="outline"
              onClick={() => {
                if (
                  window.confirm(
                    "Archive this service? It will leave the storefront.",
                  )
                ) {
                  archive();
                }
              }}
              isLoading={isPending}
            >
              Archive
            </Button>
          ) : null}
        </div>
      </div>

      <form
        className="space-y-6"
        onSubmit={(event) => {
          event.preventDefault();
          const parsed = parseUpdateService(values);
          setErrors(parsed.errors);
          if (!parsed.data) return;
          updateService(parsed.data);
        }}
      >
        <ServiceFormFields
          values={values}
          errors={errors}
          onChange={(key, value) =>
            setValues((prev) => ({ ...prev, [key]: value }))
          }
        />

        <div className="flex flex-wrap justify-between gap-3">
          <Button variant="outline" asChild type="button">
            <Link
              href={`/dashboard/studios/${studioId}/services/${service.id}/schedule`}
            >
              Schedule templates
            </Link>
          </Button>
          <div className="flex gap-3">
            <Button variant="outline" asChild type="button">
              <Link href={`/dashboard/studios/${studioId}/services`}>
                Back to list
              </Link>
            </Button>
            <Button type="submit" isLoading={isSaving}>
              Save changes
            </Button>
          </div>
        </div>
      </form>
    </div>
  );
}
