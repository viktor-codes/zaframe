"use client";

import Link from "next/link";

import { useStudio, useStudioMembers } from "@entities/studio";
import { getUserFacingApiMessage } from "@shared/api";
import {
  ResourceEmptyState,
  ResourceErrorState,
  ResourceListSkeleton,
} from "@shared/ui";

import type { AssignableMemberRole } from "../model/member-form-schema";
import { useMemberMutations } from "../model/use-member-mutations";
import { AddMemberForm } from "./add-member-form";
import { MemberRow } from "./member-row";

export interface TeamPanelProps {
  studioId: number;
}

export function TeamPanel({ studioId }: TeamPanelProps) {
  const {
    data: studio,
    isLoading: isStudioLoading,
    isError: isStudioError,
    error: studioError,
    refetch: refetchStudio,
  } = useStudio(studioId);

  const {
    data: membersPage,
    isLoading: isMembersLoading,
    isError: isMembersError,
    error: membersError,
    refetch: refetchMembers,
  } = useStudioMembers(studioId);

  const { updateMemberRole, removeMember, pendingMemberId } =
    useMemberMutations(studioId);

  if (isStudioLoading || isMembersLoading) {
    return <ResourceListSkeleton testId="team-skeleton" rows={3} />;
  }

  if (isStudioError || !studio) {
    return (
      <ResourceErrorState
        title="Could not load studio"
        message={getUserFacingApiMessage(studioError)}
        testId="team-studio-error"
        onRetry={() => {
          void refetchStudio();
        }}
      />
    );
  }

  if (isMembersError || !membersPage) {
    return (
      <ResourceErrorState
        title="Could not load team"
        message={getUserFacingApiMessage(membersError)}
        testId="team-members-error"
        onRetry={() => {
          void refetchMembers();
        }}
      />
    );
  }

  const members = membersPage.items;

  return (
    <div className="space-y-6" data-testid="team-panel">
      <div>
        <Link
          href={`/dashboard/studios/${studioId}`}
          className="mb-4 inline-block text-sm font-medium text-primary hover:text-primary-dark"
        >
          ← Back to Today
        </Link>
        <h1 className="text-secondary font-display text-2xl font-bold">Team</h1>
        <p className="mt-1 text-sm text-neutral-600">
          Managers and instructors for {studio.name}.
        </p>
      </div>

      <AddMemberForm studioId={studioId} />

      {members.length === 0 ? (
        <ResourceEmptyState
          title="No team members yet"
          description="Add a manager or instructor by email once they have signed in to ZeeFrame."
          testId="team-empty"
        />
      ) : (
        <ul className="space-y-3" data-testid="team-member-list">
          {members.map((member) => (
            <MemberRow
              key={member.id}
              member={member}
              isBusy={pendingMemberId === member.id}
              onChangeRole={(memberId, role: AssignableMemberRole) => {
                if (member.role === role) return;
                updateMemberRole({ memberId, data: { role } });
              }}
              onRemove={(memberId) => removeMember(memberId)}
            />
          ))}
        </ul>
      )}
    </div>
  );
}
