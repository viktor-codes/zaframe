import { StudioMemberRole } from "@shared/lib/constants";

/**
 * Owners are created with the studio and cannot be demoted/removed via Team UI.
 * Mutating actions are shown only for manager / instructor rows.
 */
export function canMutateStudioMemberRole(role: string): boolean {
  return (
    role === StudioMemberRole.MANAGER || role === StudioMemberRole.INSTRUCTOR
  );
}

export function formatStudioMemberRole(role: string): string {
  switch (role) {
    case StudioMemberRole.OWNER:
      return "Owner";
    case StudioMemberRole.MANAGER:
      return "Manager";
    case StudioMemberRole.INSTRUCTOR:
      return "Instructor";
    default:
      return role;
  }
}
