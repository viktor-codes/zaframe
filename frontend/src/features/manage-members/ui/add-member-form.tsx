"use client";

import { useState } from "react";

import { Button, Input } from "@shared/ui";

import {
  ASSIGNABLE_MEMBER_ROLES,
  emptyAddMemberForm,
  parseAddMember,
  type AddMemberForm,
  type AssignableMemberRole,
} from "../model/member-form-schema";
import { useMemberMutations } from "../model/use-member-mutations";

export interface AddMemberFormProps {
  studioId: number;
}

export function AddMemberForm({ studioId }: AddMemberFormProps) {
  const { addMember, isAdding } = useMemberMutations(studioId);
  const [values, setValues] = useState<AddMemberForm>(() => emptyAddMemberForm());
  const [errors, setErrors] = useState<
    Partial<Record<keyof AddMemberForm, string>>
  >({});

  return (
    <form
      className="space-y-4 rounded-2xl border border-neutral-200 bg-white p-5"
      data-testid="add-member-form"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = parseAddMember(values);
        setErrors(parsed.errors);
        if (!parsed.data) return;
        addMember(parsed.data, {
          onSuccess: () => {
            setValues(emptyAddMemberForm());
            setErrors({});
          },
        });
      }}
    >
      <div>
        <h2 className="text-sm font-semibold text-neutral-900">Add teammate</h2>
        <p className="mt-1 text-xs text-neutral-500">
          They must already have a ZeeFrame account (sign in once with OTP).
        </p>
      </div>

      <Input
        label="Email"
        type="email"
        autoComplete="email"
        required
        value={values.email}
        onChange={(event) =>
          setValues((prev) => ({ ...prev, email: event.target.value }))
        }
        error={errors.email}
        placeholder="coach@studio.com"
        data-testid="add-member-email"
      />

      <div className="w-full">
        <label
          htmlFor="add-member-role"
          className="mb-2 block text-sm font-semibold text-zinc-700"
        >
          Role
        </label>
        <select
          id="add-member-role"
          className="w-full rounded-2xl border-2 border-zinc-200 bg-white px-4 py-3 text-sm outline-none focus:border-teal-400 focus:ring-4 focus:ring-teal-100"
          value={values.role}
          onChange={(event) =>
            setValues((prev) => ({
              ...prev,
              role: event.target.value as AssignableMemberRole,
            }))
          }
          data-testid="add-member-role"
        >
          {ASSIGNABLE_MEMBER_ROLES.map((role) => (
            <option key={role} value={role}>
              {role === "manager" ? "Manager" : "Instructor"}
            </option>
          ))}
        </select>
        {errors.role ? (
          <p className="mt-1 text-xs text-red-600" role="alert">
            {errors.role}
          </p>
        ) : null}
      </div>

      <div className="flex justify-end">
        <Button type="submit" isLoading={isAdding} data-testid="add-member-submit">
          Add to team
        </Button>
      </div>
    </form>
  );
}
