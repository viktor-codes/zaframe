import { StudioTodayPanel } from "@features/studio-today";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib/constants";
import { parsePositiveIdString } from "@shared/lib/parse-positive-id";

interface StudioTodayPageProps {
  params: Promise<{ id: string }>;
}

export default async function StudioTodayPage({
  params,
}: StudioTodayPageProps) {
  const { id } = await params;
  const studioId = parsePositiveIdString(id);

  if (studioId == null) {
    return (
      <div className="mx-auto max-w-3xl px-6 py-12 text-red-800">
        Invalid studio
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.VIEW_DASHBOARD}
    >
      <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6 sm:py-12">
        <StudioTodayPanel studioId={studioId} />
      </div>
    </RequireStudioPermission>
  );
}
