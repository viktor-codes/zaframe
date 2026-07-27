"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button, Input } from "@shared/ui";

export interface StepDetailsForm {
  guest_name: string;
  guest_email: string;
  guest_phone: string;
}

export interface StepDetailsProps {
  form: StepDetailsForm;
  errors: Partial<Record<keyof StepDetailsForm, string>>;
  isSignedIn: boolean;
  onChange: (patch: Partial<StepDetailsForm>) => void;
  onContinue: () => void;
  onBack: () => void;
}

export function StepDetails({
  form,
  errors,
  isSignedIn,
  onChange,
  onContinue,
  onBack,
}: StepDetailsProps) {
  const pathname = usePathname();
  const loginHref = pathname
    ? `/auth/login?next=${encodeURIComponent(pathname)}`
    : "/auth/login";

  return (
    <form
      className="space-y-4"
      data-testid="book-course-step-details"
      onSubmit={(event) => {
        event.preventDefault();
        onContinue();
      }}
    >
      <p className="text-sm text-neutral-600">
        Buy as a guest — you can save this course to an account after payment.
      </p>

      {!isSignedIn ? (
        <p className="text-sm text-neutral-500">
          Already have an account?{" "}
          <Link
            href={loginHref}
            className="font-semibold text-teal-700 underline"
          >
            Sign in
          </Link>{" "}
          (optional).
        </p>
      ) : (
        <p className="rounded-xl bg-teal-50 px-3 py-2 text-sm text-teal-800">
          Signed in — we prefilled your details. You can still edit them.
        </p>
      )}

      <Input
        label="Name"
        type="text"
        required
        placeholder="Your name"
        value={form.guest_name}
        error={errors.guest_name}
        onChange={(event) => onChange({ guest_name: event.target.value })}
        autoComplete="name"
      />
      <Input
        label="Email"
        type="email"
        required
        placeholder="your@email.com"
        value={form.guest_email}
        error={errors.guest_email}
        onChange={(event) => onChange({ guest_email: event.target.value })}
        autoComplete="email"
        data-testid="course-guest-email-input"
      />
      <Input
        label="Phone (optional)"
        type="tel"
        placeholder="+353 87 000 0000"
        value={form.guest_phone}
        error={errors.guest_phone}
        onChange={(event) => onChange({ guest_phone: event.target.value })}
        autoComplete="tel"
      />

      <div className="flex flex-col-reverse gap-3 pt-2 sm:flex-row sm:justify-between">
        <Button type="button" variant="ghost" onClick={onBack}>
          Back
        </Button>
        <Button type="submit" data-testid="book-course-details-continue">
          Continue to summary
        </Button>
      </div>
    </form>
  );
}
