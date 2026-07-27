import { ScheduleTemplatesPanel } from "@features/manage-schedule";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib/constants";
import { parsePositiveIdString } from "@shared/lib/parse-positive-id";

interface ServiceSchedulePageProps {
  params: Promise<{ id: string; serviceId: string }>;
}

export default async function ServiceSchedulePage({
  params,
}: ServiceSchedulePageProps) {
  const { id, serviceId: serviceIdParam } = await params;
  const studioId = parsePositiveIdString(id);
  const serviceId = parsePositiveIdString(serviceIdParam);

  if (studioId == null || serviceId == null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12 text-red-800">
        Invalid schedule route
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.MANAGE_SCHEDULE}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <ScheduleTemplatesPanel studioId={studioId} serviceId={serviceId} />
      </div>
    </RequireStudioPermission>
  );
}