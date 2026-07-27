"use client";

import { useState } from "react";
import type { AuthUser } from "@shared/auth";
import { Alert, Button, Input } from "@shared/ui";
import {
  parseProfileUpdate,
  type ProfileUpdateForm,
} from "../model/profile-schema";
import { useUpdateProfile } from "../model/use-update-profile";

export interface ProfileFormProps {
  user: AuthUser;
}

function toFormValues(user: AuthUser): ProfileUpdateForm {
  return {
    name: user.name,
    phone: user.phone ?? "",
    marketing_consent: user.marketing_consent,
  };
}

export function ProfileForm({ user }: ProfileFormProps) {
  const { updateProfile, isSaving } = useUpdateProfile();
  const [values, setValues] = useState<ProfileUpdateForm>(() =>
    toFormValues(user),
  );
  const [errors, setErrors] = useState<
    Partial<Record<keyof ProfileUpdateForm, string>>
  >({});

  return (
    <form
      className="space-y-5"
      data-testid="profile-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = parseProfileUpdate(values);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        updateProfile(parsed.data);
      }}
    >
      <Input
        label="Email"
        type="email"
        value={user.email}
        disabled
        helper="Email is used for sign-in and cannot be changed here."
        autoComplete="email"
      />

      <Input
        label="Full name"
        type="text"
        value={values.name}
        onChange={(event) =>
          setValues((prev) => ({ ...prev, name: event.target.value }))
        }
        error={errors.name}
        required
        maxLength={100}
        autoComplete="name"
        placeholder="Ada Lovelace"
      />

      <Input
        label="Phone"
        type="tel"
        value={values.phone}
        onChange={(event) =>
          setValues((prev) => ({ ...prev, phone: event.target.value }))
        }
        error={errors.phone}
        maxLength={20}
        autoComplete="tel"
        placeholder="+353 87 123 4567"
        helper="Optional — studios may use this for session updates."
      />

      <label className="flex cursor-pointer items-start gap-3 rounded-2xl border-2 border-zinc-200 bg-white px-4 py-3">
        <input
          type="checkbox"
          className="mt-1 size-4 rounded border-zinc-300 text-teal-600 focus:ring-teal-400"
          checked={values.marketing_consent}
          onChange={(event) =>
            setValues((prev) => ({
              ...prev,
              marketing_consent: event.target.checked,
            }))
          }
          data-testid="profile-marketing-consent"
        />
        <span>
          <span className="block text-sm font-semibold text-zinc-800">
            Marketing updates
          </span>
          <span className="mt-0.5 block text-xs text-zinc-500">
            Occasional tips and studio highlights. You can turn this off
            anytime.
          </span>
        </span>
      </label>

      {errors.marketing_consent ? (
        <Alert variant="error" title="Could not save">
          {errors.marketing_consent}
        </Alert>
      ) : null}

      <Button
        type="submit"
        isLoading={isSaving}
        data-testid="profile-save-button"
      >
        Save profile
      </Button>
    </form>
  );
}
