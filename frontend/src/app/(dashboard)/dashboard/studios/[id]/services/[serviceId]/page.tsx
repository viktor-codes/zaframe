import { EditServicePanel } from "@features/manage-services";
import { RequireStudioPermission } from "@shared/auth";
import { StudioPermission } from "@shared/lib/constants";
import { parsePositiveIdString } from "@shared/lib/parse-positive-id";

interface EditServicePageProps {
  params: Promise<{ id: string; serviceId: string }>;
}

export default async function EditServicePage({ params }: EditServicePageProps) {
  const { id, serviceId: serviceIdParam } = await params;
  const studioId = parsePositiveIdString(id);
  const serviceId = parsePositiveIdString(serviceIdParam);

  if (studioId == null || serviceId == null) {
    return (
      <div className="mx-auto max-w-2xl px-6 py-12 text-red-800">
        Invalid service
      </div>
    );
  }

  return (
    <RequireStudioPermission
      studioId={studioId}
      permission={StudioPermission.MANAGE_SERVICES}
    >
      <div className="mx-auto max-w-2xl px-4 py-10 sm:px-6 sm:py-12">
        <EditServicePanel studioId={studioId} serviceId={serviceId} />
      </div>
    </RequireStudioPermission>
  );
}
