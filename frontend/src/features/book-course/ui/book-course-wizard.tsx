"use client";

import { useState } from "react";
import {
  getPublicServicePriceCents,
  type PublicService,
} from "@entities/service";
import { useAuth } from "@shared/auth";
import { Button } from "@shared/ui";

import { getCourseAvailabilityPresentation } from "../model/course-availability";
import {
  parseGuestDetails,
  type GuestDetails,
} from "../model/guest-details-schema";
import type { BookCourseStep } from "../model/steps";
import { useBookCourseCheckout } from "../model/use-book-course-checkout";
import { useCourseAvailability } from "../model/use-course-availability";
import { CourseAvailabilityPanel } from "./course-availability-panel";
import { StepDetails, type StepDetailsForm } from "./step-details";
import { StepSummary } from "./step-summary";
import { BookCourseWizardChrome } from "./wizard-chrome";

export interface BookCourseWizardProps {
  slug: string;
  studioId: number;
  studioName: string;
  service: PublicService;
}

function emptyGuestForm(): StepDetailsForm {
  return { guest_name: "", guest_email: "", guest_phone: "" };
}

export function BookCourseWizard({
  slug,
  studioName,
  service,
}: BookCourseWizardProps) {
  const { user } = useAuth();
  const [step, setStep] = useState<BookCourseStep>("preview");
  const [guest, setGuest] = useState<GuestDetails | null>(null);
  const [form, setForm] = useState<StepDetailsForm>(emptyGuestForm);
  const [formErrors, setFormErrors] = useState<
    Partial<Record<keyof StepDetailsForm, string>>
  >({});
  const checkout = useBookCourseCheckout();
  const availabilityQuery = useCourseAvailability({ serviceId: service.id });

  const availability = availabilityQuery.data ?? null;
  const presentation = availability
    ? getCourseAvailabilityPresentation(availability)
    : null;
  const canProceed = presentation?.canProceed ?? false;
  const schedule = availability?.schedule_details ?? [];
  const priceCents = getPublicServicePriceCents(service);
  const sessionCount =
    schedule.length > 0
      ? schedule.length
      : Math.max(service.occurrences_count ?? 0, 0);

  const goToDetails = () => {
    if (!canProceed) return;
    setForm((current) => ({
      guest_name: current.guest_name || user?.name || "",
      guest_email: current.guest_email || user?.email || "",
      guest_phone: current.guest_phone || user?.phone || "",
    }));
    setStep("details");
  };

  return (
    <BookCourseWizardChrome
      slug={slug}
      studioName={studioName}
      serviceName={service.name}
      step={step}
    >
      {step === "preview" ? (
        <>
          <CourseAvailabilityPanel serviceId={service.id} studioSlug={slug} />
          <div className="mt-6 flex justify-end">
            <Button
              type="button"
              disabled={
                !canProceed ||
                availabilityQuery.isLoading ||
                availabilityQuery.isError
              }
              onClick={goToDetails}
              data-testid="book-course-preview-continue"
            >
              Continue
            </Button>
          </div>
        </>
      ) : null}

      {step === "details" ? (
        <StepDetails
          form={form}
          errors={formErrors}
          isSignedIn={Boolean(user)}
          onChange={(patch) => setForm((current) => ({ ...current, ...patch }))}
          onBack={() => setStep("preview")}
          onContinue={() => {
            const parsed = parseGuestDetails(form);
            setFormErrors(parsed.errors);
            if (Object.keys(parsed.errors).length > 0) return;
            setGuest(parsed.data);
            setStep("summary");
          }}
        />
      ) : null}

      {step === "summary" && guest ? (
        <StepSummary
          studioName={studioName}
          serviceName={service.name}
          sessionCount={sessionCount}
          priceCents={priceCents}
          guest={guest}
          availability={availability}
          schedule={schedule}
          error={checkout.error}
          isHardBlocked={checkout.isHardBlocked}
          heldOrderId={checkout.heldOrderId}
          isPaying={checkout.isPaying}
          canProceed={canProceed}
          studioSlug={slug}
          onBack={() => setStep("details")}
          onPay={() => checkout.pay({ serviceId: service.id, guest })}
        />
      ) : null}
    </BookCourseWizardChrome>
  );
}
