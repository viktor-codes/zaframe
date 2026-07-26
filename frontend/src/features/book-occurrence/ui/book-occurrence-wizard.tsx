"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import type { OccurrenceResponse } from "@entities/occurrence";
import type { PublicService } from "@entities/service";
import { fetchStudioOccurrences } from "@shared/api";
import { useAuth } from "@shared/auth";
import { OccurrenceStatus, queryKeys } from "@shared/lib";
import { Button } from "@shared/ui";

import {
  parseGuestDetails,
  type GuestDetails,
} from "../model/guest-details-schema";
import type { BookOccurrenceStep } from "../model/steps";
import { useBookOccurrenceCheckout } from "../model/use-book-occurrence-checkout";
import { StepDetails, type StepDetailsForm } from "./step-details";
import { StepSlot } from "./step-slot";
import { StepSummary } from "./step-summary";
import { WizardChrome } from "./wizard-chrome";

export interface BookOccurrenceWizardProps {
  slug: string;
  studioId: number;
  studioName: string;
  service: PublicService;
}

const occurrenceFilters = {
  status: OccurrenceStatus.SCHEDULED,
  size: 100,
} as const;

function emptyGuestForm(): StepDetailsForm {
  return { guest_name: "", guest_email: "", guest_phone: "" };
}

export function BookOccurrenceWizard({
  slug,
  studioId,
  studioName,
  service,
}: BookOccurrenceWizardProps) {
  const { user } = useAuth();
  const [step, setStep] = useState<BookOccurrenceStep>("slot");
  const [selected, setSelected] = useState<OccurrenceResponse | null>(null);
  const [guest, setGuest] = useState<GuestDetails | null>(null);
  const [form, setForm] = useState<StepDetailsForm>(emptyGuestForm);
  const [formErrors, setFormErrors] = useState<
    Partial<Record<keyof StepDetailsForm, string>>
  >({});
  const checkout = useBookOccurrenceCheckout();

  const occurrencesQuery = useQuery({
    queryKey: queryKeys.studio.occurrences(studioId, occurrenceFilters),
    queryFn: () => fetchStudioOccurrences(studioId, occurrenceFilters),
  });

  const pickAnotherTime = () => {
    checkout.clearError();
    setSelected(null);
    setStep("slot");
    void occurrencesQuery.refetch();
  };

  const serviceOccurrences = useMemo(
    () =>
      (occurrencesQuery.data ?? []).filter(
        (occurrence) => occurrence.service_id === service.id,
      ),
    [occurrencesQuery.data, service.id],
  );

  const goToDetails = () => {
    if (!selected) return;
    setForm((current) => ({
      guest_name: current.guest_name || user?.name || "",
      guest_email: current.guest_email || user?.email || "",
      guest_phone: current.guest_phone || user?.phone || "",
    }));
    setStep("details");
  };

  return (
    <WizardChrome
      slug={slug}
      studioName={studioName}
      serviceName={service.name}
      step={step}
    >
      {step === "slot" ? (
        <>
          <StepSlot
            occurrences={serviceOccurrences}
            isLoading={occurrencesQuery.isLoading}
            isError={occurrencesQuery.isError}
            selectedId={selected?.id ?? null}
            studioSlug={slug}
            onSelect={setSelected}
          />
          <div className="mt-6 flex justify-end">
            <Button
              type="button"
              disabled={!selected}
              onClick={goToDetails}
              data-testid="book-slot-continue"
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
          onBack={() => setStep("slot")}
          onContinue={() => {
            const parsed = parseGuestDetails(form);
            setFormErrors(parsed.errors);
            if (Object.keys(parsed.errors).length > 0) return;
            setGuest(parsed.data);
            setStep("summary");
          }}
        />
      ) : null}

      {step === "summary" && selected && guest ? (
        <StepSummary
          studioName={studioName}
          serviceName={service.name}
          occurrence={selected}
          guest={guest}
          error={checkout.error}
          isOccurrenceFull={checkout.isOccurrenceFull}
          heldBookingId={checkout.heldBookingId}
          isPaying={checkout.isPaying}
          onBack={() => setStep("details")}
          onPay={() => checkout.pay({ occurrence: selected, guest })}
          onPickAnotherTime={pickAnotherTime}
        />
      ) : null}
    </WizardChrome>
  );
}
