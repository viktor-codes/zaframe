import { CheckInPanel } from "@features/check-in";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib/constants";
import { parsePositiveIdString } from "@shared/lib/parse-positive-id";

interface OccurrenceCheckInPageProps {
  params: Promise<{ id: string; occurrenceId: string }>;
}

export default async function OccurrenceCheckInPage({
  params,
}: OccurrenceCheckInPageProps) {
  const { id, occurrenceId: occurrenceIdParam } = await params;
  const studioId = parsePositiveIdString(id);
  const occurrenceId = parsePositiveIdString(occurrenceIdParam);

  if (studioId == null || occurrenceId == null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12">
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 text-red-800">
          Invalid session
        </div>
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.VIEW_BOOKINGS}
    >
      <div className="mx-auto max-w-lg px-4 py-8 sm:max-w-2xl sm:px-6 sm:py-12">
        <CheckInPanel studioId={studioId} occurrenceId={occurrenceId} />
      </div>
    </RequireStudioPermission>
  );
}
