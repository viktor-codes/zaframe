"use client";

import { useState } from "react";

import type { StudioMemberResponse } from "@entities/studio";
import { Button } from "@shared/ui";

import {
  ASSIGNABLE_MEMBER_ROLES,
  type AssignableMemberRole,
} from "../model/member-form-schema";
import {
  canMutateStudioMemberRole,
  formatStudioMemberRole,
} from "../model/member-role";

export interface MemberRowProps {
  member: StudioMemberResponse;
  isBusy: boolean;
  onChangeRole: (memberId: number, role: AssignableMemberRole) => void;
  onRemove: (memberId: number) => void;
}

export function MemberRow({
  member,
  isBusy,
  onChangeRole,
  onRemove,
}: MemberRowProps) {
  const [confirmRemove, setConfirmRemove] = useState(false);
  const canMutate = canMutateStudioMemberRole(member.role);
  const displayName = member.name?.trim() || member.email;

  return (
    <li
      className="rounded-2xl border border-neutral-200 bg-white p-4"
      data-testid={`member-row-${member.id}`}
    >
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="font-medium text-neutral-900">{displayName}</p>
          <p className="text-sm text-neutral-600">{member.email}</p>
          {!canMutate ? (
            <p
              className="mt-1 text-xs font-medium text-neutral-500"
              data-testid={`member-role-label-${member.id}`}
            >
              {formatStudioMemberRole(member.role)}
            </p>
          ) : null}
        </div>

        {canMutate ? (
          <div className="flex flex-wrap items-center gap-2">
            <select
              aria-label={`Role for ${displayName}`}
              className="rounded-xl border-2 border-zinc-200 bg-white px-3 py-2 text-sm outline-none focus:border-teal-400"
              value={member.role}
              disabled={isBusy}
              onChange={(event) =>
                onChangeRole(
                  member.id,
                  event.target.value as AssignableMemberRole,
                )
              }
              data-testid={`member-role-select-${member.id}`}
            >
              {ASSIGNABLE_MEMBER_ROLES.map((role) => (
                <option key={role} value={role}>
                  {formatStudioMemberRole(role)}
                </option>
              ))}
            </select>

            {confirmRemove ? (
              <div
                className="flex flex-wrap gap-2"
                data-testid={`member-remove-confirm-${member.id}`}
              >
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  isLoading={isBusy}
                  onClick={() => onRemove(member.id)}
                  data-testid={`member-remove-confirm-yes-${member.id}`}
                >
                  Yes, remove
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={isBusy}
                  onClick={() => setConfirmRemove(false)}
                  data-testid={`member-remove-confirm-no-${member.id}`}
                >
                  Keep
                </Button>
              </div>
            ) : (
              <Button
                type="button"
                variant="outline"
                size="sm"
                disabled={isBusy}
                onClick={() => setConfirmRemove(true)}
                data-testid={`member-remove-${member.id}`}
              >
                Remove
              </Button>
            )}
          </div>
        ) : null}
      </div>
    </li>
  );
}
